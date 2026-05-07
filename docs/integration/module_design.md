# Ganymede Module — Architecture & Design Decisions

**Status:** Built and shipped. The v2 API is live in `ganymede-backend/app/v2_routes.py`. PrisonBreak is the first concrete consumer (see [`examples/prisonbreak_consumer.md`](examples/prisonbreak_consumer.md)).

This doc explains *why* the integration surface looks the way it does. If you're building a consumer, start with [`consuming_the_v2_api.md`](consuming_the_v2_api.md) — that's the hands-on guide. This doc is the architectural commentary.

## The headline shape — open primitive, not opinionated wrapper

Ganymede is designed as an **open primitive**, not a per-domain SDK. The v2 API exposes raw access to the strategic-physics framework: any consumer composes its own scenarios, picks its pathway, ships its own pre-harvested Truth Packets, and decides its own UI (or no UI).

This is deliberate. Each consuming project knows its domain better than Ganymede possibly could. PrisonBreak knows what a "case" is and how to map case errors into Truth Packets; a Polymarket validator knows what a market's resolution criteria look like and how to harvest the underlying real-world question. Ganymede doesn't try to anticipate either. It hands the consumer a clean API and gets out of the way.

```
                     ┌─────────────────────────────┐
                     │ 9D Chess Engine (NotebookLM)│
                     │ Mirror Auditor   (NotebookLM)│
                     └───────────────┬─────────────┘
                                     │
                            cooldown gate
                                     │
                     ┌───────────────▼─────────────┐
                     │  GanymedeOrchestrator       │
                     │  (Python, single instance)  │
                     └───────────────┬─────────────┘
                                     │
                     ┌───────────────▼─────────────┐
                     │  v2 API (FastAPI)           │
                     │  /api/v2/sessions/...       │
                     │  WS /events/stream          │
                     └─────┬───────────────────┬───┘
                           │                   │
            ┌──────────────┘                   └────────────┐
            │                                               │
            ▼                                               ▼
    PrisonBreak's                              Polymarket-Validator's
    SimulatePanel                              market-runner CLI
    (genie pathway,                            (cleanroom pathway,
     case → packets,                            market → packets,
     React UI)                                  no UI, scored runs)
            ▲                                               ▲
            │                                               │
   each consumer owns its own scenario shape, packet construction, and presentation
```

Consumers can also optionally build *opinionated wrappers* on top of the open API for their own users — PrisonBreak ships one, where clicking "War-Game This Case" runs a fixed scenario with case errors mapped to packets. That's a preset built *on the open primitive*, not a replacement for it.

## What a consumer needs from Ganymede

Every consumer, regardless of domain, needs the same set of capabilities:

1. **Send a scenario.** Any of the four scenario shapes (Cleanroom question, Genie current/wished, Offensive target/objective, Mirror Audit prior_resolution) plus optional pre-existing context.
2. **Receive a session handle.** Track the run, subscribe to updates, drive strokes against it.
3. **Receive structured progress.** Stroke-by-stroke output; per-stroke synthesis results. Strongly typed, not free-text.
4. **Drive the strokes.** Single-pass synthesis or full Iterative Engine multi-stroke loop. Optionally drill into individual primitives (synthesize, audit) if needed.
5. **Receive a final structured resolution.** Strategic Lasso, Incomprehensible Move, Resolution text, plus per-stroke history if Iterative Engine was used.

The v2 API maps cleanly to these:

| Need | Endpoint |
| --- | --- |
| Send a scenario, get a session handle | `POST /api/v2/sessions` |
| Receive structured progress | `GET /api/v2/sessions/{id}/events` (poll) or `WS /api/v2/sessions/{id}/events/stream` (push) |
| Drive strokes (single-pass) | `POST /api/v2/sessions/{id}/synthesize` |
| Drive strokes (full iterative loop) | `POST /api/v2/sessions/{id}/iterate` |
| Receive a final structured resolution | `POST /api/v2/sessions/{id}/complete` |

See [`consuming_the_v2_api.md`](consuming_the_v2_api.md) for the request/response shapes, code examples, and operational guarantees.

## Why HTTP, not direct Python import

