# Experiment 01 — Hualapai Water Crisis

**Status:** ✅ Complete. Validated the full pipeline end-to-end.
**Significance:** First successful run. The GSS schema and the 3D engine were both crystallized through this experiment.

## Scenario

A new semiconductor plant proposes to draw 400,000 GPD from the Hualapai Valley Basin in Arizona. The basin is depleting at 2.4 ft/year. Pending bill HB-2041 would impose a 15% pumping restriction. Established agricultural users are already drawing on the basin.

## Pipeline trace

### Phase 0 — Oracle initialization
A temporary PKI notebook was created with the standard persona lock (zero hallucination, mandatory hash citations, no fluff). See [`../protocols/PKI_Oracle_Persona.md`](../protocols/PKI_Oracle_Persona.md).

### Phase 1 — Factual Harvest
A baseline scenario document with the four key facts (depletion rate, plant draw rate, bill mitigation coefficient, agricultural pressure) was uploaded. The Umpire was asked for both the 9D analysis and a specific 3D visualization strategy.

The Truth Packet identified:
- **Primary Gravity Well:** unsustainable groundwater depletion (2.4 ft/yr) → inescapable resource constraint for all actors.
- **Failure Vector:** intersection of new industrial demand and HB-2041 enforcement.
- **Active Dimensions:** Economic vs. Environmental, Legislative vs. Operational, Industrial vs. Agricultural, plus the long-term Sustainability dimension.

The Umpire's visualization strategy specified the steep central funnel, the high-luminosity central singularity for the semiconductor sink, the peripheral ag clusters being pulled toward the singularity, the translucent legislative ceiling, and the topological-tear failure mode at the point where industrial suction overwhelms the ceiling.

### Phase 2 — Pro-Tier Synthesis
First attempt: the Visual Packet prompt asked Gemini for `{stress, blindness, description}`. Gemini over-interpreted and produced a standalone HTML Three.js page instead of JSON — the "Creative Leak."

Second attempt with a "format reprimand" prompt yielded a richer "JSON state object" instead of just keys. This drove the schema upgrade.

Third attempt produced the now-canonical **Ganymede Strategic Schema (GSS)** — a multi-layered JSON blueprint with `metadata`, `environmental_baseline`, `legislative_framework`, `topological_entities[]`, `physics_logic`, plus the LaTeX-defined D_n governing equation.

### Phase 3 — Universal Receiver
The frontend was upgraded from a sliders-only visualizer into a GSS-compliant engine: dynamic node spawning, the D_n inverted-radial-decay deformation, fracture state, holographic legislative plane, and live override sliders for `drawRate` and `mitigation` so the human can stress-test the Umpire's model.

The final paste of the Hualapai GSS object into the Cortex Clipboard rendered correctly: central singularity warping the mesh, ag clusters sinking, legislative ceiling pulsing, fracture triggering when industrial suction was driven toward 1.5M+ GPD with mitigation at zero.

## Canonical Hualapai Truth Packet (sample GSS)

```json
{
  "metadata": {
    "compiler_version": "G-3.0-Flash",
    "classification": "STRATEGIC_SITREP",
    "timestamp": "2026-05-04T02:31:00Z"
  },
  "environmental_baseline": { "ambient_depletion": 2.4, "unit": "ft/yr" },
  "legislative_framework": {
    "bill_id": "HB-2041",
    "mitigation_coefficient": 0.15,
    "status": "Active"
  },
  "topological_entities": [
    {
      "node_id": "Semiconductor_Alpha",
      "type": "Industrial_Sink",
      "draw_rate": 400000,
      "luminosity": 0.95,
      "coordinates": { "x": 0, "y": -5.2, "z": 0 }
    },
    {
      "node_id": "Ag_Cluster_West",
      "type": "Agricultural_Peripheral",
      "draw_rate": 120000,
      "luminosity": 0.3,
      "coordinates": { "x": 8.5, "y": -1.1, "z": 4.2 }
    }
  ],
  "physics_logic": {
    "gravity_well_depth_formula": "Inverted_Radial_Decay",
    "failure_threshold": -4.5
  }
}
```

## Lessons captured

- The Umpire produces better Visual Packets when it dictates the visualization strategy itself, instead of letting Gemini guess. Phase 1 now explicitly requests both the 9D analysis and the 3D modeling instructions.
- A simple `{stress, blindness}` payload is too low-resolution. The state-object approach (full topological entities + physics logic) is what allowed the engine to render scenario-specific topologies rather than generic warps.
- A "format reprimand" prompt is sometimes necessary when Gemini overshoots into building standalone UI. Reminding it that the Ganymede frontend handles rendering keeps it in compiler mode.

## Source artifacts

- [`scripts/hualapai_harvest.py`](scripts/hualapai_harvest.py)
- `ganymede-backend/test_swarm_logic.py`
- `ganymede-backend/test_compiler.py`
- `ganymede-ui/src/types/ganymede.ts` (the schema)
- `ganymede-ui/src/components/GravityWell.tsx` (the D_n implementation)
