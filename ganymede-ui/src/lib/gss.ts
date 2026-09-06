import type { GSSState } from '../types/ganymede';

const record = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);
const finite = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value);
const text = (value: unknown): value is string => typeof value === 'string';

/** Validate every nested field before clipboard data reaches React or WebGL. */
export function isGSSState(value: unknown): value is GSSState {
  if (!record(value)) return false;
  const { metadata, environmental_baseline: baseline, legislative_framework: law,
    topological_entities: entities, physics_logic: physics } = value;
  if (!record(metadata) || !text(metadata.compiler_version) || !text(metadata.classification) || !text(metadata.timestamp)) return false;
  if (!record(baseline) || !finite(baseline.ambient_depletion) || !text(baseline.unit) ||
    (baseline.recharge_rate !== undefined && !finite(baseline.recharge_rate))) return false;
  if (!record(law) || !text(law.bill_id) || !finite(law.mitigation_coefficient) ||
    !['Active', 'Pending', 'Contested'].includes(law.status as string)) return false;
  if (!record(physics) || !text(physics.gravity_well_depth_formula) || !finite(physics.failure_threshold)) return false;
  if (!Array.isArray(entities)) return false;
  return entities.every((entity: unknown) => {
    if (!record(entity) || !text(entity.node_id) || !finite(entity.draw_rate) || !finite(entity.luminosity) ||
      !['Industrial_Sink', 'Agricultural_Peripheral', 'Monitoring_Well'].includes(entity.type as string)) return false;
    const coordinates = entity.coordinates;
    return record(coordinates) && finite(coordinates.x) && finite(coordinates.y) && finite(coordinates.z);
  });
}
