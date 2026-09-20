"""Root-bound file inspection and hash-verified copy.

Path discipline: the relative path must contain no absolute, drive,
"."/".." or (Windows) trailing dot/space components; the realpath of
the candidate must stay under the realpath of root; and no component
under root may be a symlink or reparse point (Windows
FILE_ATTRIBUTE_REPARSE_POINT via lstat).

On POSIX, actual file access is additionally dirfd-bound: components
are opened with os.open(..., dir_fd=fd) using O_NOFOLLOW (+O_DIRECTORY
for intermediates), closing the resolve→open TOCTOU window. On Windows
there is no dirfd API, so the realpath+reparse walk above is the
defence; a residual swap window remains between check and open (to be
closed properly in T7 with handle-based verification).

Copies are hash-pinned end to end: the source is streamed once into a
sibling mkstemp temp while hashing; after fsync the temp is re-read and
re-hashed; commit is os.replace (overwrite) or os.link+unlink
(no-clobber, same-volume — guaranteed by the sibling temp); finally the
destination is re-hashed. Any failure deletes the temp; the source is
never modified. Request-shape violations return status "rejected";
operational OSErrors return status "unknown".
"""

import hashlib
import os
import stat
import tempfile

import sc_contract as contract

_CHUNK = 1 << 20
_HEX64 = frozenset("0123456789abcdef")
_REPARSE = 0x400  # FILE_ATTRIBUTE_REPARSE_POINT
_NT = os.name == "nt"
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
_BINARY = getattr(os, "O_BINARY", 0)


class _Reject(Exception):
    """Path or precondition violation; maps to a rejected envelope."""


def _envelope(ok, status, value=None, precondition=None,
              postcondition=None, error=None):
    return {"ok": ok, "status": status, "value": value,
            "precondition": precondition, "postcondition": postcondition,
            "error": error}


def _reject(reason):
    return _envelope(False, "rejected", error=reason)


def _failure(reason):
    return _envelope(False, "unknown", error=reason)


def _is_reparse(path):
    """True if path is a symlink or Windows reparse point."""
    try:
        if os.path.islink(path):
            return True
        st = os.lstat(path)
    except OSError:
        return False
    return bool(getattr(st, "st_file_attributes", 0) & _REPARSE)


def _parts(rel):
    return [p for p in rel.replace("\\", "/").split("/") if p != ""]


def _resolve(root, rel):
    """Validate + resolve rel under root; raises _Reject.

    Returns (resolved_abspath, parts)."""
    if not isinstance(root, str) or not root or "\x00" in root:
        raise _Reject("root must be a non-empty string")
    if not isinstance(rel, str) or not rel or "\x00" in rel:
        raise _Reject("path must be a non-empty string")
    if (os.path.isabs(rel) or os.path.splitdrive(rel)[0]
            or rel[0] in "/\\"):
        raise _Reject("path must be relative")
    parts = _parts(rel)
    if not parts or any(p in (".", "..") for p in parts):
        raise _Reject("path contains disallowed components")
    if _NT and any(p.endswith((".", " ")) for p in parts):
        raise _Reject("path component ends in dot or space")
    root_real = os.path.realpath(root)
    probe = root_real
    for part in parts:
        probe = os.path.join(probe, part)
        if _is_reparse(probe):
            raise _Reject("path traverses a link or reparse point")
    resolved = os.path.realpath(probe)
    if resolved != root_real and \
            not resolved.startswith(root_real + os.sep):
        raise _Reject("path escapes root")
    return resolved, parts


def _open_under_root(root_fd, parts):
    """POSIX dirfd walk: each intermediate opened O_NOFOLLOW|O_DIRECTORY,
    leaf opened O_RDONLY|O_NOFOLLOW. Caller owns the returned fd."""
    dir_flags = os.O_RDONLY | _NOFOLLOW | _DIRECTORY
    fd = root_fd
    for comp in parts[:-1]:
        nxt = os.open(comp, dir_flags, dir_fd=fd)
        if fd != root_fd:
            os.close(fd)
        fd = nxt
    try:
        return os.open(parts[-1], os.O_RDONLY | _NOFOLLOW | _BINARY,
                       dir_fd=fd)
    finally:
        if fd != root_fd:
            os.close(fd)


def _open_root(root_real):
    if _NT:
        return None  # no dirfd; resolved-path opens + reparse walk
    return os.open(root_real, os.O_RDONLY | _DIRECTORY)


def _open_source(root_fd, parts, resolved):
    """Open a validated source read-only without following links."""
    if root_fd is not None:
        return _open_under_root(root_fd, parts)
    return os.open(resolved, os.O_RDONLY | _BINARY)


def _sha256_fd(fd):
    """Streaming sha256 over an open fd; returns (hexdigest, bytes)."""
    h = hashlib.sha256()
    total = 0
    while True:
        chunk = os.read(fd, _CHUNK)
        if not chunk:
            break
        h.update(chunk)
        total += len(chunk)
    return h.hexdigest(), total


def _sha256_path(path):
    """Streaming sha256 by path (used to re-read the temp after fsync)."""
    h = hashlib.sha256()
    total = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest(), total


def _stream_copy(src_fd, dst_fd):
    """Copy src fd into dst fd while hashing the source stream;
    returns (sha256, bytes). os.write may short-write — loop."""
    h = hashlib.sha256()
    total = 0
    while True:
        chunk = os.read(src_fd, _CHUNK)
        if not chunk:
            break
        view = memoryview(chunk)
        while view:
            written = os.write(dst_fd, view)
            view = view[written:]
        h.update(chunk)
        total += len(chunk)
    return h.hexdigest(), total


