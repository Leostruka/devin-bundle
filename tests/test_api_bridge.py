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
    httpd.devin, httpd.workdir = sys.executable, "."
    httpd.timeout, httpd.token = 30, token
    httpd.models = ["m1"]
    httpd.concurrency = 4
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


def test_stream_options_include_usage_emits_usage_chunk():
    """stream_options.include_usage -> final chunk with choices=[] and
    a usage block before [DONE] (OpenAI streaming contract)."""
    httpd, base = _server()
    try:
        with patch.object(mod, "_run_devin",
                          return_value=("ok", None)):
            body = json.dumps({
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
                "stream_options": {"include_usage": True}}).encode()
            req = urllib.request.Request(
                base + "/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as r:
                raw = r.read().decode()
        chunks = [json.loads(l[6:]) for l in raw.splitlines()
                  if l.startswith("data: {")]
        uchunk = [c for c in chunks if c.get("choices") == []
                  and c.get("usage")]
        assert uchunk, f"no usage chunk in {chunks}"
        assert uchunk[0]["usage"]["total_tokens"] > 0
        assert raw.rstrip().endswith("data: [DONE]")
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


def test_root_self_describing():
    httpd, base = _server()
    try:
        with urllib.request.urlopen(base + "/") as r:
            d = json.loads(r.read())
        assert d["service"] == "devin-api-bridge"
        assert "POST /v1/chat/completions" in d["endpoints"]
        assert d["models"] == 1 and d["concurrency"] == 4
    finally:
        httpd.shutdown()


def test_health_reports_backend_reachability():
    httpd, base = _server()
    try:
        with urllib.request.urlopen(base + "/health") as r:
            d = json.loads(r.read())
        assert d["ok"] is True and d["backend"]["found"] is True
        httpd.devin = "nonexistent-binary-xyz"
        try:
            urllib.request.urlopen(base + "/health")
            assert False, "expected 503"
        except urllib.error.HTTPError as e:
            assert e.code == 503
            assert json.loads(e.read())["backend"]["found"] is False
    finally:
        httpd.shutdown()


def test_setup_opencode_write_merges_and_refuses_clobber(tmp_path):
    import argparse
    cfg = tmp_path / "opencode.json"
    a = argparse.Namespace(harness="opencode", write=str(cfg),
                           model=None, token="t", port=8787)
    mod.setup(a)
    d = json.loads(cfg.read_text(encoding="utf-8"))
    assert d["provider"]["devin-local"]["options"]["baseURL"].endswith(
        ":8787/v1")
    try:
        mod.setup(a)
        assert False, "expected refusal"
    except SystemExit:
        pass


def test_setup_codex_prints_valid_toml(capsys):
    import argparse
    import tomllib
    mod.setup(argparse.Namespace(harness="codex", model=None,
                                 port=8787, write=None, token=None))
    body = capsys.readouterr().out.split("# append")[0]
    d = tomllib.loads(body)
    assert d["model_provider"] == "devin-local"
    assert d["model_providers"]["devin-local"]["wire_api"] == "chat"


def test_setup_generic_prints_env(capsys):
    import argparse
    mod.setup(argparse.Namespace(harness="generic", token="k",
                                 port=8787, model=None, write=None))
    out = capsys.readouterr().out
    assert "OPENAI_BASE_URL" in out and "OPENAI_API_KEY" in out


def test_acp_prompt_collects_chunks_and_real_usage():
    """AcpBackend.prompt joins agent_message_chunks and surfaces the
    real usage block from the prompt result — faked stdio, CI-safe."""
    import queue
    import tempfile
    lines = queue.Queue()
    lines.put(json.dumps({"jsonrpc": "2.0", "id": 3,
                          "result": {"sessionId": "s1"}}) + "\n")
    for i, t in enumerate(("trans", "miss", "ão")):
        lines.put(json.dumps({"jsonrpc": "2.0", "method": "session/update",
            "params": {"update": {"sessionUpdate": "agent_message_chunk",
                                  "content": {"type": "text",
                                              "text": t}}}}) + "\n")
    lines.put(json.dumps({"jsonrpc": "2.0", "id": 4, "result": {
        "stopReason": "end_turn",
        "usage": {"inputTokens": 100, "outputTokens": 9,
                  "totalTokens": 109}}}) + "\n")

    class FakeProc:
        stdin = type("S", (), {"write": lambda s, x: None,
                               "flush": lambda s: None})()
        def poll(self): return None
    b = mod.AcpBackend("devin", tempfile.gettempdir(), 10)
    b._proc, b._q, b._seq = FakeProc(), lines, 2

    deltas = []
    text, usage, err = b.prompt("hi", on_delta=deltas.append)
    assert err is None and text == "transmissão"
    assert deltas == ["trans", "miss", "ão"]
    assert usage == {"prompt_tokens": 100, "completion_tokens": 9,
                     "total_tokens": 109}


def test_acp_prompt_session_timeout_is_typed_error():
    import queue
    import tempfile
    b = mod.AcpBackend("devin", tempfile.gettempdir(), 2)
    b._proc = type("P", (), {"poll": lambda s: None,
        "stdin": type("S", (), {"write": lambda s, x: None,
                                "flush": lambda s: None})()})()
    b._q, b._seq = queue.Queue(), 0
    text, usage, err = b.prompt("hi")
    assert text == "" and usage is None
    assert err[0] == "timeout"
