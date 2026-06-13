---
name: feedback-autonomous-push
description: "For Ganymede specifically: routine git push to origin/master is autonomous, not operator-gated. Don't ask before pushing finished local commits on this project."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 79235d12-d2da-4b75-8e23-aaf91ebd9263
---

**Scope: Ganymede only.** Do NOT generalize this rule to other projects of James's. He explicitly flagged 2026-06-01 that the cross-project framing was wrong — this is a per-project permission, not an account-wide preference.

**The rule:** on Ganymede, after committing finished work, just `git push` to `origin/master`. No prompt, no AskUserQuestion, no "shall I push" sentence in the stop report. Push and report what landed.

**Why:** James explicitly directed this 2026-06-01: *"When you say push, do you mean the automatic push to save our work to the Github? If so, then that's not something that you need to ask me for. That's something that we should just be doing automatically no question."* He was responding to my stop-report that left the push for him to do — that's the friction he doesn't want, in this project. For any other project of his, default back to ask-first on push until he says otherwise for that project specifically.

**How to apply (Ganymede only):**
- After every autonomous commit, push.
- Force-push, deleting branches, rewriting already-pushed history — STILL stop-and-ask even on Ganymede. The relaxation is specifically for routine save-to-GitHub.
- The per-project CLAUDE.md already encodes this rule directly in the autonomy table. Memory is the cross-session backup so future-Claude inherits the directive even if CLAUDE.md drifts.

**Connection to other rules:**
- See [[project_autopilot_protocol]] — the Autopilot Protocol's framing of push as operator-cadence is overridden by this Ganymede-specific directive.
