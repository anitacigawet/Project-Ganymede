"""Tee uvicorn output to both the parent console and ``backend.log``.

Why this exists
---------------
``run_dev.bat`` previously invoked ``uvicorn`` directly.  All output went to
the cmd window only, which made post-hoc diagnosis of a failed run
impossible: scroll buffer limits, accidental window closure, anything
beyond what fit on screen at the moment of failure was lost.

Direct redirection (``uvicorn ... > backend.log 2>&1`` in cmd) writes to
file but kills the live console view — also unacceptable.  PowerShell's
``Tee-Object`` would work but wraps native-command stderr in
``NativeCommandError`` records that pollute the log file with parser noise.

This wrapper sidesteps both: it spawns uvicorn as a child process with
merged stdout+stderr, then forwards each line to the parent console *and*
appends it to ``backend.log``.  Pure Python, no shell quirks.

Usage from ``run_dev.bat``::

    "%VENV_PY%" log_runner.py app.main:app --reload --reload-dir app --port 8000

All arguments after the script name are forwarded verbatim to
``python -m uvicorn``.
"""

from __future__ import annotations

import datetime
import os
import subprocess
import sys


LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend.log")


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: python log_runner.py <uvicorn-args...>\n"
            "  forwards args verbatim to `python -m uvicorn`.",
            file=sys.stderr,
        )
        return 2

    cmd = [sys.executable, "-m", "uvicorn", *sys.argv[1:]]

    # Open the log file with line-buffered text mode.  We rely on flushes
    # at every iteration anyway, but line buffering means a crash mid-write
    # still leaves a complete line on disk.
    with open(LOG_PATH, "a", encoding="utf-8", buffering=1) as logf:
        header = (
            f"\n{'=' * 60}\n"
            f"=== {datetime.datetime.now().isoformat(timespec='seconds')}  "
            f"backend launch via run_dev.bat\n"
            f"=== cmd: {' '.join(cmd)}\n"
            f"{'=' * 60}\n"
        )
        sys.stdout.write(header)
        sys.stdout.flush()
        logf.write(header)
        logf.flush()

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout pipe
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )

        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                logf.write(line)
                logf.flush()
        except KeyboardInterrupt:
            # cmd-window close on Windows sends a CTRL_CLOSE_EVENT; on
            # POSIX a Ctrl-C raises this.  Either way, propagate to uvicorn
            # so it shuts down cleanly.
            proc.terminate()

        proc.wait()
        footer = (
            f"\n=== backend exited with code {proc.returncode} at "
            f"{datetime.datetime.now().isoformat(timespec='seconds')}\n"
        )
        sys.stdout.write(footer)
        logf.write(footer)
        return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
