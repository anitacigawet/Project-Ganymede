/**
 * Deterministic showroom data for the hosted portfolio build.
 *
 * The normal application continues to use its real backend.  The showroom
 * build keeps the exact same UI and state transitions, but replaces the
 * external model/NotebookLM boundary with this fixed, fictional run.
 */

// The public repository is always the deterministic showroom edition. The
// private workshop retains the environment switch because it can also run
// against the real backend; this build never crosses that boundary.
export const GANYMEDE_DEMO_MODE = true;

export const GANYMEDE_DEMO_PROMPT =
  'A fictional two-person toolmaker has no advertising budget and faces a dominant incumbent. How could it reach a position where buyers choose it for a capability the incumbent cannot easily copy?';

export interface DemoDispatch {
  pathway: 'cleanroom' | 'genie' | 'offensive' | 'mirror_audit';
  confidence: number;
  scenario: {
    question?: string;
    current_state?: string;
    wished_for_state?: string;
    target?: string;
    objective_state?: string;
    prior_resolution?: string;
    dream_state?: boolean;
    extra_context?: string;
  };
  needs_external_knowledge: boolean;
  rationale: string;
  clarifying_questions: string[];
}

export interface DemoStroke {
  stroke_number: number;
  pathway: 'cleanroom' | 'genie' | 'offensive' | 'mirror_audit';
  raw_response: string;
  strategic_lasso?: string | null;
  incomprehensible_move?: string | null;
  final_resolution?: string | null;
  audit_findings?: string[] | null;
  audit_kind?: 'mirror_auditor' | 'bridge' | null;
  started_at: string;
  completed_at: string;
}

const STARTED = '2026-08-17T08:00:00.000Z';
const COMPLETED = '2026-08-17T08:00:03.000Z';

export function classifyDemoIntent(text: string): DemoDispatch {
  const normalized = text.toLowerCase();

  if (normalized.includes('audit') || normalized.includes('stress-test')) {
    return {
      pathway: 'mirror_audit',
      confidence: 0.96,
      scenario: { prior_resolution: text, extra_context: 'Fictional showroom input.' },
      needs_external_knowledge: false,
      rationale: 'You supplied an existing analysis and asked the system to test it for failure modes.',
      clarifying_questions: [],
    };
  }

  if (normalized.includes('will ') || normalized.includes('predict')) {
    return {
      pathway: 'cleanroom',
      confidence: 0.92,
      scenario: { question: text, extra_context: 'Fictional showroom input.' },
      needs_external_knowledge: false,
      rationale: 'The prompt asks for a falsifiable outcome, so the dispatcher selected the prediction pathway.',
      clarifying_questions: [],
    };
  }

  if (normalized.includes('target') || normalized.includes('outmaneuver')) {
    return {
      pathway: 'offensive',
      confidence: 0.9,
      scenario: {
        target: 'Fictional incumbent',
        objective_state: text,
        extra_context: 'Fictional showroom input.',
      },
      needs_external_knowledge: false,
      rationale: 'The prompt describes a target and an intended structural position, so the dispatcher selected strategy against a target.',
      clarifying_questions: [],
    };
  }

  return {
    pathway: 'genie',
    confidence: 0.94,
    scenario: {
      current_state:
        'A fictional two-person toolmaker has no advertising budget and competes with a dominant incumbent.',
      wished_for_state:
        'Buyers select the smaller company for a capability the incumbent cannot easily copy.',
      extra_context:
        'Synthetic showroom scenario. No people, companies, or live market claims are represented.',
    },
    needs_external_knowledge: false,
    rationale: 'The prompt describes a current position and a wished-for position, so the dispatcher selected pathfinding.',
    clarifying_questions: [],
  };
}

export const GANYMEDE_DEMO_STROKES: DemoStroke[] = [
  {
    stroke_number: 1,
    pathway: 'genie',
    raw_response:
      'THESIS — The smaller company should not compete for attention on the incumbent’s strongest dimension. Its useful opening is a narrow buyer problem that is expensive for the incumbent to acknowledge because solving it would disrupt the incumbent’s standard package.\n\nSTRATEGIC LASSO: Make the overlooked capability measurable inside one low-risk pilot. Each successful pilot raises the buyer’s expectation while making the incumbent’s generic offer look less complete.\n\nINCOMPREHENSIBLE MOVE: Publish the pilot method as a buyer-owned evaluation standard instead of guarding it as marketing language.',
    strategic_lasso:
      'Turn an overlooked capability into a buyer-owned evaluation standard.',
    incomprehensible_move:
      'Publish the method so the market, rather than the company, carries it forward.',
    started_at: STARTED,
    completed_at: COMPLETED,
  },
  {
    stroke_number: 2,
    pathway: 'mirror_audit',
    audit_kind: 'mirror_auditor',
    raw_response:
      'MIRROR AUDIT — The thesis assumes buyers will adopt a new evaluation standard merely because it is useful. That skips procurement friction, proof thresholds, and the possibility that the incumbent can imitate the visible feature. The claim needs a stronger reason the standard survives copying.',
    audit_findings: [
      'Adoption friction is underweighted.',
      'The visible feature may be copied.',
      'The pilot needs a defensible proof threshold.',
    ],
    started_at: STARTED,
    completed_at: COMPLETED,
  },
  {
    stroke_number: 3,
    pathway: 'mirror_audit',
    audit_kind: 'bridge',
    raw_response:
      'CONNECTION BRIDGE — The missed connection is between procurement safety and product defensibility. The lasting advantage is not the feature itself; it is the evidence format, migration path, and buyer training that make the new standard safe to adopt. Those pieces become more valuable with every pilot and are harder to copy than a feature checklist.',
    audit_findings: [
      'Procurement safety can become part of the product.',
      'Evidence format and migration support compound across pilots.',
    ],
    started_at: STARTED,
    completed_at: COMPLETED,
  },
  {
    stroke_number: 4,
    pathway: 'genie',
    raw_response:
      'FINAL SYNTHESIS — Begin with one narrow capability whose value can be demonstrated in a reversible pilot. Package the result as a buyer-owned evaluation kit: a test, an evidence format, a migration checklist, and a training session. The company’s advantage is the complete adoption path, not a claim that its feature is unique.\n\nThe sequence is: recruit one design partner; agree on the proof threshold before the pilot; publish the buyer’s evaluation kit; repeat with two adjacent buyers; then let procurement teams ask the incumbent to meet the new standard. This redirects competition from advertising reach to accumulated adoption evidence.',
    final_resolution:
      'Compete on the complete adoption path: reversible proof, buyer-owned evidence, migration support, and training.',
    started_at: STARTED,
    completed_at: COMPLETED,
  },
];

export const waitForDemoBeat = (milliseconds: number) =>
  new Promise<void>((resolve) => window.setTimeout(resolve, milliseconds));
