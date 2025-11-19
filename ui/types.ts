export type EvidenceLink = {
  claim_id: string;
  paper_id: string;
  role: "support" | "contest" | "context";
  weight: number;
  claim_summary: string;
  paper_title: string;
  section_label?: string | null;
  location_hint?: string | null;
};

export type ToeScenario = {
  toe_candidate_id: string;
  world_id: string;
  mu_score: number;
  faizal_score: number;
  coverage_alg: number;
  mean_undecidability_index: number;
  energy_feasibility: number;
  rg_phase_index: number;
  rg_halting_indicator: number;
  evidence: EvidenceLink[];
};

export type HeatmapData = {
  toe_candidates: string[];
  world_ids: string[];
  mu_scores: number[][];
  faizal_scores: number[][];
  scenarios: Record<string, ToeScenario>;
};

export type OmegaLevel = "Ω-0" | "Ω-1" | "Ω-2" | "Ω-3";

export type SimUniverseStatus =
  | "SimUniverse-Uncertified"
  | "SimUniverse-Classical"
  | "SimUniverse-Qualified"
  | "SimUniverse-Aligned";

export type OmegaBadgeProps = {
  tenant: string;
  service: string;
  environment: string;
  omegaLevel: OmegaLevel;
  omegaScore: number;
  simUniverseScore: number;
  simUniverseStatus: SimUniverseStatus;
  lowTrustToeCount: number;
  lastUpdatedIso?: string;
};
