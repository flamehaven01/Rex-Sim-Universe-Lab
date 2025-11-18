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

All narrative text, comments, and code in this repository are now English-only to avoid mixed-language confusion.
