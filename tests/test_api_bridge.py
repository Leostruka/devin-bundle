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
