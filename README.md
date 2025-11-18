# Rex Sim Universe Lab

This repository hosts the blueprint and toy scaffolding for evaluating how computable or simulatable a universe might be using the REx Engine and NNSL TOE-Lab.

## Included artifacts
- `sim_universe_blueprint.json`: Standardized experiment/corpus schema covering Faizal MToE ideas, undecidable physics witnesses, MUH/CUH-inspired hypotheses, and energy/information constraints for REx+NNSL workflows.
- `docs/SimUniverseLabBlueprint.md`: A one-stop scaffold that explains the SimUniverse Lab concept, mathematical model, YAML configuration samples, folder layout, and key code/Helm snippets.

## Usage guide
1. Choose witnesses and hypothesis clusters from `corpus.clusters` in the JSON blueprint.
2. Build `WorldSpec` objects and run `ToeQuery` calls against the endpoints defined in `experiment_schema.nnsl_binding`.
3. Aggregate `ToeResult` values via `metrics_and_scoring` to evaluate simulation plausibility, energy feasibility, and undecidability patterns.
4. See `docs/SimUniverseLabBlueprint.md` for detailed configuration guidance, folder structure, and code snippets.

## Toy code scaffold
- `src/nnsl_toe_lab/app.py`: FastAPI TOE-Lab toy server providing `/toe/world` and `/toe/query` endpoints plus routing for spectral-gap and RG-flow witnesses.
- `src/nnsl_toe_lab/solvers/spectral_gap.py`: 1D TFIM toy solver performing full diagonalization to measure the spectral gap.
- `src/rex/sim_universe/orchestrator.py`: REx-side orchestrator that calls NNSL endpoints.
- `src/rex/core/stages/stage3_simuniverse.py`: Example Stage-3 hook that creates a world, runs queries, and appends summaries to the pipeline payload.
- `configs/rex_simuniverse.yaml`: Baseline configuration used by the Stage-3 example.

## License
MIT License (see `LICENSE` for details).
