export interface GSSMetadata {
  compiler_version: string;
  classification: string;
  timestamp: string;
}

export interface GSSEnvironmentalBaseline {
  ambient_depletion: number;
  recharge_rate?: number;
  unit: string;
}

export interface GSSLegislativeFramework {
  bill_id: string;
  mitigation_coefficient: number;
  status: 'Active' | 'Pending' | 'Contested';
}

export interface GSSTopologicalEntity {
  node_id: string;
  type: 'Industrial_Sink' | 'Agricultural_Peripheral' | 'Monitoring_Well';
  draw_rate: number;
  luminosity: number;
  coordinates: {
    x: number;
    y: number;
    z: number;
  };
}

export interface GSSPhysicsLogic {
  gravity_well_depth_formula: string;
  failure_threshold: number;
}

export interface GSSState {
  metadata: GSSMetadata;
  environmental_baseline: GSSEnvironmentalBaseline;
  legislative_framework: GSSLegislativeFramework;
  topological_entities: GSSTopologicalEntity[];
  physics_logic: GSSPhysicsLogic;
}
