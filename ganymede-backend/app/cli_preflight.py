"""Check the launcher's CLI configuration without initializing application state."""

from pathlib import Path
import sys

from dotenv import load_dotenv

from app.services.substrate import resolve_claude_bin


def main() -> int:
    # Match app.main: the process environment takes precedence over backend .env.
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    if resolve_claude_bin() is None:
        print(
            "Claude Code CLI was not found. Install it and authenticate with "
            "`claude`, or set GANYMEDE_CLAUDE_BIN to an existing executable path "
            "in the environment or ganymede-backend/.env.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