Ganymede is Python (FastAPI + Pydantic v2 + the `notebooklm-py` wrapper). One reasonable design would have been to expose `GanymedeOrchestrator` as a Python library that consumers import directly. The v2 API was chosen instead, for three reasons:

1. **Most consumers aren't Python.** PrisonBreak is TypeScript; Polymarket-Validator could be anything. An HTTP boundary lets consumers be in their native stack.
2. **Process isolation for the cooldown gate.** The gate is process-global. If consumers imported Ganymede directly, every consumer would have its own gate instance and the discipline would fragment. With one Ganymede process serving all consumers, the gate stays canonical.
3. **NotebookLM session is single-tenant.** One Playwright browser, one set of session cookies, one auth flow. A separate process is the natural place for that singleton.

Direct Python import is technically possible — `GanymedeOrchestrator` is public — but not recommended. The v2 API is the supported integration shape.

## The four pathways

The four pathways (`cleanroom`, `genie`, `offensive`, `mirror_audit`) all run through the same code path. The pathway value selects a prompt template at synthesis time; nothing else differs at the engine level. Adding a fifth pathway is a single-file change (a new template + a new enum value).

| Pathway | Confirmed runs |
| --- | --- |
| `cleanroom` | Powell (blind-validated), Tokenized Land, Musk-Altman |
| `genie` | Giant-Slayer |
| `offensive` | None yet — same code path as `genie` |
| `mirror_audit` | Used internally by `/iterate` (Stroke 2); Amnesia validation |

If a consumer needs a domain-specific framing that doesn't fit any of the four, they can either (a) pass a `framing` override to `/synthesize` to fully replace the prompt template for that one call, or (b) propose adding a new pathway. Most consumers don't need either — `cleanroom` and `genie` cover the prediction and pathfinding cases that nearly every strategic question maps to.

## What's built vs. what's deferred

### Built and shipped (v1)

- Session abstraction with status tracking, event timeline, in-memory subscriber queues
- HTTP API for create/state/synthesize/iterate/complete/events
- WebSocket event stream with replay-on-connect + live push
- Iterative Engine (Stroke 1 → Mirror Auditor → Stroke 3) as a single `/iterate` call
- Pre-harvested Truth Packet path (consumers ship their own findings, no Oracle creation)
- Cooldown gate enforcing 8s API floor + 60s session floor + 20/hr + 100/day caps
- Pathway selection (`cleanroom` / `genie` / `offensive` / `mirror_audit`) driving prompt template
- All four scenario shapes with Pydantic v2 contracts and JSON Schema export

### Deliberately deferred (v1.5+)

- **Oracle creation through the API.** The orchestrator can spin up persona-locked PKI Oracle notebooks on demand, but the v2 surface doesn't expose this — consumers ship pre-harvested Truth Packets instead. Reasons: (a) the Oracle creation path requires a manual UI Import click in the NotebookLM web app per Oracle, which defeats automation; (b) every consumer that's been targeted so far already has its own grounded RAG layer (PrisonBreak has NotebookLM, future consumers will likely have similar); (c) the event-stream types `oracle_request`, `oracle_created`, `oracle_harvested` are reserved so the Oracle flow can land in v1.5 without a breaking change.
- **Persistence.** Sessions are in-memory. A backend restart loses session state. Consumers persist their own `(consumer_id, ganymede_session_id)` mappings if they need durability. Persistence inside Ganymede would create cross-consumer shared state and complicate the single-tenant model.
- **Authentication.** None. The backend listens on `127.0.0.1` and trusts every caller. Don't bind to `0.0.0.0` without an auth proxy.
- **Multi-tenancy.** Out of scope. One Ganymede process, one NotebookLM session, one Engine notebook. Consumers needing parallelism run separate Ganymede instances on separate ports — not currently a supported configuration.

## The Import-click problem (resolved by skipping it)

Earlier design notes flagged the Import-click problem: every PKI Oracle's Deep Research output requires a manual UI click in the NotebookLM web app before the result can be queried programmatically. The `notebooklm-py` wrapper does not expose a programmatic Import.

This was a major friction point for any consumer wanting full Oracle creation. The v1 solution is to skip Oracle creation entirely — consumers ship pre-harvested Truth Packets via `/synthesize` or `/iterate`. PrisonBreak does this; Polymarket-Validator will too. The Import-click problem becomes something the consumer's own RAG layer handles in its own way (or doesn't have, if the consumer uses something other than NotebookLM as its retrieval substrate).

