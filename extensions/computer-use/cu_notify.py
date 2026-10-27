"""Composite notification dispatch for long-running computer-use tasks.

Adapters (all best-effort; a failing adapter never blocks the rest):
    file     append to .devin/scratch/cu_notifications.jsonl (always on)
    toast    Windows toast notification via PowerShell (win32 only)
    webhook  POST JSON to $CU_NOTIFY_WEBHOOK (urllib; skipped if unset)
    script   run $CU_NOTIFY_HOOK with title/message as argv (skipped if unset)

Adapted from ARTEMIS's notifiers/ composite pattern; stdlib-only.

CLI: python cu_notify.py "title" "message" [level]
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOG = os.path.join(ROOT, ".devin", "scratch", "cu_notifications.jsonl")


def _notify_file(title, message, level):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": time.time(), "level": level,
            "title": title, "message": message}) + "\n")
    return True, LOG


def _notify_toast(title, message, _level):
    if os.name != "nt":
        return None, "toast unsupported off-Windows"
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    ps = (
        "$n=[Windows.UI.Notifications.ToastNotificationManager,"
        "Windows.UI.Notifications,ContentType=WindowsRuntime];"
        "$x=$n::GetTemplateContent(1);"
        f"$x.GetElementsByTagName('text')[0].AppendChild($x.CreateTextNode('{esc(title)}'))>$null;"
        f"$x.GetElementsByTagName('text')[1].AppendChild($x.CreateTextNode('{esc(message)}'))>$null;"
        "$t=[Windows.UI.Notifications.ToastNotification]::new($x);"
        "$n::CreateToastNotifier('Cu-Talk').Show($t);")
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True, text=True, timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    return r.returncode == 0, (r.stderr or "").strip() or "toast sent"


def _notify_webhook(title, message, level):
    url = os.environ.get("CU_NOTIFY_WEBHOOK")
    if not url:
        return None, "CU_NOTIFY_WEBHOOK unset"
    body = json.dumps({"title": title, "message": message,
                       "level": level, "ts": time.time()}).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return 200 <= resp.status < 300, f"HTTP {resp.status}"


def _notify_script(title, message, level):
    hook = os.environ.get("CU_NOTIFY_HOOK")
    if not hook:
        return None, "CU_NOTIFY_HOOK unset"
    import shlex
    r = subprocess.run(
        shlex.split(hook, posix=(os.name != "nt")) + [title, message, level],
                       capture_output=True, text=True, timeout=15)
    return r.returncode == 0, (r.stderr or "").strip() or "hook ran"


ADAPTERS = [_notify_file, _notify_toast, _notify_webhook, _notify_script]


def notify(title, message, level="info"):
    """Fan out to all adapters; return {adapter: (ok|None, detail)}."""
    results = {}
    for fn in ADAPTERS:
        try:
            results[fn.__name__] = fn(title, message, level)
        except Exception as exc:
            results[fn.__name__] = (False, str(exc))
    return results


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    title, message = sys.argv[1], sys.argv[2]
    level = sys.argv[3] if len(sys.argv) > 3 else "info"
    print(json.dumps(notify(title, message, level), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
