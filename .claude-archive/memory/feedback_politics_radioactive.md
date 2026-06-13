---
name: feedback-politics-radioactive
description: "For Ganymede scenario selection, exclude political/electoral/geopolitical/regulatory-politics/partisan questions; treat Polymarket (and similar prediction-market platforms) as themselves potentially adversarial-information vectors on political topics"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 386f8d34-e567-483b-a206-2a050a6f06bf
---

Treat political topics as radioactive when picking scenarios for Project Ganymede validation runs. Exclude electoral, regulatory-politics, geopolitical, partisan, and foreign-policy questions categorically.

**Why:** James's stated view (2026-05-25, during Polymarket browse for the first live Dispatcher spin): *"anything political [is] radioactive, as the information sphere, public domain with anything related to that, including the betting platforms like polymarket themselves, are filled with or become components of psyops and other covert activity's."* Two compounding concerns: (1) political topics are precisely where coordinated information-sphere manipulation is most active, so the substrate the Engine would reason over may itself be adversarially poisoned, and (2) prediction-market prices on political questions are exactly the kind of resolution mechanism adversarial actors push, so even the "blind validation" baseline against market price is suspect.

**How to apply:** When picking scenarios for Engine validation runs (Cleanroom, Genie, Offensive Architect, Mirror Audit — all pathways), exclude political/electoral/geopolitical/regulatory-politics/partisan questions as a hard filter, not a soft preference. Lean toward: corporate strategic decisions, technological milestones (release dates, capability claims, model performance), scientific outcomes, sports championship-race dynamics, bounded-industry investigations, infrastructure/operational events. The shared property of preferred domains is that adversarial pressure on the resolution mechanism is weaker — fewer well-funded actors with strong incentive to push the price.

Important caveat: this applies to scenario *selection*, not to general project work. Historical geopolitical examples in framework documentation, references to past validated runs that happened to be political (e.g., Powell), and discussion of geopolitical primitives in concept docs are fine — they're already on disk and don't introduce new manipulation surface. The rule is forward-looking: don't pick new political scenarios as test substrates.

Related: [[project_dispatcher_frontend]] (this constraint shapes what the Dispatcher should be tested against in the first live spin and going forward).