If a future consumer genuinely needs Ganymede to drive Oracle creation, the path forward is browser automation via Playwright (already a dep through `notebooklm-py`) — but that's a v1.5+ decision, not a v1 problem.

## How Ganymede deploys

The supported deployment is one HTTP service per consumer environment, on `localhost:8000`:

```powershell
cd ganymede-backend
.\venv_312\Scripts\activate
$env:PYTHONPATH = "."
uvicorn app.main:app --port 8000
```

Consumer applications discover Ganymede via the `GANYMEDE_BASE_URL` env var (defaults to `http://127.0.0.1:8000`).

For development without burning NotebookLM quota, `ganymede-backend/start_mocked.py` boots the same API with the engine calls patched to return canned responses. Consumers can iterate end-to-end against the mocked backend without needing live NotebookLM auth.

## Why the open-primitive shape is the right call

A few principles fall out of having shipped the integration twice (once in concept, once for real with PrisonBreak) that should generalize:

- **Consumer domain knowledge is irreplaceable.** PrisonBreak knows that "EM Finding (severity 4)" is a TruthPacket subject worth keeping intact; Ganymede couldn't have guessed that. The right boundary is "consumer constructs the packets, Ganymede synthesizes."
- **Pre-harvested Truth Packets are the *common* integration shape, not the exotic one.** Any consumer that already has its own document-grounded retrieval will not want Ganymede creating fresh notebooks for it. The "synthesize-from-pre-harvested" path being a first-class API endpoint (rather than an edge case bolted onto an Oracle-creation flow) is the load-bearing decision.
- **Pathway selection is a prompt-template selector, not architectural.** Cleanroom / Genie / Offensive / Mirror_Audit share 99% of the code. Treating them as a runtime enum that picks the framing keeps the surface small.
- **WebSocket streaming is the right transport for multi-stroke runs.** Each stroke takes minutes; a 10-minute "loading…" with no signal is unacceptable. WS subscribers see strokes as they land.
- **Cooldown discipline must be the backend's problem, not the consumer's.** Asking each consumer to implement the 8s gate would fragment it. Putting it in `_CooldownGate` at the lowest layer of the orchestrator means consumers get correct behavior for free.

## Open questions

These are not blockers but are worth thinking about before the next consumer:

1. **Multi-consumer concurrency.** A single Ganymede process serializes all NotebookLM calls. If two consumers fire `/iterate` simultaneously, the second one waits ~24s+ behind the first. Acceptable for v1; might want fairness scheduling in v1.5 if multi-consumer usage gets dense.
2. **Authentication.** Currently relies on the localhost binding. Any deployment that crosses a network boundary will need a token or a reverse proxy.
3. **Run history.** Sessions are in-memory; once `/complete` returns, the only durable record is whatever the consumer wrote down. A future "GET /api/v2/runs" that returns a history of recent FinalResolutions could be useful for operators auditing the engine across consumers, but adds the persistence concern.
4. **Mirror Validation as a fully standalone pathway.** Currently `mirror_audit` works for one-off audits (you pass `prior_resolution` in the Scenario), and `/iterate` drives Stroke 2 internally. There's no surface for "run a full Mirror Validation pathway with N audit cycles" — if the project's Mirror Validation methodology grows beyond a single audit step, the API needs an extension.
5. **The `framing` override on `/synthesize`.** Lets a consumer fully replace the synthesis prompt for one call. Powerful but invites prompt-engineering drift if consumers start writing their own templates rather than picking from the four pathways. Should this be locked down per-consumer, or trust consumers to use it judiciously? Currently trust-based.

## Reading order if you're new to this folder

1. [`consuming_the_v2_api.md`](consuming_the_v2_api.md) — hands-on consumer guide. Probably 80% of what you need.
2. This doc — the *why* behind the API shape.
3. [`examples/prisonbreak_consumer.md`](examples/prisonbreak_consumer.md) — concrete reference consumer.
4. [`../OVERVIEW.md`](../OVERVIEW.md) — broader project context if you want to understand the framework being exposed.
