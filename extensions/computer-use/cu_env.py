#!/usr/bin/env python3
"""Environment prerequisites — read-only doctor.

doctor(which, run, ...) -> report dict
  Inspects platform, QEMU binary, version, announced vs initialized
  accelerators, free disk/RAM, and an explicitly-indicated image.
  Never installs, never enables OS features, never starts a VM:
  `actions_performed` is always []. Deficiencies land in
  `required_user_actions` for a human to resolve.

`run` seam: run(argv, timeout_s) ->
  {"returncode": int, "stdout": str, "stderr": str, "timed_out": bool}
  The accel init probe relies on `-machine none`: a process that stays
  alive past the deadline initialized the accelerator (subprocess.run
  kills it); a fast non-zero exit means it did not. TCG is never a
  substitute for the platform accelerator.
"""
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ACCEL_PREFERRED = {"Windows": "whpx", "Linux": "kvm", "Darwin": "hvf"}
_ACCEL_HELP_RE = re.compile(r"^[a-z0-9_-]+$")
_VERSION_RE = re.compile(r"version (\d+\.\d+\.\d+)")


def _default_run(argv, timeout_s=10):
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=timeout_s)
        return {"returncode": proc.returncode, "stdout": proc.stdout,
                "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "",
                "timed_out": True}


def _qemu_binary(machine):
    arch = {"AMD64": "x86_64", "x86_64": "x86_64",
            "ARM64": "aarch64", "aarch64": "aarch64"}.get(machine, "x86_64")
    return f"qemu-system-{arch}"


def _parse_accel_listing(text):
    out = []
    for line in text.splitlines():
        tok = line.strip().lower()
        if _ACCEL_HELP_RE.match(tok):
            out.append(tok)
    return out


def _probe_accel(run, qemu_path, accel, timeout_s):
    """Init probe on a real machine type, CPU frozen (-S): `-machine none`
    is not a valid accel target (QEMU ≥11 errors on it). Staying alive
    past the deadline = the accelerator initialized."""
    argv = [qemu_path, "-machine", "q35", "-accel", accel,
            "-display", "none", "-monitor", "none", "-S", "-nodefaults"]
    res = run(argv, timeout_s)
    return res["timed_out"] or res["returncode"] == 0


def _free_ram_mib(sysname):
    try:
        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_AVPHYS_PAGES")
            return pages * os.sysconf("SC_PAGE_SIZE") // (1024 * 1024)
        if sysname == "Windows":
            import ctypes

            class _Mem(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong),
                            ("memory_load", ctypes.c_ulong),
                            ("total_phys", ctypes.c_ulonglong),
                            ("avail_phys", ctypes.c_ulonglong),
                            ("total_pf", ctypes.c_ulonglong),
                            ("avail_pf", ctypes.c_ulonglong),
                            ("total_virt", ctypes.c_ulonglong),
                            ("avail_virt", ctypes.c_ulonglong),
                            ("avail_ext_virt", ctypes.c_ulonglong)]

            st = _Mem()
            st.length = ctypes.sizeof(_Mem)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return st.avail_phys // (1024 * 1024)
    except (ValueError, OSError, AttributeError):
        pass
    return None


