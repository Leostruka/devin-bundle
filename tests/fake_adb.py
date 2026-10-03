#!/usr/bin/env python3
"""Fake `adb` — a device-shaped subprocess for E2E tests.

Invoked via adb.bat shim. Every call appends {"argv": [...]} as a JSONL
line to $FAKE_ADB_LOG. Behavior via $FAKE_ADB_MODE:
  ok          one device FAKEDEV01 (default)
  none        `devices` lists none
  two         two devices attached
  unauth      FAKEDEV01\\tunauthorized
  badrc       shell commands exit 1 with a realistic error

Outputs are byte-faithful to real adb: "UI hierchary dumped to:" typo
included, UTF-8 XML on exec-out cat, raw PNG on exec-out screencap.
"""
import json
import os
import struct
import sys
import zlib

SERIAL = "FAKEDEV01"
W, H = 1080, 2400

UI_XML = b"""<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout"
   package="com.android.launcher3" content-desc="" checkable="false"
   checked="false" clickable="false" enabled="true" focusable="false"
   focused="false" scrollable="false" long-clickable="false" password="false"
   selected="false" bounds="[0,0][1080,2400]">
    <node index="0" text="Apps" resource-id="com.android.launcher3:id/apps"
     class="android.widget.TextView" package="com.android.launcher3"
     content-desc="" checkable="false" checked="false" clickable="true"
     enabled="true" focusable="true" focused="false" scrollable="false"
     long-clickable="true" password="false" selected="false"
     bounds="[480,2280][600,2360]" />
    <node index="1" text="" resource-id="com.x:id/gear"
     class="android.widget.ImageButton" package="com.x"
     content-desc="Op\xc3\xa7\xc3\xb5es" checkable="false" checked="false"
     clickable="true" enabled="true" focusable="true" focused="false"
     scrollable="false" long-clickable="false" password="false"
     selected="false" bounds="[900,60][1020,180]" />
    <node index="2" text="desligado" resource-id="" class="android.widget.Button"
     package="com.x" content-desc="" checkable="false" checked="false"
     clickable="true" enabled="false" focusable="true" focused="false"
     scrollable="false" long-clickable="false" password="false"
     selected="false" bounds="[10,400][110,460]" />
    <node index="3" text="ghost" resource-id="" class="android.widget.TextView"
     package="com.x" content-desc="" checkable="false" checked="false"
     clickable="true" enabled="true" focusable="false" focused="false"
     scrollable="false" long-clickable="false" password="false"
     selected="false" bounds="[0,0][0,0]" />
    <node index="4" text="" resource-id="android:id/list"
     class="androidx.recyclerview.widget.RecyclerView" package="com.x"
     content-desc="" checkable="false" checked="false" clickable="false"
     enabled="true" focusable="true" focused="false" scrollable="true"
     long-clickable="false" password="false" selected="false"
     bounds="[0,500][1080,2200]" />
    <node index="5" text="" resource-id="" class="android.view.View"
     package="com.x" content-desc="" checkable="false" checked="false"
     clickable="false" enabled="true" focusable="false" focused="false"
     scrollable="false" long-clickable="false" password="false"
     selected="false" bounds="[0,300][540,360]" />
  </node>
</hierarchy>
"""


def _log(argv):
    path = os.environ.get("FAKE_ADB_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"argv": argv}) + "\n")


def _out(b):
    sys.stdout.buffer.write(b if isinstance(b, bytes)
                            else b.encode("utf-8"))


def _png():
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    row = b"\x00" + bytes(W * 3)          # filter 0 + black RGB row
    raw = row * H
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 1)) + chunk(b"IEND", b""))


def _devices(mode):
    lines = {"ok": f"{SERIAL}\tdevice",
             "badrc": f"{SERIAL}\tdevice",
             "unauth": f"{SERIAL}\tunauthorized",
             "two": f"{SERIAL}\tdevice\nFAKEDEV02\tdevice",
             "none": ""}
    _out("List of devices attached\n" + lines.get(mode, "") + "\n\n")
    return 0


def main():
    argv = sys.argv[1:]
    _log(argv)
    mode = os.environ.get("FAKE_ADB_MODE", "ok")
    # strip global flags: -s SERIAL / -P PORT / -H HOST / -L LOC
    i = 0
    while i < len(argv) and argv[i].startswith("-"):
        i += 2 if argv[i] in ("-s", "-P", "-H", "-L") else 1
    cmd = argv[i:]

    if cmd[:1] == ["devices"]:
        return _devices(mode)
    if cmd[:1] == ["get-state"]:
        _out("device\n")
        return 0
    if cmd[:1] == ["version"]:
        _out("Android Debug Bridge version 1.0.41\n")
        return 0
    if cmd[:2] == ["exec-out", "screencap"]:
        _out(_png())
        return 0
    if cmd[:2] == ["exec-out", "cat"]:
        _out(UI_XML)
        return 0
    if cmd[:3] == ["shell", "uiautomator", "dump"]:
        _out(f"UI hierchary dumped to: {cmd[-1]}\n")   # adb's real typo
        return 0
    if cmd[:1] == ["shell"]:
        if mode == "badrc":
            _out("")
            sys.stderr.write("java.lang.SecurityException: injected\n")
            return 1
        if len(cmd) > 1:
            _out("fake:" + " ".join(str(a) for a in cmd[1:]) + "\n")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
