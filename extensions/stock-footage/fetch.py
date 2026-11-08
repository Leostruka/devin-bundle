"""fetch -- thin Pexels + Pixabay stock-footage fetcher.

stdlib urllib only. API keys come from env; absent keys report a typed
"missing" status and no network call is ever made without one.

  python fetch.py search --query "ocean waves" --provider pexels \
      [--per-page 10] [--orientation portrait|landscape|square]
    -> {"ok": true, "status": "ok", "action": "search",
        "result": {"provider": ..., "hits": [{id, width, height,
                   duration, url, preview, files}]}}

  python fetch.py download --provider pexels --id 1234 --out clip.mp4 \
      [--min-width 720]
    -> {"ok": true, "status": "ok", "action": "download",
        "result": {"out": ..., "bytes": ..., "picked": {quality, width}}}

Envelope: {"ok": bool, "status": "ok"|"missing"|"error",
           "action": ..., "result"|"error": ..., "hint"?: ...,
           "duration_s": ...}
Exit 0 = ok, non-zero = error/missing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MAX_JSON = 4 * 1024 * 1024        # 4 MiB cap on API responses
MAX_FILE = 200 * 1024 * 1024      # 200 MiB cap on downloads
TIMEOUT = 30
DL_TIMEOUT = 300
PER_PAGE_MAX = 80

PEXELS_SEARCH = "https://api.pexels.com/videos/search"
PEXELS_VIDEO = "https://api.pexels.com/videos/videos/{id}"
PIXABAY_SEARCH = "https://pixabay.com/api/videos/"

PROVIDERS = ("pexels", "pixabay")
KEY_ENV = {"pexels": "PEXELS_API_KEY", "pixabay": "PIXABAY_API_KEY"}

HINT = {"pexels": "set PEXELS_API_KEY (free key at pexels.com/api)",
        "pixabay": "set PIXABAY_API_KEY (free key at pixabay.com/api/docs)"}


class _FetchError(Exception):
    pass


def envelope(action, status, duration, result=None, error=None):
    env = {"ok": status == "ok", "status": status, "action": action,
           "duration_s": round(duration, 2)}
    if result is not None:
        env["result"] = result
    if error is not None:
        env["error"] = error
    return env


def emit(payload, code=0):
    print(json.dumps(payload, ensure_ascii=False))
    return code


def missing(action, duration, provider):
    env = envelope(action, "missing", duration,
                   error="no_api_key:" + provider)
    env["hint"] = HINT[provider]
    return env


def _get_json(url, headers=None, timeout=TIMEOUT):
    """GET url -> parsed JSON. Raises _FetchError on any failure."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(MAX_JSON + 1)
    except urllib.error.HTTPError as exc:
        raise _FetchError("http_error:%d" % exc.code)
    except (urllib.error.URLError, OSError) as exc:
        raise _FetchError("fetch_error:%s" % exc)
    if len(body) > MAX_JSON:
        raise _FetchError("response_too_large")
    try:
        data = json.loads(body)
    except ValueError:
        raise _FetchError("bad_json")
    if not isinstance(data, dict):
        raise _FetchError("bad_json:not_an_object")
    return data


def _key(provider):
    return os.environ.get(KEY_ENV[provider]) or None


def _hits_pexels(data):
    hits = []
    for v in data.get("videos", []):
        files = v.get("video_files") or []
        pics = v.get("video_pictures") or [{}]
        hits.append({
            "id": v.get("id"),
            "width": v.get("width"),
            "height": v.get("height"),
            "duration": v.get("duration"),
            "url": v.get("url"),
            "preview": pics[0].get("picture"),
            "files": [{"quality": f.get("quality"),
                       "width": f.get("width"),
                       "height": f.get("height"),
                       "link": f.get("link")}
                      for f in files if f.get("link")]})
    return hits


def _hits_pixabay(data):
    hits = []
    for v in data.get("hits", []):
        variants = v.get("videos") or {}
        files = [{"quality": q, "width": f.get("width"),
                  "height": f.get("height"), "link": f.get("url")}
                 for q, f in variants.items() if f.get("url")]
        w = max((f.get("width") or 0 for f in files), default=0)
        h = max((f.get("height") or 0 for f in files), default=0)
        hits.append({
            "id": v.get("id"),
            "width": w or None,
            "height": h or None,
            "duration": v.get("duration"),
            "url": v.get("pageURL"),
            "preview": variants.get("tiny", {}).get("url"),
            "files": files})
    return hits


