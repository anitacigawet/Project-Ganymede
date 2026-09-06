# Project Ganymede continuation rules

Read [START_HERE.md](START_HERE.md) before changing this repository.

- Scope is this repository only. Job Matrix and sibling portfolio projects are out of scope unless James explicitly says otherwise.
- Preserve both editions: the full local FastAPI/Next.js application and the deterministic static showcase.
- Do not restore NotebookLM, browser automation, or remote notebook operations. The remaining notebook-shaped identifiers are a compatibility seam implemented by the local Claude runtime.
- Analytical, audit, bridge, and translation calls must keep all tools disabled. Research may use only Claude Code's `WebSearch`; MCP configuration stays empty.
- Treat `docs/foundations/` as runtime input. Read its README before changing the corpus.
- Do not inspect or commit ignored runtime state, especially `ganymede-backend/data/`, unless James explicitly asks. It may contain prior local scenarios.
- Do not commit generated dependencies, environments, builds, logs, caches, databases, sessions, or credentials.
- Preserve unrelated working-tree changes. Begin with `git status --short --branch` and `git diff --check`.
- Verify backend compilation/tests and both frontend builds before reporting code changes complete.
- Do not commit, push, merge, deploy, release, or publish unless James directly requests that action.
