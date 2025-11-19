# SimUniverse Lab Blueprint (REx + NNSL)

This document is an English-only scaffold that gathers the concept, math model, configuration snippets, folder layout, and core code fragments for experimenting with the simulation hypothesis using the REx Engine plus the NNSL TOE-Lab.

## 1. Overview
- **Corpus**: `REx.SimUniverseCorpus.v0.1` captures undecidable physics witnesses (spectral gap, uncomputable RG flows), astro/energy constraints, and MUH/CUH or Faizal-style philosophical stances.
- **SimUniverse Lab**: Runs Theory-of-Everything (TOE) or host candidates against undecidable witnesses to measure how far an algorithmic simulation can go and where non-algorithmic behavior is needed.

### Core components
- **REx side**
  - `sim_universe/corpus.py`: Loader for the JSON blueprint.
  - `sim_universe/models.py`: Pydantic models for `WorldSpec`, `ToeQuery`, `ToeResult`, and supporting configs.
  - `sim_universe/metrics.py`: Basic coverage and undecidability summaries.
  - `sim_universe/reporting.py`: Score helpers and reporting utilities.
  - `sim_universe/orchestrator.py`: High-level orchestration to call NNSL endpoints.
- **NNSL side (TOE-Lab)**
  - `nnsl_toe_lab/app.py`: FastAPI service exposing `/toe/world` and `/toe/query`.
  - `nnsl_toe_lab/solvers/*`: Toy solvers for spectral-gap and RG-flow witnesses.
  - `nnsl_toe_lab/semantic.py`: Placeholder semantic field and quantizer utilities.
- **Configuration**
  - `configs/rex_simuniverse.yaml`: REx-side toggles, defaults, and governance rules.
  - `configs/nnsl_toe_lab.yaml`: NNSL solver profiles and service options.

## 2. Mathematical model
- **WorldSpec**: `(id, toe_candidate, host_model, physics_modules, resolution, energy_budget)` with lattice/step cutoffs and budgets reflecting astro constraints.
- **ToeQuery**: `(world, witness_id, question, resource_budget, solver_chain)` describing a single experiment.
- **ToeResult**: `(status, approx_value, confidence, undecidability_index, t_soft_decision, t_oracle_called, metrics)` where metrics include runtime and sensitivity.
- **Undecidability index**: Combines complexity growth, sensitivity to resolution, and failure patterns via a sigmoid heuristic.
- **Coverage metrics**: `coverage_alg` (decided_true/false), `coverage_meta` (undecidable_theory or oracle use), and mean undecidability.

## 3. YAML snippets
- `configs/rex_simuniverse.yaml`: Enables SimUniverse, sets defaults for world resolution and budgets, wires NNSL endpoint, configures governance gates, and enables Prometheus metrics.
- `configs/nnsl_toe_lab.yaml`: Sets service host/port plus solver limits (system size for spectral gap, max depth for RG flow) and logging/observability options.

## 4. Folder layout (simplified)
```
configs/
  rex_simuniverse.yaml
  nnsl_toe_lab.yaml
src/
  rex/sim_universe/...
  nnsl_toe_lab/...
scripts/
  run_toe_heatmap.py
  run_toe_heatmap_with_evidence.py
```

## 5. Key code snippets
- `src/rex/sim_universe/__init__.py`: Re-exports models, corpus loader, and orchestrator.
- `src/nnsl_toe_lab/app.py`: Registers worlds and dispatches queries to solvers.
- `src/nnsl_toe_lab/solvers/spectral_gap.py`: TFIM toy spectral-gap sweep with undecidability scoring.
- `src/nnsl_toe_lab/solvers/rg_flow.py`: Watson-inspired RG toy with depth sweeps, phase classification, and halting indicators.
- `src/rex/core/stages/stage3_simuniverse.py`: Example Stage-3 pipeline step that creates a world, runs spectral-gap and RG queries, summarizes coverage/undecidability, and adds an energy-feasibility score based on astro constraints.

## 6. Helm chart placeholders
Example `values.yaml` fragments (not exhaustive) set image tags, service ports, config paths, resource limits, and Prometheus scraping for both the REx SimUniverse service and the NNSL TOE-Lab.