def _orientation_ok(hit, orientation):
    if not orientation or not hit.get("width") or not hit.get("height"):
        return True
    w, h = hit["width"], hit["height"]
    if orientation == "portrait":
        return h > w
    if orientation == "landscape":
        return w > h
    if orientation == "square":
        return abs(w - h) <= max(w, h) // 10
    return True


def search(args):
    t0 = time.time()
    if not _key(args.provider):
        return missing("search", time.time() - t0, args.provider)
    per_page = max(1, min(args.per_page, PER_PAGE_MAX))
    if args.provider == "pexels":
        params = {"query": args.query, "per_page": per_page}
        if args.orientation:
            params["orientation"] = args.orientation
        url = PEXELS_SEARCH + "?" + urllib.parse.urlencode(params)
        data = _get_json(url, headers={"Authorization": _key("pexels")})
        hits = _hits_pexels(data)
    else:
        params = {"key": _key("pixabay"), "q": args.query,
                  "per_page": per_page, "video_type": "all"}
        url = PIXABAY_SEARCH + "?" + urllib.parse.urlencode(params)
        data = _get_json(url)
        hits = _hits_pixabay(data)
        hits = [h for h in hits if _orientation_ok(h, args.orientation)]
    return envelope("search", "ok", time.time() - t0,
                    result={"provider": args.provider,
                            "query": args.query, "hits": hits})


def _detail(args):
    if args.provider == "pexels":
        data = _get_json(PEXELS_VIDEO.format(id=args.id),
                         headers={"Authorization": _key("pexels")})
        hits = _hits_pexels({"videos": [data]})
    else:
        params = {"key": _key("pixabay"), "id": str(args.id)}
        data = _get_json(PIXABAY_SEARCH + "?" +
                         urllib.parse.urlencode(params))
        hits = _hits_pixabay(data)
    if not hits or not hits[0].get("files"):
        raise _FetchError("no_files:id=%s" % args.id)
    return hits[0]


def _pick(files, min_width):
    """Smallest file meeting min_width; else smallest available."""
    def width(f):
        return f.get("width") or 0
    ok = [f for f in files if width(f) >= min_width]
    pool = ok or list(files)
    return min(pool, key=width)


def download(args):
    t0 = time.time()
    if not _key(args.provider):
        return missing("download", time.time() - t0, args.provider)
    hit = _detail(args)
    picked = _pick(hit["files"], args.min_width)
    req = urllib.request.Request(picked["link"],
                                 headers={"User-Agent": "curl"})
    try:
        with urllib.request.urlopen(req, timeout=DL_TIMEOUT) as resp:
            body = resp.read(MAX_FILE + 1)
    except urllib.error.HTTPError as exc:
        raise _FetchError("http_error:%d" % exc.code)
    except (urllib.error.URLError, OSError) as exc:
        raise _FetchError("fetch_error:%s" % exc)
    if len(body) > MAX_FILE:
        raise _FetchError("file_too_large")
    out = Path(args.out)
    if out.exists():
        raise _FetchError(f"out_exists:{args.out} (refusing to "
                          "overwrite; pick another --out)")
    with open(out, "wb") as fh:
        fh.write(body)
    return envelope("download", "ok", time.time() - t0,
                    result={"out": args.out, "bytes": len(body),
                            "id": hit["id"],
                            "picked": {"quality": picked.get("quality"),
                                       "width": picked.get("width"),
                                       "height": picked.get("height")}})


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fetch")
    sub = ap.add_subparsers(dest="action", required=True)
    sp = sub.add_parser("search")
    sp.add_argument("--query", required=True)
    sp.add_argument("--provider", choices=PROVIDERS, default="pexels")
    sp.add_argument("--per-page", type=int, default=10)
    sp.add_argument("--orientation",
                    choices=("portrait", "landscape", "square"))
    dp = sub.add_parser("download")
    dp.add_argument("--provider", choices=PROVIDERS, default="pexels")
    dp.add_argument("--id", required=True)
    dp.add_argument("--out", required=True)
    dp.add_argument("--min-width", type=int, default=720)
    args = ap.parse_args(argv)
    try:
        env = search(args) if args.action == "search" else download(args)
    except _FetchError as exc:
        env = envelope(args.action, "error", 0.0, error=str(exc))
    return emit(env, 0 if env["ok"] else 1)


if __name__ == "__main__":
    sys.exit(main())
