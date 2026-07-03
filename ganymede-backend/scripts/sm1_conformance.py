"""SM-1 conformance harness — fire real Sonnet strokes through
SonnetSubstrate and assert the orchestrator's five load-bearing parsers
extract structure from them (docs/concepts/Substrate_Migration.md § 3).

Parsers under test:
  1. parse_triage_hit_list      — <HIT_LIST_JSON> marker contract (REQUIRED:
                                  a miss silently degrades run_universal_loop)
  2. _count_bridges_in_audit    — "Bridge N (STRUCTURAL|IMPLIED)" shapes
  3. _parse_audit_findings      — Auditor's numbered fault categories
  4. _extract_final_resolution_section — FINAL RESOLUTION header
  5. _strip_trailing_cta        — persona's no-CTA rule (strip finds nothing)

Also records: per-stroke cost_usd + model_id (provenance fields), sphere
notice behavior on a packets-present stroke, and the cache-hit economics of
a repeated identical stroke (plan § 4 open question).

Run from ganymede-backend/:  ./venv_mac/bin/python scripts/sm1_conformance.py
Live cost: ~5 strokes, ~$1-1.5 of the included non-interactive cap.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.orchestrator import (  # noqa: E402
    TRIAGE_TEMPLATE_STRUCTURED,
    SYNTHESIS_TEMPLATE,
    AUDIT_TEMPLATE,
    BRIDGE_AUDIT_TEMPLATE,
    parse_triage_hit_list,
    _count_bridges_in_audit,
    _parse_audit_findings,
    _extract_final_resolution_section,
    _strip_trailing_cta,
)
from app.services.substrate import SonnetSubstrate  # noqa: E402

# A deliberately framework-internal toy scenario (no real-world entities →
# no harvest dependence; sphere check uses a packets-present synthesis).
SCENARIO = (
    "Two rival guilds compete to control a newly discovered trade route. "
    "Guild A has superior maps but slower ships. Guild B has faster ships "
    "but must hire A's cartographers to navigate. Neither can win alone."
)

PACKETS = {
    "Trade Route Survey": (
        "The route shortens transit by 40% [SRC-survey-01:a1b2c3]. "
        "Cartographer contracts include exclusivity clauses "
        "[SRC-guild-reg:d4e5f6]. Guild B's fleet is leased, not owned "
        "[SRC-port-ledger:g7h8i9]."
    ),
    "Guild Finances": (
        "Guild A carries no debt [SRC-ledger-A:j1k2l3]. Guild B's lease "
        "payments consume 60% of revenue [SRC-ledger-B:m4n5o6]."
    ),
}


def packets_block() -> str:
    parts = []
    for subject, packet in PACKETS.items():
        parts.append(f"--- TRUTH PACKET: {subject} ---")
        parts.append(packet)
        parts.append("")
    return "\n".join(parts).strip()


async def main() -> int:
    sub = SonnetSubstrate()
    results: list[tuple[str, bool, str]] = []
    total_cost = 0.0

    def record(name: str, ok: bool, detail: str, cost: float | None):
        nonlocal total_cost
        total_cost += cost or 0.0
        results.append((name, ok, detail))
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({detail}; "
              f"cost=${(cost or 0):.3f})")

    # ---- 1. Triage → parse_triage_hit_list -------------------------------
    triage_prompt = TRIAGE_TEMPLATE_STRUCTURED.format(
        scenario=SCENARIO, max_subjects=2
    )
    r = await sub.query_engine(triage_prompt)
    blueprint, subjects = parse_triage_hit_list(r.text)
    record(
        "parse_triage_hit_list",
        len(subjects) == 2 and all(s.get("surgical_prompt") for s in subjects),
        f"{len(subjects)} subjects parsed, model={r.model_id}",
        r.cost_usd,
    )

    # ---- 2. Synthesis (packets present) → FINAL RESOLUTION + notice ------
    synth_prompt = SYNTHESIS_TEMPLATE.format(
        scenario=SCENARIO, packets_block=packets_block()
    )
    r2 = await sub.query_engine(synth_prompt)
    r2 = SonnetSubstrate.check_sphere_notice(r2, packets_present=True)
    final_sec = _extract_final_resolution_section(r2.text)
    record(
        "_extract_final_resolution_section",
        len(final_sec) > 100,
        f"{len(final_sec)} chars extracted",
        r2.cost_usd,
    )
    record(
        "sphere_notice_present",
        not r2.sphere_notice_missing,
        "Notice: prefix found" if not r2.sphere_notice_missing
        else "MISSING Notice: prefix",
        None,
    )
    stripped, cta = _strip_trailing_cta(r2.text)
    record(
        "_strip_trailing_cta (no-CTA persona rule)",
        cta is None,
        "no trailing CTA" if cta is None else f"CTA leaked: {cta[:60]!r}",
        None,
    )

    # ---- 3. Auditor stroke → _parse_audit_findings ------------------------
    audit_prompt = AUDIT_TEMPLATE.format(
        scenario_context=SCENARIO, analysis_under_audit=r2.text[:4000]
    )
    r3 = await sub.query_auditor(audit_prompt)
    findings = _parse_audit_findings(r3.text)
    record(
        "_parse_audit_findings",
        findings is not None and len(findings) >= 1,
        f"{len(findings or [])} findings parsed",
        r3.cost_usd,
    )

    # ---- 4. Bridge stroke → _count_bridges_in_audit -----------------------
    # Notebook-era Bridges read Truth Packets as uploaded sources; on the
    # Sonnet side they must ride in the prompt (SM-2 wires this into the
    # orchestrator — here we compose it the same way SM-2 will).
    bridge_prompt = (
        "AUTHENTICATED TRUTH PACKETS (the substrate under audit):\n"
        + packets_block()
        + "\n\n"
        + BRIDGE_AUDIT_TEMPLATE.format(
            scenario_context=SCENARIO,
            analysis_under_audit=r2.text[:4000],
        )
    )
    r4 = await sub.query_bridge(bridge_prompt)
    n_bridges = _count_bridges_in_audit(r4.text)
    record(
        "_count_bridges_in_audit",
        n_bridges >= 0 and ("Bridge" in r4.text or "Total missed bridges" in r4.text),
        f"{n_bridges} STRUCTURAL/IMPLIED bridges counted",
        r4.cost_usd,
    )

    # ---- 5. Cache-hit economics: repeat stroke 1 verbatim ----------------
    t0 = time.time()
    r5 = await sub.query_engine(triage_prompt)
    cache_read = (r5.raw_usage or {}).get("cache_read_input_tokens", 0)
    cache_create = (r5.raw_usage or {}).get("cache_creation_input_tokens", 0)
    record(
        "cache_hit_on_repeat",
        cache_read > cache_create,
        f"read={cache_read} create={cache_create} "
        f"cost=${(r5.cost_usd or 0):.3f} vs first=${(r.cost_usd or 0):.3f} "
        f"({time.time()-t0:.0f}s)",
        r5.cost_usd,
    )

    # ---- Report -----------------------------------------------------------
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} checks passed; "
          f"total live cost ${total_cost:.2f} "
          f"(bills the included non-interactive cap)")
    report = {
        "passed": passed, "total": len(results),
        "total_cost_usd": round(total_cost, 4),
        "model_pin": sub.model,
        "checks": [
            {"name": n, "ok": ok, "detail": d} for n, ok, d in results
        ],
    }
    out = Path(__file__).parent / "sm1_conformance_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"report → {out}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
