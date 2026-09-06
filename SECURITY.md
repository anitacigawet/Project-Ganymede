# Security

The full local edition can invoke the authenticated Claude Code CLI and use its built-in WebSearch tool. Run it only on a machine and account you control.

- The supplied launcher binds the API and UI to `127.0.0.1` by default.
- LAN binding is opt-in. Add only trusted origins to `GANYMEDE_CORS_ORIGINS`.
- Analytical calls have all tools disabled.
- Research calls allow only `WebSearch`; MCP configuration is forced empty.
- The repository does not need or accept NotebookLM credentials.
- Do not commit `.env`, `ganymede-backend/data`, logs, session databases, Claude authentication state, or generated output.

Treat scenarios and harvested pages as untrusted input. Review source links before acting on an analysis.

Report vulnerabilities privately through GitHub Security Advisories. Include the affected file, reproduction steps, and likely impact; do not post credentials or private scenarios in the report.