## 7. Running the toy stack
1. Start NNSL TOE-Lab locally: `uvicorn nnsl_toe_lab.app:app --host 0.0.0.0 --port 8080 --reload`.
2. Create a toy world via `/toe/world` then run spectral-gap and RG queries via `/toe/query` as shown in `scripts/run_toe_heatmap*.py`.
3. Inspect summaries in the returned payload: coverage, undecidability index, RG observables, and astro-driven energy feasibility.

## 8. SIDRCE Omega integration hooks
- `src/rex/sidrce/omega_schema.py`: Pydantic schema for Omega reports and axes, now treated as the authoritative spec for SIDRCE outputs.
- `src/rex/sidrce/omega_simuniverse_integration.py`: Aggregates MUH, Faizal, undecidability, and energy summaries into the `simuniverse_consistency` axis, renormalizes weights, and recalculates `omega_total`.
- `src/rex/sidrce/cli.py`: CLI wrapper that reads a base Omega JSON plus the Stage-5 SimUniverse trust summary and emits an updated report that GitOps gates and ASDP exporters can consume.

Example usage:

```bash
python -m rex.sidrce.cli \
  --omega-json sidrce_report_base.json \
  --simuniverse-trust-json artifacts/stage5_simuniverse/simuniverse_trust_summary_RUN.json \
  --out sidrce_report_with_simuniverse.json
```

All narrative text, comments, and code in this repository are now English-only to avoid mixed-language confusion.

## 9. Stage-5 trust summaries and registry updates
- `scripts/build_simuniverse_trust_summary.py`: Consumes a LawBinder Stage-5 JSON (or direct `simuniverse_summary` list), converts each entry into `ToeScenarioScores`, then emits per-TOE aggregates using `build_toe_trust_summary`.
- `rex.sim_universe.stage5_loader.load_stage5_scores`: Shared helper that parses Stage-5 payloads, extracts the embedded `run_id`, and normalizes list-style or dict-style JSON into `ToeScenarioScores` objects.
- `src/rex/sim_universe/trust_integration.py`: Hosts `ToeTrustSummary`, `serialize_trust_summaries`, and `update_registry_with_trust`. The default heuristic (`mu_min_good=0.4`, `faizal_max_good=0.7`) labels a TOE as low-trust when MUH support stays low while Faizal obstruction stays high across worlds.
- Registry automation flow:
  1. Stage-5 gate invokes the script:

     ```bash
     python scripts/build_simuniverse_trust_summary.py \
       --stage5-json artifacts/stage5/LawBinderStage5Report.json \
       --run-id "$RUN_ID" \
       --out artifacts/stage5/simuniverse_trust_summary_$RUN_ID.json
     ```

  2. A GitOps sidecar loads the resulting JSON and calls `update_registry_with_trust` so every `toe_candidate` entry gains `trust.simuniverse.{mu_score_avg,...,low_trust_flag}` plus the `simuniverse.low_trust` sovereign tag when appropriate.
  3. Meta-Router and downstream policies can now read `trust.tier` and `trust.simuniverse` without parsing the original Stage-5 artifact.

## 10. Router scoring, gates, and trust-tier penalties
- `simuniverse_quality(mu, faizal)` implements the canonical `0.7 * mu + 0.3 * (1 - faizal)` formula so MUH-aligned TOE candidates rise while Faizal-obstructed ones fall.
- `route_omega(base_omega, sim_q, trust_tier)` blends the Stage-5 signal into the Omega score and applies tier penalties (`high=1.0`, `normal=0.9`, `unknown=0.8`, `low=0.6`). Use the result inside Meta-Router/Fusion-Orchestrator weighting functions.
- `compute_trust_tier_from_failures(prev_tier, failure_count, failure_threshold)` lets Prometheus counters such as `simuniverse_stage5_gate_failures_total{toe_candidate=*}` demote chronic offenders to low-trust.
- GitOps Gate DSL example, assuming the exporter publishes per-TOE metrics like `simuniverse_mu_score_avg` and `simuniverse_faizal_score_avg`:

  ```yaml
  rules:
    - 'IF metric("asdpi_omega_total") < 0.82 THEN warn("Omega below 0.82")'
    - 'IF metric("simuniverse_mu_score_avg","toe_candidate","${TOE}") < 0.20 AND \
        metric("simuniverse_faizal_score_avg","toe_candidate","${TOE}") > 0.70 \
        THEN fail("SimUniverse gate failed for ${TOE}")'
    - 'IF metric("asdpi_omega_axis","axis","simuniverse_consistency") >= 0.75 AND \
        metric("simuniverse_mu_score_avg","toe_candidate","${TOE}") >= 0.60 \
        THEN warn("SimUniverse strong candidate ${TOE}")'
  ```

