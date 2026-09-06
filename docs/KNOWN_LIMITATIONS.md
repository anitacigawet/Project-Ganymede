# Known limitations

These are current implementation facts, not planned features.

- The orchestrator still uses notebook-shaped identifiers and extensive provider-era comments. The shipped `ClaudeRuntimeService` implements those calls with process-local records and Claude CLI invocations; no NotebookLM service is present.
- Process-local oracle and bridge handles do not survive a backend restart. Sessions and completed strokes can persist in SQLite, but temporary uploaded bridge context does not.
- The API accepts `research_mode` and request-level `deep_research_timeout`, but the current Claude runtime does not vary behavior from those values. `GANYMEDE_CLAUDE_TIMEOUT` controls each CLI invocation.
- `sources_imported` is a legacy response field. Its value is the count of unique URLs extracted from the returned Truth Packet, not a count of sources imported into a remote provider.
- Provider-era prompt budgets remain active and can truncate material before synthesis, audit, bridging, or translation. Their old comments are historical rationale, not verified Claude CLI limits. The supported tuning variables are listed in [CONFIGURATION.md](CONFIGURATION.md).
- Some internal comments point to old `docs/experiments`, `docs/learnings`, `docs/protocols`, or `docs/concepts` paths. Those directories are not part of this public source release; the canonical shipped documentation is linked from [START_HERE.md](../START_HERE.md).
- Automated regression tests use synthetic inputs and do not exercise an authenticated Claude end-to-end analysis.
