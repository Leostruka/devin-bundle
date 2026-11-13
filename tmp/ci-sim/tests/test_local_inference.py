"""L5: local inference adapters — BitNet CPU, offloading plans, held-out batch."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

AI_TOOLS = Path(__file__).resolve().parent.parent / "extensions" / "ai-tools"
sys.path.insert(0, str(AI_TOOLS))

import bitnet_adapter as ba
import offload_plan as op
import heldout_batch as hb
import vllm_tpu_runner as vt


def test_build_command_matches_bitnet_contract(tmp_path):
    model = tmp_path / "ggml-model-i2_s.gguf"
    model.write_bytes(b"x")
    cfg = ba.BitNetConfig(binary=tmp_path / "llama-cli", model=model,
                          n_predict=32, threads=4, ctx_size=1024, temperature=0.0)
    argv = ba.build_command(cfg, "hello")
    assert argv[0] == str(tmp_path / "llama-cli")
    assert argv[1:3] == ["-m", str(model)]
    for flag, val in [("-n", "32"), ("-t", "4"), ("-c", "1024"), ("-ngl", "0"), ("--temp", "0.0")]:
        i = argv.index(flag)
        assert argv[i + 1] == val
    i = argv.index("-p")
    assert argv[i + 1] == "hello"


def test_prompt_bounded(tmp_path):
    cfg = ba.BitNetConfig(binary=tmp_path / "x", model=tmp_path / "m",
                          max_prompt_bytes=10)
    with pytest.raises(ValueError):
        ba.build_command(cfg, "p" * 200)


def test_missing_binary_or_model_reports_unavailable(tmp_path):
    cfg = ba.BitNetConfig(binary=tmp_path / "nope", model=tmp_path / "no.gguf")
    r = ba.run("hi", cfg)
    assert r["ok"] is False and r["backend_unavailable"] is True


def test_process_timeout(tmp_path):
    b, m = _files(tmp_path)
    cfg = ba.BitNetConfig(binary=b, model=m, timeout=0.01)

    def slow(*a, **k):
        raise subprocess.TimeoutExpired(cmd=a[0], timeout=0.01)
    orig = subprocess.run
    subprocess.run = slow
    try:
        r = ba.run("hi", cfg)
    finally:
        subprocess.run = orig
    assert r["ok"] is False and r["timed_out"] is True


def test_bad_exit_rc(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    _fake_proc(monkeypatch, stdout="boom", stderr="err", rc=3)
    cfg = ba.BitNetConfig(binary=b, model=m)
    r = ba.run("hi", cfg)
    assert r["ok"] is False and "exit" in r["error"].lower()


def test_suggest_validates_candidate_ids(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    _fake_proc(monkeypatch, '{"choice": "zzz-not-a-candidate"}')
    cfg = ba.BitNetConfig(binary=b, model=m)
    r = ba.suggest("pick", [{"id": "a"}, {"id": "b"}], cfg)
    assert r["type"] == "abstain" and r["authority"] is False


def test_suggest_returns_suggestion_for_valid_id(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    _fake_proc(monkeypatch, 'noise {"choice": "b"} tail')
    cfg = ba.BitNetConfig(binary=b, model=m)
    r = ba.suggest("pick", [{"id": "a"}, {"id": "b"}], cfg)
    assert r["type"] == "suggestion" and r["choice"] == "b"
    assert r["authority"] is False and "confidence" not in r


def test_suggest_abstains_on_garbage_output(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    _fake_proc(monkeypatch, 'not json at all')
    cfg = ba.BitNetConfig(binary=b, model=m)
    r = ba.suggest("pick", [{"id": "a"}], cfg)
    assert r["type"] == "abstain"


def test_llamacpp_moe_offload_flags():
    argv = op.build_argv("llama.cpp", model_is_moe=True, n_gpu_layers=99,
                         n_cpu_moe=8)
    assert argv[argv.index("-ngl") + 1] == "99"
    i = argv.index("--n-cpu-moe")
    assert argv[i + 1] == "8"


def test_llamacpp_all_moe_on_cpu():
    argv = op.build_argv("llama.cpp", model_is_moe=True, n_gpu_layers=99,
                         cpu_moe=True)
    assert "--cpu-moe" in argv


def test_dense_model_rejects_moe_offload():
    with pytest.raises(ValueError, match="MoE"):
        op.build_argv("llama.cpp", model_is_moe=False, cpu_moe=True)


def test_bitnet_backend_is_cpu_first():
    argv = op.build_argv("bitnet.cpp", model_is_moe=False)
    assert argv == ["-ngl", "0"]


def test_bitnet_rejects_expert_offload():
    with pytest.raises(ValueError):
        op.build_argv("bitnet.cpp", model_is_moe=False, cpu_moe=True)


def test_override_tensor_format():
    argv = op.build_argv("llama.cpp", model_is_moe=True,
                         override_tensors=["blk.*.ffn_.*_exps.=CPU"])
    i = argv.index("--override-tensor")
    assert argv[i + 1] == "blk.*.ffn_.*_exps.=CPU"


def test_override_tensor_rejects_bad_format():
    with pytest.raises(ValueError):
        op.build_argv("llama.cpp", model_is_moe=True,
                      override_tensors=["no-equals"])


def test_unknown_backend_rejected():
    with pytest.raises(ValueError):
        op.build_argv("magic-engine")


def _manifest(tmp_path, entries):
    for e in entries:
        f = tmp_path / e["id"]
        f.write_bytes(e.pop("_data"))
        e["path"] = str(f)
        e["sha256"] = hashlib.sha256(f.read_bytes()).hexdigest()
        e.setdefault("split", "heldout")
        e.setdefault("source", "synthetic")
    m = tmp_path / "manifest.json"
    m.write_text(json.dumps({"entries": entries}))
    return m


def test_manifest_hash_tamper_rejected(tmp_path):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"abc"}])
    data = json.loads(m.read_text())
    data["entries"][0]["sha256"] = "0" * 64
    m.write_text(json.dumps(data))
    with pytest.raises(hb.ManifestError, match="sha256"):
        hb.load_manifest(m)


def test_manifest_rejects_non_heldout_split(tmp_path):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x", "split": "train"}])
    with pytest.raises(hb.ManifestError, match="split"):
        hb.load_manifest(m)


def test_manifest_rejects_non_public_source(tmp_path):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x",
                              "source": "proprietary"}])
    with pytest.raises(hb.ManifestError, match="source"):
        hb.load_manifest(m)


def test_manifest_rejects_sensitive_path(tmp_path):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    data = json.loads(m.read_text())
    data["entries"][0]["path"] = str(tmp_path / "credentials" / ".env")
    m.write_text(json.dumps(data))
    with pytest.raises(hb.ManifestError, match="sensitive"):
        hb.load_manifest(m)


def test_manifest_rejects_path_escape(tmp_path):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    data = json.loads(m.read_text())
    data["entries"][0]["path"] = str(tmp_path.parent / "outside.txt")
    m.write_text(json.dumps(data))
    with pytest.raises(hb.ManifestError, match="root"):
        hb.load_manifest(m, data_root=tmp_path)


def test_batch_bounded_jobs(tmp_path):
    m = _manifest(tmp_path, [{"id": f"e{i}", "_data": b"x"} for i in range(5)])
    entries = hb.load_manifest(m, data_root=tmp_path)
    with pytest.raises(ValueError, match="jobs"):
        hb.run_batch(entries, runner=lambda e, p: {"ok": True}, max_jobs=3)


def test_batch_deterministic_records(tmp_path):
    m = _manifest(tmp_path, [{"id": "b", "_data": b"2"},
                             {"id": "a", "_data": b"1"}])
    entries = hb.load_manifest(m, data_root=tmp_path)
    out1 = hb.run_batch(entries, runner=lambda e, p: {"ok": True,
                                                    "output": e["id"]})
    out2 = hb.run_batch(entries, runner=lambda e, p: {"ok": True,
                                                    "output": e["id"]})
    assert [r["id"] for r in out1["results"]] == ["a", "b"]
    assert out1 == out2
    assert "output_sha256" in out1["results"][0]


def test_serve_command_contract():
    argv = vt.build_serve_command("some/model", tensor_parallel_size=8,
                                  max_model_len=4096,
                                  download_dir="/tmp/dl")
    assert argv[:2] == ["vllm", "serve"]
    for f, v in [("--tensor-parallel-size", "8"), ("--max-model-len", "4096"),
                 ("--download_dir", "/tmp/dl")]:
        assert argv[argv.index(f) + 1] == v


def test_tpu_unavailable_reported_honestly(monkeypatch):
    monkeypatch.setitem(sys.modules, "jax", None)
    r = vt.check_tpu()
    assert r["ok"] is False


def test_relative_paths_resolve_against_data_root(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    (root / "e1").write_bytes(b"data")
    m = tmp_path / "m.json"
    import hashlib as h
    m.write_text(json.dumps({"entries": [{
        "id": "e1", "path": "e1",
        "sha256": h.sha256(b"data").hexdigest(),
        "split": "heldout", "source": "public"}]}))
    monkeypatch.chdir(tmp_path.parent)
    entries = hb.load_manifest(m, data_root=root)
    assert entries[0]["id"] == "e1"


def test_manifest_rejects_bad_field_types(tmp_path):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    data = json.loads(m.read_text())
    data["entries"][0]["sha256"] = 12345
    m.write_text(json.dumps(data))
    with pytest.raises(hb.ManifestError):
        hb.load_manifest(m)


def test_oversized_entry_rejected_not_truncated(tmp_path):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x" * 100}])
    with pytest.raises(hb.ManifestError, match="bytes"):
        hb.load_manifest(m, data_root=tmp_path, max_entry_bytes=10)


def test_manifest_size_bound_enforced(tmp_path, monkeypatch):
    m = tmp_path / "m.json"
    m.write_text(json.dumps({"entries": []}))
    monkeypatch.setattr(hb, "MAX_MANIFEST_BYTES", 4)
    with pytest.raises(hb.ManifestError, match="size bound"):
        hb.load_manifest(m)


def test_toctou_bound_bytes(tmp_path):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"original"}])
    entries = hb.load_manifest(m, data_root=tmp_path)
    (tmp_path / "e1").write_bytes(b"TAMPERED-AFTER-LOAD")
    seen = []
    hb.run_batch(entries, runner=lambda e, p: seen.append(p) or {"ok": True})
    assert seen == ["original"]


def test_run_batch_rejects_unvalidated_entries():
    with pytest.raises(ValueError):
        hb.run_batch([{"id": "x", "path": "/tmp/x", "sha256": "0" * 64}],
                     runner=lambda e, p: {"ok": True})


def test_cli_aggregate_fail(monkeypatch, tmp_path, capsys):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    argv = ["heldout_batch.py", "--manifest", str(m), "--data-root",
            str(tmp_path)]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as se:
        hb.main()
    out = json.loads(capsys.readouterr().out)
    assert se.value.code != 0 and out["ok"] is False


def _backend(tmp_path):
    b = tmp_path / "bin.exe"
    mo = tmp_path / "m.gguf"
    b.write_bytes(b"x")
    mo.write_bytes(b"x")
    return b, mo


def _cli_argv(m, tmp_path, out, b, mo):
    return ["heldout_batch.py", "--manifest", str(m), "--data-root",
            str(tmp_path), "--binary", str(b), "--model", str(mo),
            "--out", str(out)]


def test_out_rejects_manifest_collision(monkeypatch, tmp_path, capsys):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    b, mo = _backend(tmp_path)
    before = m.read_bytes()
    monkeypatch.setattr(sys, "argv", _cli_argv(m, tmp_path, m, b, mo))
    monkeypatch.setattr(ba, "run",
                        lambda *a, **k: {"ok": True, "output": "x"})
    with pytest.raises(SystemExit) as se:
        hb.main()
    assert se.value.code != 0
    assert m.read_bytes() == before


def test_out_rejects_entry_collision(monkeypatch, tmp_path, capsys):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    b, mo = _backend(tmp_path)
    entry_path = tmp_path / "e1"
    before = entry_path.read_bytes()
    monkeypatch.setattr(sys, "argv",
                        _cli_argv(m, tmp_path, entry_path, b, mo))
    monkeypatch.setattr(ba, "run",
                        lambda *a, **k: {"ok": True, "output": "x"})
    with pytest.raises(SystemExit) as se:
        hb.main()
    assert se.value.code != 0
    assert entry_path.read_bytes() == before


def test_out_rejects_existing_destination(monkeypatch, tmp_path, capsys):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    b, mo = _backend(tmp_path)
    out = tmp_path / "results.json"
    out.write_text("prior results")
    monkeypatch.setattr(sys, "argv", _cli_argv(m, tmp_path, out, b, mo))
    monkeypatch.setattr(ba, "run",
                        lambda *a, **k: {"ok": True, "output": "x"})
    with pytest.raises(SystemExit) as se:
        hb.main()
    assert se.value.code != 0
    assert out.read_text() == "prior results"


def test_out_writes_fresh_destination(monkeypatch, tmp_path, capsys):
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    b, mo = _backend(tmp_path)
    out = tmp_path / "new-results.json"
    monkeypatch.setattr(sys, "argv", _cli_argv(m, tmp_path, out, b, mo))
    monkeypatch.setattr(ba, "run",
                        lambda *a, **k: {"ok": True, "output": "x"})
    with pytest.raises(SystemExit) as se:
        hb.main()
    data = json.loads(out.read_text())
    assert data["manifest_entries"] == 1


def test_vllm_batch_requires_tpu(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "jax", None)
    m = _manifest(tmp_path, [{"id": "e1", "_data": b"x"}])
    entries = hb.load_manifest(m, data_root=tmp_path)
    r = vt.run_tpu_batch(entries, model="m")
    assert r["ok"] is False and r["backend_unavailable"] is True


def _fake_vllm(outs):
    import types

    class _LLM:
        def __init__(self, **kw):
            pass

        def generate(self, prompts, sp):
            return outs

    return types.SimpleNamespace(
        LLM=_LLM, SamplingParams=lambda **kw: kw)


def _tpu_ok(monkeypatch, tmp_path, outs, n=2):
    m = _manifest(tmp_path,
                  [{"id": f"e{i}", "_data": f"p{i}".encode()}
                   for i in range(n)])
    entries = hb.load_manifest(m, data_root=tmp_path)
    monkeypatch.setattr(vt, "check_tpu", lambda: {"ok": True})
    monkeypatch.setitem(sys.modules, "vllm", _fake_vllm(outs))
    return vt.run_tpu_batch(entries, model="m")


def test_vllm_incomplete_results_not_ok(monkeypatch, tmp_path):
    for outs in ([], ["one"]):
        r = _tpu_ok(monkeypatch, tmp_path, outs)
        assert r["ok"] is False
        assert r["manifest_entries"] == 2


def test_vllm_extra_results_not_ok(monkeypatch, tmp_path):
    out = type("O", (), {"outputs": [type("C", (), {"text": "t"})()]})()
    r = _tpu_ok(monkeypatch, tmp_path, [out] * 3)
    assert r["ok"] is False
    assert r["manifest_entries"] == 2


def test_vllm_complete_batch_ok(monkeypatch, tmp_path):
    out = type("O", (), {"outputs": [type("C", (), {"text": "t"})()]})()
    r = _tpu_ok(monkeypatch, tmp_path, [out, out])
    assert r["ok"] is True
    assert len(r["results"]) == 2
    assert all(x["ok"] for x in r["results"])


def test_serve_binds_localhost_and_bounded_port():
    argv = vt.build_serve_command("m", port=8080)
    assert argv[argv.index("--host") + 1] == "127.0.0.1"
    with pytest.raises(ValueError):
        vt.build_serve_command("m", port=80)


def test_serve_rejects_host_override_in_extra():
    with pytest.raises(ValueError):
        vt.build_serve_command("m", port=8080,
                               extra_flags=["--host", "0.0.0.0"])


def test_bitnet_config_bounds(tmp_path):
    with pytest.raises(ValueError):
        ba.build_command(ba.BitNetConfig(binary="b", model="m",
                                         timeout=float("inf")), "p")
    with pytest.raises(ValueError):
        ba.build_command(ba.BitNetConfig(binary="b", model="m",
                                         timeout=-1), "p")
    with pytest.raises(ValueError):
        ba.build_command(ba.BitNetConfig(binary="b", model="m",
                                         n_predict=10 ** 9), "p")


def test_prompt_must_be_str(tmp_path):
    with pytest.raises((TypeError, ValueError)):
        ba.build_command(ba.BitNetConfig(binary="b", model="m"),
                         prompt=b"bytes")


def test_extra_flags_cannot_override_or_smuggle(tmp_path):
    for flags in (["-ngl", "4"], ["-m", "other.gguf"], ["-p", "x"],
                  ["--temp", "1"], ["--model-url", "http://e/x"]):
        with pytest.raises(ValueError):
            ba.build_command(ba.BitNetConfig(binary="b", model="m",
                                             extra_flags=list(flags)), "p")
    with pytest.raises(ValueError):
        ba.build_command(ba.BitNetConfig(binary="b", model="m",
                                         extra_flags=["http://evil/x"]), "p")


def test_candidates_unique_bounded_safe(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    _fake_proc(monkeypatch, '{"choice": "a"}')
    cfg = ba.BitNetConfig(binary=b, model=m)
    assert ba.suggest("p", [{"id": "a"}, {"id": "a"}], cfg)["type"] == "abstain"
    many = [{"id": f"c{i}"} for i in range(9)]
    assert ba.suggest("p", many, cfg)["type"] == "abstain"
    assert ba.suggest("p", [{"id": "a; rm -rf"}], cfg)["type"] == "abstain"


def test_suggest_strips_prompt_echo(tmp_path, monkeypatch):
    prompt = "pick\n\nPick exactly one of these candidate IDs:\n- \"a\"\n- \"b\"\n\nAnswer ONLY with JSON: {\"choice\": \"<id>\"}"
    b, m = _files(tmp_path)
    _fake_proc(monkeypatch, "> " + prompt + "\n\n" + '{"choice": "b"}')
    cfg = ba.BitNetConfig(binary=b, model=m)
    r = ba.suggest("pick", [{"id": "a"}, {"id": "b"}], cfg)
    assert r["type"] == "suggestion" and r["choice"] == "b"


def test_abstain_does_not_leak_raw_choice(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    _fake_proc(monkeypatch, '{"choice": "SECRET-INVALID"}')
    cfg = ba.BitNetConfig(binary=b, model=m)
    r = ba.suggest("pick", [{"id": "a"}], cfg)
    assert r["type"] == "abstain" and "SECRET-INVALID" not in json.dumps(r)


def test_nul_in_prompt_rejected(tmp_path):
    cfg = ba.BitNetConfig(binary=tmp_path / "b", model=tmp_path / "m")
    with pytest.raises(ValueError):
        ba.build_command(cfg, "a\x00b")
    (tmp_path / "b").write_bytes(b"x")
    (tmp_path / "m").write_bytes(b"x")
    r = ba.run("a\x00b", cfg)
    assert r["ok"] is False and r["backend_unavailable"] is False


def test_binary_model_path_types_validated(tmp_path):
    r = ba.run("p", ba.BitNetConfig(binary=123, model="m"))
    assert r["ok"] is False and "binary" in r["error"].lower()
    r = ba.run("p", ba.BitNetConfig(binary="b", model=None))
    assert r["ok"] is False and "model" in r["error"].lower()


def test_bitnet_offload_rejects_explicit_nonzero_ngl():
    for v in (4, -1, True, "x"):
        with pytest.raises(ValueError):
            op.build_argv("bitnet.cpp", n_gpu_layers=v)
    argv = op.build_argv("bitnet.cpp", n_gpu_layers=0)
    assert argv == ["-ngl", "0"]


def test_offload_nonint_and_zero_bounds():
    for v in (0, -3, True, "x"):
        with pytest.raises(ValueError):
            op.build_argv("llama.cpp", model_is_moe=True, n_cpu_moe=v)
    for v in (True, "x"):
        with pytest.raises(ValueError):
            op.build_argv("llama.cpp", n_gpu_layers=v)


def _files(tmp_path):
    b = tmp_path / "llama-cli"
    m = tmp_path / "m.gguf"
    b.write_bytes(b"x")
    m.write_bytes(b"x")
    return b, m


def _fake_proc(monkeypatch, stdout="", stderr="", rc=0):
    def fake(argv, **kw):
        fake.seen = kw
        return subprocess.CompletedProcess(argv, rc, stdout, stderr)
    monkeypatch.setattr(subprocess, "run", fake)
    return fake


def test_run_uses_utf8_decoding(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    fake = _fake_proc(monkeypatch, "gen")
    ba.run("p", ba.BitNetConfig(binary=b, model=m))
    assert fake.seen.get("encoding") == "utf-8"
    assert fake.seen.get("errors") == "replace"


def test_framed_output_stripped(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    raw = ("banner\navailable commands:\n  /exit\n\n"
           "> p\n\n: generated text\n\n"
           "[ Prompt: 1 t/s | Generation: 2 t/s ]\n\nExiting...")
    _fake_proc(monkeypatch, raw)
    r = ba.run("p", ba.BitNetConfig(binary=b, model=m))
    assert r["ok"] and "generated text" in r["output"]
    assert "Prompt:" not in r["output"] and "banner" not in r["output"]


def test_repeated_prompt_preserved(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    raw = "> Paris\n\n Paris is the capital of Paris.\n\n" \
          "[ Prompt: 1 t/s | Generation: 2 t/s ]\nExiting..."
    _fake_proc(monkeypatch, raw)
    r = ba.run("Paris", ba.BitNetConfig(binary=b, model=m))
    assert "Paris is the capital of Paris" in r["output"]


def test_unframed_output_preserved(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    _fake_proc(monkeypatch, "plain model output, no framing")
    r = ba.run("p", ba.BitNetConfig(binary=b, model=m))
    assert r["output"] == "plain model output, no framing"


def test_suggest_only_uses_generation(tmp_path, monkeypatch):
    b, m = _files(tmp_path)
    q_start = "pick\n\nPick exactly one"
    raw = f"> {q_start} of these candidate IDs:\n- \"a\"\n- \"b\"\n\n" \
          'Answer ONLY with JSON: {"choice": "<id>"}\n\n' \
          '{"choice": "b"}\n[ Prompt: 1 t/s ]\nExiting...'
    _fake_proc(monkeypatch, raw)
    cfg = ba.BitNetConfig(binary=b, model=m)
    r = ba.suggest("pick", [{"id": "a"}, {"id": "b"}], cfg)
    assert r["type"] == "suggestion" and r["choice"] == "b"


def test_bat_binary_rejected(tmp_path):
    if sys.platform != "win32":
        return
    bat = tmp_path / "x.bat"
    bat.write_bytes(b"@echo hi")
    (tmp_path / "m").write_bytes(b"x")
    r = ba.run("p", ba.BitNetConfig(binary=bat, model=tmp_path / "m"))
    assert r["ok"] is False and "backend_unavailable" in r


def test_extra_flags_allowlist_rejects_all_unknown(tmp_path):
    cfg = lambda f: ba.BitNetConfig(binary="b", model="m", extra_flags=f)
    for flags in (["--model", "e.gguf"], ["--model=e.gguf"],
                  ["--prompt", "x"], ["--n-predict", "9"],
                  ["--ctx-size=99"], ["--n-gpu-layers", "2"],
                  ["--gpu-layers=1"], ["--temp", "0.1"],
                  ["positional"], ["--no-warmup"], ["-no-cnv"]):
        with pytest.raises(ValueError):
            ba.build_command(cfg(list(flags)), "p")
    for bad in ("--model", 123, [b"x"]):
        with pytest.raises((ValueError, TypeError)):
            ba.build_command(cfg(bad), "p")
    argv = ba.build_command(cfg([]), "p")
    assert argv[argv.index("-p") + 1] == "p"


def test_vllm_extra_flags_rejected_nonempty():
    for flags in (["--host=0.0.0.0"], ["--host", "0.0.0.0"], ["--port=1"],
                  ["--api-key", "k"], ["--gpu-memory-utilization=0.5"],
                  ["positional"]):
        with pytest.raises(ValueError):
            vt.build_serve_command("m", port=8080, extra_flags=list(flags))
    argv = vt.build_serve_command("m", port=8080, extra_flags=[])
    assert argv[argv.index("--host") + 1] == "127.0.0.1"


def test_manifest_rejects_non_object_json(tmp_path):
    for bad in ("null", "[1,2]", "5", '"s"'):
        m = tmp_path / "m.json"
        m.write_text(bad)
        with pytest.raises(hb.ManifestError):
            hb.load_manifest(m)


# --- audit-r3: typed errors on bad weights -----------------------------------

def test_abliterator_missing_weights_typed(tmp_path, capsys):
    import abliterator
    import argparse
    with pytest.raises(SystemExit) as exc:
        abliterator.run(argparse.Namespace(
            weights=str(tmp_path / "nope.safetensors"), model=None,
            tensor=None, layer=6, self_test=False))
    assert exc.value.code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False and "weights load failed" in out["error"]
