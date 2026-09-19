"""Policy layer: deny-wins classification and one-shot confirmations.

Tokens are random 256-bit values stored as <token>.json containing only
{digest, created_at, expires_at} — never the raw request or its args.
Consumption deletes the token file before validation returns, including
mismatch and expiry. Deny always wins; unknown capabilities deny.
"""

import hashlib
import hmac
import json
import math
import os
import re
import secrets
import tempfile
import time
from pathlib import Path

import sc_contract as contract

STATE_DIR = (Path(tempfile.gettempdir())
             / "devin-system-control-confirmations")

DENY = {"file.delete", "disk.format", "security.disable",
        "credential.read"}
CONFIRM = {
    "process.exec", "process.cancel", "session.spawn", "session.send",
    "session.cancel", "daemon.stop", "service.restart", "file.copy",
    "file.copy_overwrite", "broker.dispatch",
}
ALLOW = {
    "capabilities", "process.observe", "process.wait", "service.observe",
    "file.inspect", "events.open", "events.drain", "events.close",
    "events.list",
    "session.status", "session.recv", "session.resize", "session.close",
    "daemon.start", "daemon.status", "broker.status",
}

TTL_MAX_S = 120
_TOKEN_RE = re.compile(r"[0-9a-f]{64}")


def request_digest(request: dict) -> str:
    """Canonical SHA-256 over the validated request.

    policy.confirmation_id is stripped so an issued token does not
    change the digest; every other field is bound.
    """
    req = contract.validate_request(request)
    if "policy" in req:
        pol = dict(req["policy"])
        pol.pop("confirmation_id", None)
        req["policy"] = pol
    canonical = json.dumps(req, sort_keys=True,
                           separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def classify(request: dict) -> dict:
    """Classify capability: DENY → CONFIRM → ALLOW → unknown deny."""
    req = contract.validate_request(request)
    cap = req["capability"]
    if cap in DENY:
        return {"decision": "deny", "reason": "capability_denied"}
    if cap in CONFIRM:
        return {"decision": "confirm", "reason": "confirmation_required"}
    if cap in ALLOW:
        return {"decision": "allow", "reason": "capability_allowed"}
    return {"decision": "deny", "reason": "unknown_capability"}


def _ensure_state_dir():
    os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
    try:
        os.chmod(STATE_DIR, 0o700)
    except OSError:
        pass  # best-effort on Windows


def _write_metadata(path, meta):
    """Atomic write: random sibling temp file (0o600), fsync, replace."""
    fd, tmpname = tempfile.mkstemp(dir=str(STATE_DIR), prefix=".tok-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(meta, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmpname, path)
    except BaseException:
        try:
            os.unlink(tmpname)
        except OSError:
            pass
        raise


def issue_confirmation(request: dict, ttl_s: int = 120) -> dict:
    """Issue a one-shot token bound to the request digest.

    Only capabilities classified "confirm" may be issued a token —
    deny wins over confirmation.
    """
    if classify(request)["decision"] != "confirm":
        raise contract.InvalidRequest(
            "capability does not require confirmation")
    if (isinstance(ttl_s, bool) or not isinstance(ttl_s, int)
            or not 1 <= ttl_s <= TTL_MAX_S):
        raise contract.InvalidRequest(
            f"ttl_s must be an integer in [1, {TTL_MAX_S}]")
    digest = request_digest(request)
    token = secrets.token_hex(32)
    _ensure_state_dir()
    now = time.time()
    expires_at = now + ttl_s
    _write_metadata(STATE_DIR / f"{token}.json",
                    {"digest": digest, "created_at": now,
                     "expires_at": expires_at})
    return {"confirmation_id": token, "expires_at": expires_at}


def _read_claimed(path, attempts=5):
    """Read an already-claimed token file, retrying transient OSError
    (e.g. Windows AV/indexer locks). Only reached after the atomic
    claim; the claim itself is never retried."""
    for attempt in range(attempts):
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            if attempt + 1 == attempts:
                raise
            time.sleep(0.01)


def _valid_time(v) -> bool:
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v))


def consume_confirmation(request: dict, confirmation_id: str) -> dict:
    """Consume a token: atomic rename claim, delete, then validate."""
    digest = request_digest(request)
    if (not isinstance(confirmation_id, str)
            or not _TOKEN_RE.fullmatch(confirmation_id)):
        return {"ok": False, "reason": "unknown_confirmation"}
    path = STATE_DIR / f"{confirmation_id}.json"
    claimed = (STATE_DIR
               / f".consume-{confirmation_id}-{secrets.token_hex(8)}")
    try:
        os.replace(path, claimed)
    except OSError:
        return {"ok": False, "reason": "unknown_confirmation"}
    try:
        raw = _read_claimed(claimed)
    except (OSError, UnicodeError):
        try:
            claimed.unlink()
        except OSError:
            pass
        return {"ok": False, "reason": "unknown_confirmation"}
    try:
        claimed.unlink()
    except OSError:
        return {"ok": False, "reason": "unknown_confirmation"}
    try:
        meta = json.loads(raw)
    except (ValueError, RecursionError):
        return {"ok": False, "reason": "unknown_confirmation"}
    if (not isinstance(meta, dict)
            or set(meta) != {"digest", "created_at", "expires_at"}):
        return {"ok": False, "reason": "unknown_confirmation"}
    stored = meta["digest"]
    created = meta["created_at"]
    expires = meta["expires_at"]
    if (not isinstance(stored, str) or not _valid_time(created)
            or not _valid_time(expires) or expires < created
            or not 0 < expires - created <= TTL_MAX_S):
        return {"ok": False, "reason": "unknown_confirmation"}
    if time.time() >= expires:
        return {"ok": False, "reason": "expired"}
    if not hmac.compare_digest(stored, digest):
        return {"ok": False, "reason": "request_mismatch"}
    return {"ok": True, "reason": "confirmed"}
