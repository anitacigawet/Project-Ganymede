"""Powell-sound Bridge null test (P1-02).

Feeds the Connection Bridge the EXACT same substrate as the canonical
Powell Cleanroom run (4 Truth Packets) and the Powell Engine Resolution
as the audit target. Classifies the Bridge output:

  - "0 missed bridges"           - Bridge correctly recognised substrate
                                   was fully utilised (null result on sound)
  - "valid catches"              - Bridge surfaced connections the
                                   canonical run genuinely missed
  - "over-produced speculative"  - Bridge invented speculative bridges
                                   despite the substrate being well-used

Reads the Truth Packets + Engine Resolution from the canonical run
record under docs/experiments/runs/Powell_Cleanroom/ so the test stays
in sync with the source of truth.

Run with:
    cd ganymede-backend
    .\\venv_312\\Scripts\\python.exe ..\\scripts\\powell_bridge_null_test.py
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "docs" / "experiments" / "runs" / "Powell_Cleanroom"
ARTIFACT_DIR = ROOT / "docs" / "experiments" / "runs" / "Powell_Bridge_Null_Test_Artifacts"


def extract_truth_packets() -> list[dict[str, str]]:
    """Parse the 4 Truth Packets from 03_Truth_Packets.md.

    Each packet is inside a triple-backtick fenced block under a
    `## Silo D... ` heading. Header line of each fenced block reads
    `TRUTH PACKET: <name>`.
    """
    text = (RUN_DIR / "03_Truth_Packets.md").read_text(encoding="utf-8")
    # Match: ## Silo <something> <title>\n\n```<lang or empty>\n<body>\n```
    pattern = re.compile(
        r"## (Silo [^\n]+)\n+```\w*\n(TRUTH PACKET:[^\n]*\n.+?)\n```",
        re.DOTALL,
    )
    packets: list[dict[str, str]] = []
    for match in pattern.finditer(text):
        silo_header = match.group(1).strip()
        body = match.group(2).strip()
        # Extract the TRUTH PACKET: <title> line as the subject
        first_line = body.split("\n", 1)[0].replace("TRUTH PACKET:", "").strip()
        subject = f"Powell - {first_line} ({silo_header})"
        packets.append({
            "subject": subject[:200],
            "content": body,
            "source_label": "Powell Cleanroom canonical Truth Packet",
        })
    if len(packets) != 4:
        raise RuntimeError(
            f"Expected 4 truth packets, parsed {len(packets)}. "
            f"Check the run record's fenced-block structure."
        )
    return packets


def extract_engine_resolution() -> str:
    """Extract the verbatim Engine Resolution from 05_Engine_Resolution.md.

    The resolution lives inside a blockquote (lines starting with `> `)
    in the "Verbatim Engine output" section. Strip the leading `> `.
    """
    text = (RUN_DIR / "05_Engine_Resolution.md").read_text(encoding="utf-8")
    # Find the "Verbatim Engine output" section
    start = text.find("## Verbatim Engine output")
    if start == -1:
        raise RuntimeError("Verbatim Engine output section not found")
    # Everything until the next ## section
    next_header = text.find("\n## ", start + 1)
    section = text[start:next_header] if next_header > -1 else text[start:]
    # Extract blockquote lines
    lines: list[str] = []
    for line in section.splitlines():
        if line.startswith("> "):
            lines.append(line[2:])
        elif line.strip() == ">":
            lines.append("")
    resolution = "\n".join(lines).strip()
    if "Convergence Theorem" not in resolution or "Final Resolution" not in resolution:
        raise RuntimeError(
            "Resolution extraction looks malformed - missing expected markers. "
            "Check the blockquote structure of 05_Engine_Resolution.md."
        )
    return resolution


def main() -> None:
    print("Step 0: parsing canonical Powell artifacts from run record...")
    truth_packets = extract_truth_packets()
    resolution = extract_engine_resolution()
    print(f"  Truth packets parsed: {len(truth_packets)}")
    for p in truth_packets:
        print(f"    - {p['subject']} ({len(p['content'])} chars)")
    print(f"  Engine resolution: {len(resolution)} chars")

    client = httpx.Client(base_url=BASE, timeout=300.0)

    # ── 1. Create session ──
    print("\nStep 1: creating Cleanroom session...")
    session_resp = client.post(
        "/api/v2/sessions",
        json={
            "scenario": {
                "question": "Will jerome powell actually get fired",
                "dream_state": True,
            },
            "pathway": "cleanroom",
            "iterative": False,
            "max_strokes": 1,
        },
    )
    session_resp.raise_for_status()
    session_id = session_resp.json()["session_id"]
    print(f"  Session: {session_id}")

    # ── 2. Provision Bridge ──
    print("\nStep 2: provisioning Bridge notebook (~3-5 min)...")
    provision_resp = client.post(
        "/api/v2/bridge/provision",
        json={
            "title": "Bridge - Powell sound-input null test",
            "truth_packets": truth_packets,
            "include_foundations": True,
        },
    )
    provision_resp.raise_for_status()
    task_id = provision_resp.json()["task_id"]
    print(f"  Task: {task_id}")

    provision_start = time.time()
    bridge_notebook_id: str | None = None
    while True:
        time.sleep(15)
        task_state = client.get(f"/api/v2/tasks/{task_id}").json()
        elapsed = int(time.time() - provision_start)
        print(f"  +{elapsed}s status={task_state['status']}")
        if task_state["status"] == "completed":
            bridge_notebook_id = task_state["result"]["notebook_id"]
            print(
                f"  Provisioned: notebook={bridge_notebook_id} "
                f"foundations={task_state['result']['foundations_uploaded']} "
                f"packets={task_state['result']['truth_packets_uploaded']}"
            )
            break
        if task_state["status"] == "error":
            print(f"  PROVISIONING FAILED: {task_state.get('error_message')}")
            sys.exit(1)
        if elapsed > 600:
            print("  TIMEOUT after 10 min")
            sys.exit(1)

    # ── 3. Bridge audit ──
    print("\nStep 3: firing /bridge-audit with Powell Engine Resolution...")
    audit_start = time.time()
    audit_resp = client.post(
        f"/api/v2/sessions/{session_id}/bridge-audit",
        json={
            "bridge_notebook_id": bridge_notebook_id,
            "target_text": resolution,
            "scenario_context": "Will jerome powell actually get fired",
        },
    )
    audit_resp.raise_for_status()
    audit_elapsed = round(time.time() - audit_start, 1)
    audit_data = audit_resp.json()
    raw = audit_data["stroke"]["raw_response"]
    print(f"  Audit completed in {audit_elapsed}s, {len(raw)} chars")

    print("\n" + "=" * 60)
    print("BRIDGE OUTPUT (verbatim)")
    print("=" * 60)
    print(raw)
    print("=" * 60)

    # ── 4. Persist artifacts ──
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / "bridge_output.txt").write_text(raw, encoding="utf-8")
    metadata: dict[str, Any] = {
        "session_id": session_id,
        "bridge_notebook_id": bridge_notebook_id,
        "provision_seconds": round(time.time() - provision_start - audit_elapsed, 1),
        "audit_seconds": audit_elapsed,
        "response_chars": len(raw),
        "stroke": audit_data["stroke"],
        "scenario_question": "Will jerome powell actually get fired",
        "truth_packet_subjects": [p["subject"] for p in truth_packets],
        "engine_resolution_chars": len(resolution),
    }
    (ARTIFACT_DIR / "metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\nArtifacts: {ARTIFACT_DIR}")
    print(f"Bridge notebook ID (for cleanup later): {bridge_notebook_id}")


if __name__ == "__main__":
    main()
