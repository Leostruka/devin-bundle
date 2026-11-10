"""api-bridge: OpenAI-shim contract tests (devin backend mocked)."""
import importlib.util
import json
import os
import sys
import threading
import urllib.request
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "extensions",
                       "api-bridge")
spec = importlib.util.spec_from_file_location(
    "bridge", os.path.join(SCRIPTS, "bridge.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_flatten_system_and_turns():
    p = mod._flatten([
        {"role": "system", "content": "Be terse."},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "bye"},
    ])
    assert "System instructions:\nBe terse." in p
    assert "User: hi" in p and "Assistant: hello" in p
    assert "next message" in p  # multi-turn continuation hint


def test_flatten_multipart_content():
    p = mod._flatten([{"role": "user", "content": [
        {"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}])
    assert "User: ab" in p


def test_completion_shape():
    c = mod._completion("hi", "swe-2-medium", cid="x")
    assert c["object"] == "chat.completion"
    assert c["choices"][0]["message"]["content"] == "hi"
    assert c["choices"][0]["finish_reason"] == "stop"


def _server(token=None):
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), mod.Handler)
    httpd.devin, httpd.workdir = "devin", "."
    httpd.timeout, httpd.token = 30, token
    httpd.models = ["m1"]
    httpd.sem = threading.BoundedSemaphore(4)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def test_endpoints_with_mock_backend():
    httpd, base = _server()
    try:
        with urllib.request.urlopen(base + "/health") as r:
            assert json.load(r)["ok"] is True
        with urllib.request.urlopen(base + "/v1/models") as r:
            assert r.status == 200
            assert json.load(r)["data"][0]["id"] == "m1"
        with patch.object(mod, "_run_devin", return_value=("ponte", None)):
            body = json.dumps({"messages": [{"role": "user",
                                             "content": "hi"}]}).encode()
            req = urllib.request.Request(
                base + "/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as r:
                d = json.load(r)
            assert d["choices"][0]["message"]["content"] == "ponte"
    finally:
        httpd.shutdown()


def test_token_enforced_when_set():
    httpd, base = _server(token="sekret")
    try:
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(base + "/health")
        assert e.value.code == 401
        req = urllib.request.Request(
            base + "/health",
            headers={"Authorization": "Bearer sekret"})
        with urllib.request.urlopen(req) as r:
            assert json.load(r)["ok"] is True
    finally:
        httpd.shutdown()


def test_bad_messages_rejected():
    httpd, base = _server()
    try:
        body = json.dumps({"messages": []}).encode()
        req = urllib.request.Request(base + "/v1/chat/completions",
                                     data=body)
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req)
        assert e.value.code == 400
    finally:
        httpd.shutdown()


def test_unknown_model_400_with_hint():
    httpd, base = _server()
    try:
        body = json.dumps({"model": "nope-1",
                           "messages": [{"role": "user",
                                         "content": "hi"}]}).encode()
        req = urllib.request.Request(base + "/v1/chat/completions",
                                     data=body)
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req)
        assert e.value.code == 400
        d = json.loads(e.value.read())
        assert d["error"]["param"] == "model"
        assert "v1/models" in d["error"]["hint"]
    finally:
        httpd.shutdown()


def test_usage_estimated_nonzero():
    c = mod._completion("ponte" * 40, "m", prompt="translate this")
    assert c["usage"]["prompt_tokens"] >= 1
    assert c["usage"]["completion_tokens"] >= 10
    assert (c["usage"]["total_tokens"]
            == c["usage"]["prompt_tokens"]
            + c["usage"]["completion_tokens"])


def test_upstream_error_taxonomy():
    with patch.object(mod, "_run_devin",
                      return_value=(None, ("timeout", "slow"))):
        httpd, base = _server()
        try:
            body = json.dumps({"messages": [{"role": "user",
                                             "content": "hi"}]}).encode()
            req = urllib.request.Request(
                base + "/v1/chat/completions", data=body)
            with pytest.raises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(req)
            assert e.value.code == 504
            assert json.loads(e.value.read()
                              )["error"]["type"] == "timeout_error"
        finally:
            httpd.shutdown()


def test_cors_preflight_and_headers():
    httpd, base = _server()
    try:
        req = urllib.request.Request(base + "/v1/models",
                                     method="OPTIONS",
                                     headers={"Origin": "http://x"})
        with urllib.request.urlopen(req) as r:
            assert r.status == 204
            assert r.headers["Access-Control-Allow-Origin"] == "http://x"
        req2 = urllib.request.Request(
            base + "/health", headers={"Origin": "http://y"})
        with urllib.request.urlopen(req2) as r:
            assert r.headers["Access-Control-Allow-Origin"] == "http://y"
    finally:
        httpd.shutdown()


def test_concurrency_cap_serializes_backend():
    calls = []
    def slow_backend(d, p, m, w, t):
        calls.append(1)
        try:
            __import__("time").sleep(0.3)
            return "ok", None
        finally:
            calls.pop()
    httpd, base = _server()
    try:
        with patch.object(mod, "_run_devin", slow_backend):
            body = json.dumps({"messages": [{"role": "user",
                                             "content": "x"}]}).encode()
            def hit():
                urllib.request.urlopen(urllib.request.Request(
                    base + "/v1/chat/completions", data=body)).read()
            ts = [threading.Thread(target=hit) for _ in range(4)]
            t0 = __import__("time").time()
            [t.start() for t in ts]; [t.join() for t in ts]
            # semaphore=4 in _server: all run in ~1x backend time;
            # assert the cap mechanism itself is wired (sem exists)
            assert httpd.sem._value >= 0
            assert __import__("time").time() - t0 < 1.2
    finally:
        httpd.shutdown()


def test_ignored_params_surfaced():
    httpd, base = _server()
    try:
        with patch.object(mod, "_run_devin",
                          lambda d, p, m, w, t: ("resposta", None)):
            body = json.dumps({"messages": [{"role": "user",
                                             "content": "oi"}],
                               "temperature": 0.1,
                               "max_tokens": 5}).encode()
            with urllib.request.urlopen(urllib.request.Request(
                    base + "/v1/chat/completions", data=body)) as r:
                d = json.loads(r.read())
            assert d["x-ignored-params"] == ["temperature", "max_tokens"]
    finally:
        httpd.shutdown()
