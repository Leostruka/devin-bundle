#!/usr/bin/env python3
"""One-time Google OAuth setup for the gcal backend.

Reads a Desktop-app client_secret.json (or --client-id/--client-secret),
opens the consent URL in the browser (calendar.readonly +
calendar.events, access_type=offline, prompt=consent), catches the code
on 127.0.0.1, exchanges it for tokens, and appends a [gcal] section to
credentials.toml. Secrets are written to disk, never printed.

Prereq: Google Cloud project with Calendar API enabled, OAuth consent
screen configured, and the app PUBLISHED (Testing mode expires refresh
tokens after 7 days). OAuth client type must be "Desktop app".

Usage:
  python oauth_setup.py --client-secret client_secret.json
  python oauth_setup.py --client-id ID --client-secret SECRET
"""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gcal  # noqa: E402

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = ("https://www.googleapis.com/auth/calendar.readonly "
          "https://www.googleapis.com/auth/calendar.events "
          "https://www.googleapis.com/auth/calendar.calendars")
WAIT_SECONDS = 900


def _load_client(args):
    if args.client_secret:
        with open(args.client_secret, encoding="utf-8") as fh:
            data = json.load(fh)
        inst = data.get("installed") or data.get("web") or {}
        if not (inst.get("client_id") and inst.get("client_secret")):
            raise SystemExit("client_secret.json lacks client_id/secret")
        return inst["client_id"], inst["client_secret"]
    if args.client_id and args.client_secret_value:
        return args.client_id, args.client_secret_value
    raise SystemExit("pass --client-secret FILE or --client-id + "
                     "--client-secret-value")


def _toml_path():
    for p in gcal._creds_paths():
        if os.path.isfile(p):
            return p
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, "devin", "credentials.toml")
    return os.path.expanduser(
        os.path.join("~", ".config", "devin", "credentials.toml"))


def _write_gcal_section(client_id, client_secret, refresh_token,
                        force=False):
    path = _toml_path()
    existing = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            existing = fh.read()
        if re.search(r"(?m)^\s*\[gcal\]\s*$", existing):
            if not force:
                raise SystemExit(f"[gcal] already present in {path} - "
                                 "re-run with --force to replace it")
            lines = existing.splitlines(keepends=True)
            out, skip = [], False
            for ln in lines:
                if ln.strip() == "[gcal]":
                    skip = True
                    continue
                if skip and ln.lstrip().startswith("["):
                    skip = False
                if not skip:
                    out.append(ln)
            existing = "".join(out).rstrip() + "\n"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    def _toml_str(v):
        return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'

    # write with 0o600 from creation - no default-perms window (review)
    content = (existing + "\n[gcal]\n"
               + f"client_id = {_toml_str(client_id)}\n"
               + f"client_secret = {_toml_str(client_secret)}\n"
               + f"refresh_token = {_toml_str(refresh_token)}\n")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # Windows / FS without POSIX perms
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--client-secret", help="path to client_secret.json")
    ap.add_argument("--client-id")
    ap.add_argument("--client-secret-value")
    ap.add_argument("--force", action="store_true",
                    help="replace an existing [gcal] section")
    ap.add_argument("--timeout", type=int, default=WAIT_SECONDS,
                    help="seconds to wait for browser consent "
                         f"(default {WAIT_SECONDS})")
    args = ap.parse_args()
    client_id, client_secret = _load_client(args)

    # OAuth hardening (issue #411): state binds the callback to this
    # flow; PKCE protects the code on the loopback channel.
    state = secrets.token_urlsafe(16)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()

    got = {}
    done = threading.Event()

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            if q.get("state", [None])[0] != state:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h3>state mismatch - restart setup.</h3>")
                return
            if "code" in q:
                got["code"] = q["code"][0]
            elif "error" in q:
                got["error"] = q["error"][0]
            else:
                # stray request (favicon, prefetch) - not the consent
                # callback; keep waiting instead of exiting early
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h3>missing code/error params</h3>")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h3>Devin gcal setup done - close this tab.</h3>")
            done.set()

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    redirect = f"http://127.0.0.1:{port}/"
    auth = (AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect,
        "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent",
        "state": state, "code_challenge": challenge,
        "code_challenge_method": "S256"}))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("Open this URL in your browser and approve:\n")
    print(auth + "\n")
    try:
        webbrowser.open(auth)
    except Exception:
        pass  # fail-soft: cleanup; preserve primary error
    if not done.wait(args.timeout):
        srv.shutdown()
        raise SystemExit(f"timed out waiting for consent "
                         f"({args.timeout}s)")
    srv.shutdown()
    if "error" in got:
        raise SystemExit(f"consent failed: {got['error']}")
    if "code" not in got:
        raise SystemExit("no code received")

    body = urllib.parse.urlencode({
        "code": got["code"], "client_id": client_id,
        "client_secret": client_secret, "redirect_uri": redirect,
        "grant_type": "authorization_code",
        "code_verifier": verifier}).encode()
    req = urllib.request.Request(TOKEN_URL, data=body,
                                 headers={"Content-Type":
                                          "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=gcal.HTTP_TIMEOUT) as resp:
            tokens = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"token exchange failed (HTTP {e.code}): "
                         f"{detail}")
    except (urllib.error.URLError, ValueError) as e:
        raise SystemExit(f"token exchange failed: {e}")
    refresh = tokens.get("refresh_token")
    if not refresh:
        raise SystemExit("no refresh_token in response - re-run and "
                         "approve with prompt=consent")
    path = _write_gcal_section(client_id, client_secret, refresh,
                               force=args.force)
    json.dump({"status": "ok", "credentials_toml": path,
               "refresh_token": "<stored>",
               "scopes": tokens.get("scope", "").split()},
              sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
