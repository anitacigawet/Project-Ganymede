# Configuration

Copy `ganymede-backend/.env.example` to `ganymede-backend/.env` only when changing defaults.

## Claude CLI

- `GANYMEDE_ENGINE_MODEL`: Claude Code model alias or full ID. Default `sonnet`.
- `GANYMEDE_CLAUDE_BIN`: explicit executable path when `claude` is not on `PATH`.
- `GANYMEDE_CLAUDE_TIMEOUT`: seconds allowed per invocation. Default `600`.
- `GANYMEDE_CLAUDE_MAX_ATTEMPTS`: bounded attempts per invocation. Default `2`.

Authentication belongs to Claude Code. Run `claude` in a terminal and complete its normal sign-in flow. Project Ganymede does not store that authentication in this repository.

## Data and corpus

- `GANYMEDE_SESSION_DB`: SQLite path. Default `ganymede-backend/data/sessions.db`.
- `GANYMEDE_DATA_DIR`: prompt-cache and runtime-data root.
- `GANYMEDE_DISABLE_SESSION_PERSISTENCE=1`: in-memory sessions only.
- `GANYMEDE_FOUNDATIONS_DIR`: alternate foundation directory.
- `GANYMEDE_CORPUS_FILES`: comma-separated foundation filenames to load.

## Browser access

- `GANYMEDE_CORS_ORIGINS`: comma-separated origins. Defaults to localhost on ports 3000 and 3001.
- `GANYMEDE_CORS_ORIGIN_REGEX`: optional extra origin regular expression. Empty by default.
- `NEXT_PUBLIC_GANYMEDE_BASE_URL`: explicit backend URL for the frontend.
- `NEXT_PUBLIC_GANYMEDE_BACKEND_PORT`: backend port when deriving the URL from the page host. Default `8000`.

The launchers bind to `127.0.0.1`. `scripts/start.ps1 -Lan` explicitly changes both services to `0.0.0.0`; use it only on a trusted network and set a narrow CORS origin.

## Advanced compatibility tuning

These settings control retained prompt-size and convergence safeguards:

- `GANYMEDE_LOG_LEVEL`: backend logging level. Default `INFO`.
- `GANYMEDE_S1_INJECTION_BUDGET`: first-stroke injection characters. Default `1800`.
- `GANYMEDE_S2_INJECTION_BUDGET`: second-stroke injection characters. Default `1500`.
- `GANYMEDE_S2_AUDITOR_BUDGET`: second-stroke auditor characters. Default `900`.
- `GANYMEDE_S2_BRIDGE_BUDGET`: second-stroke bridge characters. Default `600`.
- `GANYMEDE_SYNTHESIS_PACKETS_BUDGET`: research-packet characters supplied to synthesis. Default `4500`.
- `GANYMEDE_TRANSLATION_PROMPT_BUDGET`: translation-prompt characters. Default `4800`.
- `GANYMEDE_RESOLUTION_STABLE_THRESHOLD`: similarity threshold used by the stability check. Default `0.85`.

These limits were inherited from an older provider integration and remain active conservative caps. Change them only with regression tests. See [Known limitations](KNOWN_LIMITATIONS.md).

## Frontend edition

Do not set `NEXT_PUBLIC_GANYMEDE_EDITION` manually. The package scripts set the internal `GANYMEDE_EDITION` build flag:

- `npm run dev` / `npm run build`: full
- `npm run dev:showcase` / `npm run build:showcase`: showcase