def _valid_hash(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in _HEX64 for c in value.lower()))


def validate_copy_args(root, rel_src, rel_dst):
    """Resolve src/dst and check src is a regular file; raises
    InvalidRequest so the CLI rejects before consuming a token."""
    try:
        src, _ = _resolve(root, rel_src)
        dst, _ = _resolve(root, rel_dst)
    except _Reject as exc:
        raise contract.InvalidRequest(str(exc))
    if not os.path.isdir(root):
        raise contract.InvalidRequest("root is not a directory")
    if not os.path.isfile(src):
        raise contract.InvalidRequest("source is not a file")
    if not os.path.isdir(os.path.dirname(dst)):
        raise contract.InvalidRequest("destination parent is missing")
    return src, dst


def _type_of(st):
    if stat.S_ISREG(st.st_mode):
        return "file"
    if stat.S_ISDIR(st.st_mode):
        return "dir"
    return "other"


def _missing_value(resolved):
    return {"path": resolved, "type": "missing", "size": None,
            "mtime": None, "inode": None, "sha256": None,
            "is_link": False}


def inspect_path(root, rel):
    """Stat + hash a file under root; never returns file contents."""
    try:
        resolved, parts = _resolve(root, rel)
    except _Reject as exc:
        return _reject(str(exc))
    root_fd = None
    fd = None
    try:
        if _NT:
            try:
                st = os.lstat(resolved)
            except OSError:
                st = None
            if st is None:
                return _envelope(True, "verified",
                                 value=_missing_value(resolved))
            kind = _type_of(st)
            digest = None
            if kind == "file":
                fd = os.open(resolved, os.O_RDONLY | _BINARY)
                digest, _ = _sha256_fd(fd)
        else:
            root_fd = _open_root(os.path.realpath(root))
            try:
                fd = _open_under_root(root_fd, parts)
            except FileNotFoundError:
                return _envelope(True, "verified",
                                 value=_missing_value(resolved))
            except OSError as exc:
                return _reject(f"inspect rejected: {exc}")
            st = os.fstat(fd)
            kind = _type_of(st)
            digest = None
            if kind == "file":
                digest, _ = _sha256_fd(fd)
        return _envelope(True, "verified", value={
            "path": resolved, "type": kind, "size": st.st_size,
            "mtime": st.st_mtime, "inode": st.st_ino,
            "sha256": digest, "is_link": False})
    except OSError as exc:
        return _failure(f"inspect failed: {exc}")
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass


def copy_verified(root, rel_src, rel_dst, *, expected_hash,
                  dry_run=False, overwrite=False):
    """Copy rel_src to rel_dst under root, hash-verified end to end."""
    if not _valid_hash(expected_hash):
        return _reject("expected_hash must be 64 hex chars")
    expected = expected_hash.lower()
    try:
        src, src_parts = _resolve(root, rel_src)
        dst, _ = _resolve(root, rel_dst)
    except _Reject as exc:
        return _reject(str(exc))
    if not os.path.isdir(root):
        return _reject("root is not a directory")
    dst_parent = os.path.dirname(dst)
    if not os.path.isdir(dst_parent):
        return _reject("destination parent is missing")
    root_fd = None
    src_fd = None
    fd = None
    tmp = None
    try:
        root_fd = _open_root(os.path.realpath(root))
        try:
            src_fd = _open_source(root_fd, src_parts, src)
        except FileNotFoundError:
            return _reject("source is not a file")
        except OSError as exc:
            if getattr(exc, "errno", None) in (40, 20):  # ELOOP/ENOTDIR
                return _reject(f"source rejected: {exc}")
            raise
        st = os.fstat(src_fd)
        if not stat.S_ISREG(st.st_mode):
            return _reject("source is not a regular file")
        if dry_run:
            src_hash, nbytes = _sha256_fd(src_fd)
            if src_hash != expected:
                return _reject("source hash mismatch")
            return _envelope(True, "verified", value={
                "src_sha256": src_hash, "dst": dst, "bytes": nbytes})
        if os.path.lexists(dst) and not overwrite:
            return _reject("destination exists")
        fd, tmp = tempfile.mkstemp(dir=dst_parent, prefix=".copy-")
        src_hash, nbytes = _stream_copy(src_fd, fd)
        if src_hash != expected:
            return _reject("source hash mismatch")
        os.fsync(fd)
        os.close(fd)
        fd = None
        # Re-read the temp after fsync; never trust the write stream.
        tmp_hash, _ = _sha256_path(tmp)
        if tmp_hash != expected:
            return _reject("copy verification failed")
        if overwrite:
            os.replace(tmp, dst)
        else:
            # Atomic no-clobber: sibling temp guarantees same volume.
            try:
                os.link(tmp, dst)
            except FileExistsError:
                return _reject("destination exists")
            os.unlink(tmp)
        tmp = None
        dst_hash, _ = _sha256_path(dst)
        if dst_hash != expected:
            return _failure("postcondition hash mismatch")
        return _envelope(
            True, "verified", value={"dst": dst, "bytes": nbytes},
            precondition={"sha256": expected},
            postcondition={"sha256": dst_hash})
    except OSError as exc:
        return _failure(f"copy failed: {exc}")
    finally:
        for closeable in (fd, src_fd, root_fd):
            if closeable is not None:
                try:
                    os.close(closeable)
                except OSError:
                    pass
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass
