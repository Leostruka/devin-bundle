"""Minimal GetChatMessage probe — hand-encoded protobuf, no CLI.

POST /exa.api_server_pb.ApiServerService/GetChatMessage
auth: Basic base64(windsurf_api_key)
body: connect+proto frame(flags=0, len4, message)

Usage: python recon/internal_probe.py
"""

import base64
import json
import tomllib
import urllib.request
import uuid
from pathlib import Path


def v(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def fld(num: int, wt: int) -> bytes:
    return v((num << 3) | wt)


def s(num: int, text: str) -> bytes:
    b = text.encode()
    return fld(num, 2) + v(len(b)) + b


def m(num: int, body: bytes) -> bytes:
    return fld(num, 2) + v(len(body)) + body


def vi(num: int, val: int) -> bytes:
    return fld(num, 0) + v(val)


def meta(api_key: str) -> bytes:
    inner = b"".join([
        s(1, "devin-cli"), s(2, "3000.12.43"), s(3, api_key),
        s(5, "windows"), s(7, "3000.12.43"), s(12, "chisel"), s(28, "chisel"),
    ])
    return m(1, inner)


def chat_msg(role: int, text: str) -> bytes:
    return m(3, s(1, str(uuid.uuid4())) + vi(2, role) + s(3, text))


def tool(name: str, desc: str, schema: dict) -> bytes:
    return m(10, s(1, name) + s(2, desc) + s(3, json.dumps(schema)))


def build_request(api_key: str, model_uid: str, tools: list) -> bytes:
    req = b"".join([
        meta(api_key),
        chat_msg(1, "What is 2+2? Use the calculator tool."),
        vi(7, 5),
        m(8, vi(1, 1) + vi(2, 128000) + vi(3, 400)),
        *tools,
        s(16, str(uuid.uuid4())),
        vi(20, 1),
        s(21, model_uid),
    ])
    return b"\x00" + len(req).to_bytes(4, "big") + req


def parse_stream(raw: bytes):
    i = 0
    while i + 5 <= len(raw):
        flags = raw[i]
        ln = int.from_bytes(raw[i + 1:i + 5], "big")
        yield flags, raw[i + 5:i + 5 + ln]
        i += 5 + ln


def fields(b: bytes):
    i = 0
    while i < len(b):
        key, i2 = 0, i
        while True:
            key |= (b[i2] & 0x7F) << ((i2 - i) * 7)
            if not (b[i2] & 0x80):
                i2 += 1
                break
            i2 += 1
        fn, wt = key >> 3, key & 7
        i = i2
        if wt == 0:
            val, j = 0, i
            while True:
                val |= (b[j] & 0x7F) << ((j - i) * 7)
                if not (b[j] & 0x80):
                    j += 1
                    break
                j += 1
            yield fn, wt, val
            i = j
        elif wt == 2:
            ln, j = 0, i
            while True:
                ln |= (b[j] & 0x7F) << ((j - i) * 7)
                if not (b[j] & 0x80):
                    j += 1
                    break
                j += 1
            yield fn, wt, b[j:j + ln]
            i = j + ln
        elif wt == 1:
            yield fn, wt, b[i:i + 8]
            i += 8
        elif wt == 5:
            yield fn, wt, b[i:i + 4]
            i += 4
        else:
            return


def main() -> None:
    creds = tomllib.load(open(Path.home() / "AppData/Roaming/devin/credentials.toml", "rb"))
    key = creds["windsurf_api_key"]
    base = creds["api_server_url"].rstrip("/")
    tools = [tool("calculator", "Evaluate an arithmetic expression",
                  {"type": "object",
                   "properties": {"expr": {"type": "string"}},
                   "required": ["expr"]})]
    req_body = build_request(key, "swe-2-max", tools)
    auth = base64.b64encode(key.encode()).decode()
    req = urllib.request.Request(
        base + "/exa.api_server_pb.ApiServerService/GetChatMessage",
        data=req_body, method="POST",
        headers={"content-type": "application/connect+proto",
                 "connect-protocol-version": "1",
                 "authorization": f"Basic {auth}"})
    try:
        r = urllib.request.urlopen(req, timeout=120)
        raw = r.read()
        print("HTTP", r.status, "resp bytes", len(raw))
    except Exception as e:  # noqa: BLE001 - probe
        print("ERR", getattr(e, "code", ""), str(e)[:200])
        if hasattr(e, "read"):
            print(e.read()[:300])
        return
    for flags, fr in parse_stream(raw):
        if flags & 0x80 or flags == 2:
            print("[trailer]", fr[:120])
            continue
        line = {}
        for fn, wt, val in fields(fr):
            if wt == 2 and fn == 3:
                line["delta_text"] = val.decode("utf-8", "replace")[:60]
            elif wt == 2 and fn == 4:
                line["delta_tool_calls_raw"] = val[:120].hex()
            elif wt == 2 and fn == 9:
                line["thinking"] = val.decode("utf-8", "replace")[:60]
            elif wt == 2 and fn == 10:
                line["json_blob"] = val[:100]
            elif wt == 2 and fn == 25:
                line["stop"] = val.decode("utf-8", "replace")
            elif wt == 2 and fn == 28:
                line["usage_raw"] = val[:80].hex()
            elif wt == 2 and fn in (1, 15, 21):
                line[f"f{fn}"] = val.decode("utf-8", "replace")[:40]
        if line:
            print(line)


if __name__ == "__main__":
    main()
