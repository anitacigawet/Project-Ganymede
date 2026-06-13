---
name: feedback-zspan-reference-first
description: "When Ganymede needs infrastructure (auth, logging, notebook lifecycle, ops tooling), default to inspecting Z-SPAN's solved code at C:\\Users\\james\\Desktop\\ZSPAN_FINAL\\ZSPAN before reinventing. Read-only; port with adapted env-var naming."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b1fabc43-1fa7-4ec9-b300-429b7b733143
---

When Ganymede needs INFRASTRUCTURE (NotebookLM auth, ops tooling, logging discipline, anything operational rather than research-domain), the first move is read-only inspection of Z-SPAN's solved code at `C:\Users\james\Desktop\ZSPAN_FINAL\ZSPAN`. Default to porting their pattern rather than designing from scratch.

**Why:** James explicitly directed this 2026-05-31 after the recurring NotebookLM re-auth pain interrupted work: *"if you look at the different projects I have on my desktop and just make sure you only do read-only, you will see that they already have adjusted their notebook LM bridge with that capacity."* Z-SPAN solved many of Ganymede's operational problems earlier; Ganymede inherits, doesn't reinvent. The `auto_relogin` port in milestone 40 was the proof case: 30-min copy + adapt vs. 2-3 hours of designing from scratch, plus the design was battle-tested.

**How to apply:**

- Before writing new infrastructure code (auth flows, cookie handling, subprocess management, file-watching, logging discipline, background-task coordination), grep Z-SPAN for the equivalent pattern. Common locations:
  - `ZSPAN/02_Core_Project/notebooklm_bridge/` — NotebookLM-specific code
  - `ZSPAN/02_Core_Project/*/worker.py` — pre-flight + recovery patterns
  - `ZSPAN/agents/` — operational routines + safety reviews
- **Read-only on Z-SPAN.** Port into Ganymede; never edit Z-SPAN to "fix" something Ganymede needs.
- Adapt env-var naming (`ZSPAN_*` → `GANYMEDE_*`) and any project-specific assumptions (Python version, paths).
- Credit Z-SPAN's design in docstrings + commit messages — the cleverness belongs to its decision log (e.g., "D-035" for `auto_relogin`).
- Limits: this is for INFRASTRUCTURE, not research-domain code. Ganymede's 9D Engine work, Bicameral Convergence architecture, pathway design — those are Ganymede's own thinking. Z-SPAN doesn't have analogues.

**Concrete examples already in repo:**
- `app/services/notebooklm/auth_check.py` — entire module adapted from `ZSPAN/02_Core_Project/notebooklm_bridge/auth_check.py` (per the docstring at top), including `auto_relogin` ported in milestone 40.
- `app/services/notebooklm/` sub-package layout (client/cooldown/studio/research/auth_check siblings) — mirrors Z-SPAN's bridge layout (milestone 30).
