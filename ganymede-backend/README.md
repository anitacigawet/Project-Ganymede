# Project Ganymede backend

FastAPI provides session creation, multi-stroke orchestration, persistent local history, WebSocket progress, and the Claude CLI process boundary.

Start it from the repository root after running the setup script:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir ganymede-backend --host 127.0.0.1 --port 8000
```

The OpenAPI page is available at `http://127.0.0.1:8000/docs`.

The backend uses the existing Claude Code login. Analytical calls have no tools. Research harvest calls allow only `WebSearch`. Local session state and generated prompt-cache files are written below `ganymede-backend/data/`, which is ignored by Git.

Configuration is documented in [`../docs/CONFIGURATION.md`](../docs/CONFIGURATION.md); architecture and process permissions are documented in [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).
