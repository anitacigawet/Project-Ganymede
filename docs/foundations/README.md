# Foundation corpus

These Markdown documents are the runtime grounding corpus for Project Ganymede's analytical engine. `ganymede-backend/app/services/substrate.py` loads every `.md` file in this directory except this README, in sorted filename order, and attaches the combined corpus to engine, auditor, and bridge system prompts.

The files are an upstream snapshot of the 9D framework material that Project Ganymede operationalizes. They are kept in source form so a normal clone can reproduce the local analytical substrate without a remote notebook or private document store.

Use `GANYMEDE_CORPUS_FILES` to select a comma-separated subset by filename, or `GANYMEDE_FOUNDATIONS_DIR` to point the runtime at another corpus directory. Do not casually edit the bundled files: changes alter the grounding shared by every analytical stroke.