def _check_image(image_path, image_sha256):
    if image_path is None:
        return None
    entry = {"path": image_path, "present": False,
             "sha256": None, "approved": False}
    if not os.path.isfile(image_path):
        return entry
    entry["present"] = True
    if image_sha256 is None:
        return entry
    digest = hashlib.sha256()
    with open(image_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    entry["sha256"] = digest.hexdigest()
    entry["approved"] = entry["sha256"] == image_sha256.lower()
    return entry


def doctor(which=None, run=None, sysname=None, image_path=None,
           image_sha256=None, disk_path=None, probe_timeout_s=5,
           qemu_path=None):
    """Read-only prerequisite report; performs zero mutations.
    qemu_path overrides PATH lookup (fresh installs lag shells)."""
    which = which or shutil.which
    run = run or _default_run
    sysname = sysname or platform.system()
    machine = platform.machine()

    report = {"schema_version": 1, "provider": "qemu", "ready": False,
              "platform": {"system": sysname, "machine": machine,
                           "python": platform.python_version()},
              "qemu": {"path": None, "version": None},
              "accelerators": {"listed": [], "verified": [],
                               "preferred": ACCEL_PREFERRED.get(sysname)},
              "resources": {"disk_free_mib": None, "ram_mib_free": None},
              "image": None,
              "required_user_actions": [],
              "actions_performed": []}
    actions = report["required_user_actions"]

    try:
        usage = shutil.disk_usage(disk_path or tempfile.gettempdir())
        report["resources"]["disk_free_mib"] = usage.free // (1024 * 1024)
    except OSError:
        pass
    report["resources"]["ram_mib_free"] = _free_ram_mib(sysname)

    if qemu_path is not None and not os.path.isfile(qemu_path):
        actions.append(f"qemu_path_missing: {qemu_path}")
        report["image"] = _check_image(image_path, image_sha256)
        return report
    qemu_path = qemu_path or which(_qemu_binary(machine))
    if not qemu_path:
        actions.append("install_qemu: qemu-system binary not found on PATH")
        report["image"] = _check_image(image_path, image_sha256)
        return report
    report["qemu"]["path"] = qemu_path

    try:
        res = run([qemu_path, "--version"], 15)
        m = _VERSION_RE.search(res["stdout"])
        if m:
            report["qemu"]["version"] = m.group(1)
        else:
            actions.append("qemu_version_unreadable: reinstall or fix QEMU")
            report["image"] = _check_image(image_path, image_sha256)
            return report
    except Exception as exc:  # spawn/timeout failures are data, not crashes
        actions.append(f"qemu_probe_failed: {type(exc).__name__}")
        report["image"] = _check_image(image_path, image_sha256)
        return report

    try:
        res = run([qemu_path, "-accel", "help"], 15)
        report["accelerators"]["listed"] = _parse_accel_listing(
            res["stdout"] + "\n" + res["stderr"])
    except Exception as exc:
        actions.append(f"accel_listing_failed: {type(exc).__name__}")

    preferred = report["accelerators"]["preferred"]
    if preferred and preferred in report["accelerators"]["listed"]:
        try:
            if _probe_accel(run, qemu_path, preferred, probe_timeout_s):
                report["accelerators"]["verified"].append(preferred)
            else:
                actions.append(
                    f"enable_accelerator: {preferred} listed but failed "
                    "to initialize")
        except Exception as exc:
            actions.append(f"accel_probe_failed: {type(exc).__name__}")
    elif preferred:
        actions.append(
            f"enable_accelerator: {preferred} not announced by QEMU")
    else:
        actions.append(f"unknown_platform_accelerator: {sysname}")

    report["image"] = _check_image(image_path, image_sha256)
    if report["image"] is None:
        actions.append("indicate_approved_image: no image_path given")
    elif not report["image"]["present"]:
        actions.append("image_missing: indicated image not found")
    elif not report["image"]["approved"]:
        actions.append("image_not_approved: sha256 missing or mismatched")

    report["ready"] = (
        report["qemu"]["version"] is not None
        and preferred in report["accelerators"]["verified"]
        and (report["image"] is None
             or (report["image"]["present"] and report["image"]["approved"]))
    )
    return report


# ---------------------------------------------------------------------------
# C04 — lifecycle: validated spec, consent-bound mutations, supervisor-owned
# QEMU process. Mutating ops never run without an interactive human approval
# bound to the spec digest; a spec mutated after consent fails closed.
# ---------------------------------------------------------------------------

class ConsentDenied(Exception):
    """Mutating lifecycle op without (or after) human consent."""


class SpecMismatch(Exception):
    """On-disk artifact diverges from the approved spec (image/binary)."""


_ACCELS = {"whpx", "kvm", "hvf"}
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_spec(spec):
    """List of human-readable errors; [] means the spec is consumable.
    Closed profile: network/clipboard/mounts/devices must be explicitly
    off — absent or permissive values are errors, never defaults."""
    errors = []
    if not isinstance(spec, dict):
        return ["spec_not_a_mapping"]
    if spec.get("schema_version") != 1:
        errors.append("schema_version: must be 1")
    try:
        import cu_target
        cu_target._check_component(spec.get("env_id"), "env_id")
    except (ValueError, ImportError):
        errors.append("env_id: missing or unsafe component")
    if spec.get("provider") != "qemu":
        errors.append("provider: only 'qemu' supported")
    if not isinstance(spec.get("image_ref"), str) \
            or not spec["image_ref"]:
        errors.append("image_ref: required")
    digest = spec.get("image_sha256")
    if not isinstance(digest, str) or not _SHA_RE.match(digest.lower()):
        errors.append("image_sha256: must be 64 lowercase hex")
    if spec.get("image_format", "iso") not in ("iso", "qcow2"):
        errors.append("image_format: 'iso' or 'qcow2'")
    if not isinstance(spec.get("guest_os"), str):
        errors.append("guest_os: required")
    if not isinstance(spec.get("keyboard_layout"), str):
        errors.append("keyboard_layout: required")
    if spec.get("accel") not in _ACCELS:
        errors.append("accel: explicit whpx|kvm|hvf required (no tcg)")
    if not isinstance(spec.get("qemu_path"), str) \
            or not spec["qemu_path"]:
        errors.append("qemu_path: required")
    res = spec.get("resources") or {}
    if not isinstance(res.get("vcpus"), int) or res["vcpus"] < 1:
        errors.append("resources.vcpus: int >= 1")
    if not isinstance(res.get("memory_mib"), int) \
            or res["memory_mib"] < 256:
        errors.append("resources.memory_mib: int >= 256")
    if spec.get("network") != "off":
        errors.append("network: must be 'off' (no implicit sharing)")
    if spec.get("clipboard") != "off":
        errors.append("clipboard: must be 'off'")
    if spec.get("mounts"):
        errors.append("mounts: must be [] (no host paths)")
    if spec.get("physical_devices"):
        errors.append("physical_devices: must be [] (leases are C15)")
    pinned = spec.get("qemu_sha256")
    if pinned is not None and (not isinstance(pinned, str)
                               or not _SHA_RE.match(pinned.lower())):
        errors.append("qemu_sha256: must be 64 lowercase hex")
    return errors


def build_qemu_argv(spec, overlay):
    """Argument list (never a shell string). Closed profile: no display,
    no monitor, no serial on stdout, no NIC. QMP rides stdio pipes owned
    by the supervisor — never a socket."""
    res = spec["resources"]
    argv = [spec["qemu_path"],
            "-name", spec["env_id"],
            "-machine", "q35",
            "-accel", spec["accel"],
            "-smp", str(res["vcpus"]),
            "-m", str(res["memory_mib"]),
            "-display", "none",
            "-monitor", "none",
            "-serial", "none",
            "-nic", "none",
            "-qmp", "stdio",
            "-nodefaults"]
    if spec.get("image_format", "iso") == "iso":
        argv += ["-boot", "once=d", "-cdrom", spec["image_ref"]]
        if overlay is not None:
            argv += ["-drive",
                     f"file={overlay},format=qcow2,if=virtio"]
    else:
        argv += ["-drive", f"file={overlay},format=qcow2,if=virtio"]
    return argv


def _canonical_digest(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def spec_digest(spec):
    return _canonical_digest(spec)


def plan_digest(plan):
    return _canonical_digest(plan)


def interactive_consent(plan, stdin=None, stderr=None):
    """Human-in-the-loop approval. A piped stdin (agent, CI, script) is
    NOT a consent channel — refuse without a real TTY. The operator must
    type 'yes' after seeing the plan digest."""
    stdin = stdin if stdin is not None else sys.stdin
    stderr = stderr if stderr is not None else sys.stderr
    if not stdin.isatty():
        print(f"refused: {plan.get('op', '?')} requires an interactive "
              "terminal", file=stderr)
        return False
    print(f"plan {plan.get('op', '?')} digest={plan.get('digest', '?')}",
          file=stderr)
    print("type 'yes' to approve: ", end="", file=stderr, flush=True)
    try:
        answer = stdin.readline().strip().lower()
    except (OSError, EOFError):
        return False
    return answer == "yes"


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pid_alive(pid):
    """Existence probe for a pid we recorded — never a name scan."""
    if os.name == "nt":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        try:
            code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(
                    h, ctypes.byref(code)):
                return False
            return code.value == 259  # STILL_ACTIVE
        finally:
            ctypes.windll.kernel32.CloseHandle(h)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _atomic_write_json(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    os.replace(tmp, path)


class EnvironmentManager:
    """Owns env lifecycle for one spec: create overlay, start QEMU under a
    Supervisor (private QMP stdio), stop, reset.

    Seam params: run(argv,timeout)->dict, spawn(argv)->proc,
    consent(plan)->bool. Defaults are the real subprocess/TTY paths;
    tests inject fakes. Every mutating op requires consent bound to the
    spec digest — mutating the spec after approval fails closed.
    """

    def __init__(self, spec, root=None, run=None, spawn=None,
                 consent=None, wait_ready=None, ipc=None):
        self.spec = spec
        env_id = spec.get("env_id", "env") if isinstance(spec, dict) \
            else "env"
        if root is None:
            import cu_target
            root = Path(cu_target.runtime_root()) / env_id
        self.root = Path(root)
        self.env_dir = self.root / env_id
        self._run = run or _default_run
        self._spawn = spawn or self._default_spawn
        self._consent = consent or interactive_consent
        self._wait_ready = wait_ready or self._wait_ready_file
        if ipc is None:
            import cu_qmp_backend
            ipc = cu_qmp_backend.ipc_call
        self._ipc = ipc
        self._approved_digest = None
        self._daemon = None
        self._state_file = self.env_dir / "state.json"

    @staticmethod
    def _default_spawn(argv):
        """Daemon process: detached from our stdio — it outlives this CLI
        and owns QEMU's QMP pipes. Crashes land in daemon-error.txt."""
        return subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

    def _wait_ready_file(self, deadline_s):
        import time
        ready = self.env_dir / "ready.json"
        end = time.monotonic() + deadline_s
        while time.monotonic() < end:
            try:
                data = json.loads(ready.read_text("utf-8"))
                if data.get("socket") and data.get("qemu_pid"):
                    return data
            except (OSError, json.JSONDecodeError):
                pass
            time.sleep(0.1)
        return None

    @property
    def overlay_path(self):
        return str(self.env_dir / "overlay.qcow2")

    # -- validation / provenance -------------------------------------------

    def _validate(self):
        errors = validate_spec(self.spec)
        if errors:
            raise ValueError("invalid_spec:" + ";".join(errors))

    def _check_spec_unchanged(self):
        if self._approved_digest is not None \
                and spec_digest(self.spec) != self._approved_digest:
            raise ConsentDenied("spec_changed_after_consent")

    def _verify_image(self):
        actual = _sha256_file(self.spec["image_ref"])
        if actual != self.spec["image_sha256"].lower():
            raise SpecMismatch("image_sha256")

    def _verify_binary(self):
        pinned = self.spec.get("qemu_sha256")
        if pinned and _sha256_file(self.spec["qemu_path"]) \
                != pinned.lower():
            raise SpecMismatch("qemu_sha256")

    def _require_consent(self, op, detail=None):
        plan = {"op": op, "env_id": self.spec.get("env_id"),
                "spec_sha256": spec_digest(self.spec)}
        if detail:
            plan["detail"] = detail
        plan["digest"] = plan_digest(plan)
        if not self._consent(plan):
            raise ConsentDenied(op)
        self._approved_digest = plan["spec_sha256"]

    # -- overlay ------------------------------------------------------------

    def _resolve_overlay(self, override):
        p = Path(override) if override is not None \
            else Path(self.overlay_path)
        if not p.is_absolute():
            p = self.env_dir / p
        rp, rr = p.resolve(), self.root.resolve()
        if os.path.commonpath([str(rr), str(rp)]) != str(rr):
            raise ValueError(f"escape:{p}")
        return rp

    def _qemu_img(self):
        q = Path(self.spec["qemu_path"])
        suffix = ".exe" if q.name.lower().endswith(".exe") else ""
        return str(q.with_name("qemu-img" + suffix))

    def _create_overlay(self, overlay):
        if self.spec.get("image_format", "iso") == "qcow2":
            argv = [self._qemu_img(), "create", "-f", "qcow2",
                    "-b", self.spec["image_ref"], "-F", "qcow2",
                    str(overlay)]
        else:
            size = self.spec.get("disk_mib", 8192)
            argv = [self._qemu_img(), "create", "-f", "qcow2",
                    str(overlay), f"{size}M"]
        res = self._run(argv, 60)
        if res["timed_out"] or res["returncode"] != 0:
            raise RuntimeError(f"qemu-img failed: {res['stderr'][:200]}")

    # -- public ops ----------------------------------------------------------

    def create(self, override_overlay=None):
        self._validate()
        self._verify_image()
        overlay = self._resolve_overlay(override_overlay)
        self._require_consent("create", {"overlay": str(overlay)})
        import cu_target
        cu_target.ensure_private_dir(self.env_dir)
        self._create_overlay(overlay)
        _atomic_write_json(self._state_file,
                           {"env_id": self.spec["env_id"], "pid": None,
                            "instance_id": None, "running": False,
                            "spec_sha256": spec_digest(self.spec)})
        return overlay

    def start(self):
        self._check_spec_unchanged()
        self._require_consent("start")
        self._start()

    def _start(self):
        self._verify_image()
        self._verify_binary()
        import cu_target
        cu_target.ensure_private_dir(self.env_dir)
        _atomic_write_json(self.env_dir / "spec.approved.json", self.spec)
        daemon_py = Path(__file__).with_name("cu_env_daemon.py")
        argv = [sys.executable, str(daemon_py),
                "--env-dir", str(self.env_dir)]
        proc = self._spawn(argv)
        self._daemon = proc
        ready = self._wait_ready(15)
        if ready is None:
            try:
                proc.kill()
            except Exception:
                pass
            self._daemon = None
            raise RuntimeError("daemon_ready_timeout")
        instance_id = f"i-{uuid.uuid4().hex[:12]}"
        _atomic_write_json(self._state_file,
                           {"env_id": self.spec["env_id"],
                            "pid": proc.pid,
                            "qemu_pid": ready.get("qemu_pid"),
                            "socket": ready.get("socket"),
                            "token": ready.get("token"),
                            "instance_id": instance_id, "running": True,
                            "spec_sha256": spec_digest(self.spec)})

    def status(self):
        state = {}
        try:
            state = json.loads(self._state_file.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        running = False
        if self._daemon is not None and self._daemon.poll() is None:
            running = True
        elif state.get("pid") and state.get("running"):
            running = _pid_alive(state["pid"])
        return {"env_id": self.spec.get("env_id"),
                "running": running,
                "pid": state.get("pid"),
                "qemu_pid": state.get("qemu_pid"),
                "instance_id": state.get("instance_id")}

    def stop(self, force=False):
        self._check_spec_unchanged()
        self._require_consent("stop:force" if force else "stop")
        self._stop(force=force)

    def _stop(self, force=False):
        """Graceful: IPC system_powerdown to the daemon, which forwards it
        over QMP. The daemon exits when QEMU does. force kills the daemon
        proc — its atexit kills QEMU, no orphans."""
        try:
            state = json.loads(self._state_file.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
        sock = state.get("socket")
        if sock:
            try:
                self._ipc(sock, {"command": "system_powerdown"}, 10,
                          token=state.get("token"))
            except Exception:
                pass
        daemon = self._daemon
        if daemon is not None:
            import time
            end = time.monotonic() + 15
            while time.monotonic() < end and daemon.poll() is None:
                time.sleep(0.1)
            if daemon.poll() is None:
                if not force:
                    raise TimeoutError("powerdown_timeout")
                daemon.kill()
                daemon.wait(timeout=5)
        self._daemon = None
        try:
            state = json.loads(self._state_file.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {"env_id": self.spec.get("env_id")}
        state.update({"running": False, "pid": None, "qemu_pid": None})
        _atomic_write_json(self._state_file, state)

    def reset(self):
        """Cold reset: wipe overlay, new instance_id, fresh boot. Old
        observations die with the old instance."""
        self._check_spec_unchanged()
        self._require_consent("reset")
        self._stop(force=True)
        overlay = Path(self.overlay_path)
        if overlay.exists():
            overlay.unlink()
        self._create_overlay(overlay)
        self._start()