Together these helpers ensure that the Stage-5 experiment acts as a first-class governance signal across ASDP, Meta-Router, and FinOps surfaces.

## 11. DFI meta CLI for end-to-end governance rehearsals
- `python -m rex.sim_universe.dfi_meta_cli` ties Stage-5 payloads, trust summaries, and Omega axes into a single “DFI meta” batch.
  - Inputs: `--stage5-json`, `--omega-json`, `--out-dir`, optional `--run-id`, and knobs for MUH/Faizal heuristics or axis weights.
  - Default behavior runs **30 iterations** to mimic repeated governance reviews, emitting `simuniverse_trust_summary_iter_XX.json`, `omega_with_simuniverse_iter_XX.json`, and a consolidated `dfi_meta_summary.json` verdict ("simulatable" vs "obstructed").
- Run it with `PYTHONPATH=src` (or install the package) so the `rex.*` modules resolve without poetry/pip installs.
- Sample artifacts live under `samples/` so CI or humans can quickly sanity-check the loop:

```bash
python -m rex.sim_universe.dfi_meta_cli \
  --stage5-json samples/stage5_sample.json \
  --omega-json samples/omega_base_sample.json \
  --out-dir artifacts/dfi_meta_demo \
  --iterations 30
```

This meta CLI gives ASDP operators a reproducible way to rehearse the combined REx Engine → SimUniverse → LawBinder → Ω certification flow whenever new TOE evidence lands.

## 12. Control plane, registry sync, and metrics exporter
- **Run registry (`rex.sim_universe.registry`)** keeps every SimUniverse execution keyed by `run_id`, environment, Git SHA, and experiment inputs. The helper stores `omega_total` plus `simuniverse_consistency` once a run finishes so dashboards and downstream automation can trace the provenance of every Omega verdict.
- **Control plane API (`rex.sim_universe.control_plane`)** exposes a FastAPI surface with `POST /runs`, `GET /runs/{run_id}`, and `GET /runs` endpoints. Internally it calls `run_stage5_for_run_id`, which executes the Stage-5 → trust summary → Omega merge loop, writes artifacts to `artifacts/simuniverse_runs/<run_id>/`, and updates the registry atomically.
- **ASDP registry sync (`scripts/sync_simuniverse_trust_to_asdp.py`)** consumes any `simuniverse_trust_summary.json` plus `asdp.knowledge.yaml`, applies `update_registry_with_trust`, and rewrites the registry so every TOE candidate gains `trust.simuniverse.*` metrics and the `simuniverse.low_trust` tag when needed:

  ```bash
  python scripts/sync_simuniverse_trust_to_asdp.py \
    --registry asdp.knowledge.yaml \
    --trust artifacts/stage5/simuniverse_trust_summary_RUN.json
  ```

- **Prometheus exporter (`rex/sim_universe/metrics_exporter.py`)** publishes gauges such as `simuniverse_mu_score_avg{toe_candidate=*}`, `simuniverse_faizal_score_avg{toe_candidate=*}`, `asdpi_omega_axis{axis="simuniverse_consistency"}`, and `asdpi_omega_total`. Deploy it next to the artifacts bucket or attach it to the same persistent volume used by Stage-5 so GitOps Gate DSL rules, Grafana, and alerting policies see real-time SimUniverse governance signals.

Together these three pillars turn the conceptual Stage-5 workflow into an operational control plane: every run is registered, Omega/ASDP artifacts remain queryable, and governance signals stay synchronized across Meta-Router, FinOps, and certification dashboards.
