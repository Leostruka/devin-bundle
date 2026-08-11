#!/usr/bin/env python3
"""Stop the brainstorm visual companion server.

Usage:
  python stop-server.py <session_dir>

Kills the server process. Only deletes session directory if it is
under a temp dir. Persistent directories (.devin/) are kept
so mockups can be reviewed later.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def is_windows():
    return sys.platform == "win32"


def read_server_id(path):
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if text and 32 <= len(text) <= 64 and all(c.isalnum() or c in "_-" for c in text):
        return text
    return None


def command_has_server_id(pid, expected_id):
    """Best-effort check that the process command line contains the expected server id."""
    expected_arg = f"--brainstorm-server-id={expected_id}"
    try:
        if is_windows():
            # Try WMIC first, then tasklist
            result = subprocess.run(
                ["wmic", "process", "where", f"ProcessId={pid}", "get", "CommandLine", "/value"],
                capture_output=True,
                text=True,
                errors="replace",
            )
            if result.returncode == 0 and expected_arg in result.stdout:
                return True
        else:
            # Read /proc/pid/cmdline on Linux
            cmdline_path = f"/proc/{pid}/cmdline"
            if os.path.exists(cmdline_path):
                with open(cmdline_path, "rb") as f:
                    cmdline = f.read().replace(b"\0", b" ").decode("utf-8", errors="replace")
                return expected_arg in cmdline
            # Fallback to ps
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                capture_output=True,
                text=True,
                errors="replace",
            )
            return result.returncode == 0 and expected_arg in result.stdout
    except Exception:
        pass
    return False


def is_brainstorm_server(pid, state_dir):
    expected_id = read_server_id(state_dir / "server-instance-id")
    if not expected_id:
        return False
    return command_has_server_id(pid, expected_id)


def is_process_alive(pid):
    """Return True if the process exists and can be signaled."""
    try:
        if is_windows():
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                errors="replace",
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, OSError):
        return False


def terminate(pid):
    """Try graceful shutdown, then force kill."""
    if is_windows():
        os.system(f"taskkill /PID {pid} >nul 2>&1")
        for _ in range(20):
            if not is_process_alive(pid):
                return True
            time.sleep(0.1)
        os.system(f"taskkill /F /PID {pid} >nul 2>&1")
        time.sleep(0.1)
        return not is_process_alive(pid)
    else:
        try:
            os.kill(pid, 15)
        except ProcessLookupError:
            return True
        for _ in range(20):
            if not is_process_alive(pid):
                return True
            time.sleep(0.1)
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
        return not is_process_alive(pid)


def mark_stopped(state_dir, reason):
    (state_dir / "server-info").unlink(missing_ok=True)
    (state_dir / "server-stopped").write_text(
        f'{{"reason":"{reason}","timestamp":{int(time.time())}}}',
        encoding="utf-8",
    )


def main():
    if len(sys.argv) != 2:
        print('{"error": "Usage: python stop-server.py <session_dir>"}')
        sys.exit(1)

    session_dir = Path(sys.argv[1]).resolve()
    if not session_dir.exists():
        print('{"status": "not_running"}')
        sys.exit(0)

    state_dir = session_dir / "state"
    pid_file = state_dir / "server.pid"
    server_id_file = state_dir / "server-instance-id"
    log_file = state_dir / "server.log"

    if not pid_file.exists():
        mark_stopped(state_dir, "no_pid_file")
        print('{"status": "not_running"}')
        return

    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
    except ValueError:
        pid_file.unlink(missing_ok=True)
        server_id_file.unlink(missing_ok=True)
        mark_stopped(state_dir, "stale_pid")
        print('{"status": "stale_pid"}')
        return

    # Refuse to signal a PID we cannot verify is our server
    if not is_brainstorm_server(pid, state_dir):
        pid_file.unlink(missing_ok=True)
        server_id_file.unlink(missing_ok=True)
        mark_stopped(state_dir, "stale_pid")
        print('{"status": "stale_pid"}')
        return

    if not is_process_alive(pid):
        pid_file.unlink(missing_ok=True)
        server_id_file.unlink(missing_ok=True)
        mark_stopped(state_dir, "already_dead")
        print('{"status": "already_dead"}')
        return

    if terminate(pid):
        pid_file.unlink(missing_ok=True)
        server_id_file.unlink(missing_ok=True)
        log_file.unlink(missing_ok=True)
        mark_stopped(state_dir, "stop-server.py")

        # Only delete ephemeral /tmp directories
        try:
            temp_root = Path(os.environ.get("TEMP", "/tmp")).resolve()
            linux_tmp = Path("/tmp").resolve()
            resolved_session = session_dir.resolve()
            if resolved_session.is_relative_to(temp_root) or resolved_session.is_relative_to(linux_tmp):
                shutil.rmtree(session_dir, ignore_errors=True)
        except Exception:
            pass

        print('{"status": "stopped"}')
    else:
        print('{"status": "failed", "error": "process still running"}')
        sys.exit(1)


if __name__ == "__main__":
    main()
