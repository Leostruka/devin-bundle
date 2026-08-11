#!/usr/bin/env python3
"""Start the brainstorm visual companion server.

Usage:
  python start-server.py [--project-dir <path>] [--host <bind-host>] [--url-host <display-host>] [--idle-timeout-minutes <n>] [--open] [--foreground] [--background]

Starts server on a random high port, outputs JSON with URL.
Each session gets its own directory to avoid conflicts.

Options:
  --project-dir <path>    Store session files under <path>/.devin/brainstorm/
                          instead of a temp dir. Files persist after server stops.
  --host <bind-host>      Host/interface to bind (default: 127.0.0.1).
  --url-host <host>       Hostname shown in returned URL JSON.
  --idle-timeout-minutes  Shut down after n minutes idle (default 240 = 4h).
  --open                  Auto-open the browser on the first screen.
  --foreground            Run server in the current terminal.
  --background            Force background mode.
"""
import argparse
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path


def is_windows():
    return sys.platform == "win32"


def random_hex(n):
    return "".join(random.choice("0123456789abcdef") for _ in range(n))


def generate_server_id():
    return random_hex(32)


def find_node():
    """Find the node executable."""
    node = shutil.which("node")
    if not node:
        print('{"error": "node not found in PATH"}')
        sys.exit(1)
    return node


def wait_for_log(log_file, timeout=5.0):
    """Wait for the server to write 'server-started' to its log."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "server-started" in line:
                        return line.strip()
        time.sleep(0.1)
    return None


def wait_for_process_alive(process, seconds=2.0):
    """Return True if the process is still alive after a short window."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        time.sleep(0.1)
    return process.poll() is None


def main():
    parser = argparse.ArgumentParser(description="Start the brainstorm visual companion server.")
    parser.add_argument("--project-dir", help="Store session files under <path>/.devin/brainstorm/")
    parser.add_argument("--host", default="127.0.0.1", help="Host/interface to bind")
    parser.add_argument("--url-host", help="Hostname shown in returned URL JSON")
    parser.add_argument("--idle-timeout-minutes", type=int, help="Idle shutdown in minutes")
    parser.add_argument("--open", action="store_true", help="Auto-open the browser")
    parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    parser.add_argument("--background", action="store_true", help="Force background mode")
    args = parser.parse_args()

    bind_host = args.host
    url_host = args.url_host or ("localhost" if bind_host in ("127.0.0.1", "localhost") else bind_host)

    script_dir = Path(__file__).resolve().parent
    server_js = script_dir / "server.cjs"
    if not server_js.exists():
        print('{"error": "server.cjs not found next to start-server.py"}')
        sys.exit(1)

    # Determine session directory
    if args.project_dir:
        session_root = Path(args.project_dir) / ".devin" / "brainstorm"
        session_id = f"{os.getpid()}-{int(time.time())}"
        session_dir = session_root / session_id
        port_file = session_root / ".last-port"
        token_file = session_root / ".last-token"
    else:
        session_id = f"brainstorm-{os.getpid()}-{int(time.time())}"
        session_dir = Path("/tmp" if not is_windows() else os.environ.get("TEMP", "/tmp")) / session_id
        port_file = token_file = None

    session_dir.mkdir(parents=True, exist_ok=True)
    content_dir = session_dir / "content"
    state_dir = session_dir / "state"
    content_dir.mkdir(exist_ok=True)
    state_dir.mkdir(exist_ok=True)

    pid_file = state_dir / "server.pid"
    log_file = state_dir / "server.log"
    server_id_file = state_dir / "server-instance-id"

    # Kill any existing server recorded in this state dir
    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            if is_windows():
                os.system(f'taskkill /PID {old_pid} /F >nul 2>&1')
            else:
                try:
                    os.kill(old_pid, 0)  # check exists
                except ProcessLookupError:
                    pass
                else:
                    os.kill(old_pid, 15)
        except (ValueError, ProcessLookupError, OSError):
            pass
        pid_file.unlink(missing_ok=True)

    server_id = generate_server_id()
    server_id_file.write_text(server_id, encoding="utf-8")

    # Owner PID: leave empty on Windows because Node cannot verify MSYS/PowerShell PIDs reliably
    owner_pid = str(os.getppid()) if not is_windows() else ""

    env = os.environ.copy()
    env["BRAINSTORM_DIR"] = str(session_dir)
    env["BRAINSTORM_HOST"] = bind_host
    env["BRAINSTORM_URL_HOST"] = url_host
    if owner_pid:
        env["BRAINSTORM_OWNER_PID"] = owner_pid
    if args.open:
        env["BRAINSTORM_OPEN"] = "1"
    if args.idle_timeout_minutes:
        env["BRAINSTORM_IDLE_TIMEOUT_MS"] = str(args.idle_timeout_minutes * 60 * 1000)
    if port_file:
        env["BRAINSTORM_PORT_FILE"] = str(port_file)
    if token_file:
        env["BRAINSTORM_TOKEN_FILE"] = str(token_file)

    node = find_node()
    cmd = [node, str(server_js), f"--brainstorm-server-id={server_id}"]

    foreground = args.foreground
    if not foreground and not args.background and is_windows():
        # On Windows background processes may be reaped; default to foreground
        foreground = True

    try:
        if foreground:
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if is_windows() else 0,
            )
            pid_file.write_text(str(process.pid), encoding="utf-8")
            for line in process.stdout:
                print(line, end="")
            sys.exit(process.returncode)
        else:
            with open(log_file, "w", encoding="utf-8") as log:
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    cwd=script_dir,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=False,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if is_windows() else 0,
                )
            pid_file.write_text(str(process.pid), encoding="utf-8")

            started_line = wait_for_log(log_file, timeout=5.0)
            if started_line and wait_for_process_alive(process, seconds=2.0):
                print(started_line)
                sys.exit(0)
            else:
                project_dir_text = args.project_dir or ""
                print(f'{{"error": "Server started but was killed. Retry with: python start-server.py --project-dir {project_dir_text} --host {bind_host} --url-host {url_host} --foreground"}}')
                sys.exit(1)
    except Exception as e:
        print(f'{{"error": "Failed to start server: {e}"}}')
        sys.exit(1)


if __name__ == "__main__":
    main()
