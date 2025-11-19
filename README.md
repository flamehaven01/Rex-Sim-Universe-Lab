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
- `scripts/meta_cycle_runner.py`: Lightweight meta-coverage driver that replays the toy scenario for multiple cycles and enforces a 90% threshold.
- `scripts/dfi_meta_cli.py`: Sandboxed DFI-META CLI exposing meta-cognitive evolution commands (default 30-cycle evolve runs) and quick coherence checks.
- `scripts/run_toe_heatmap_with_evidence.py`: Async CLI that executes the toy witnesses for multiple TOE candidates, aggregates MUH/Faizal scores, and emits Markdown/HTML/Jupyter/React-friendly evidence-aware reports plus trust summaries and Prometheus metrics.
- `scripts/update_toe_trust.py`: Helper that patches an ASDP-style registry JSON using a SimUniverse trust summary (including optional Stage-5 failure counters).
- `templates/simuniverse_report.html`: Glassmorphic Jinja2 template used to render an interactive HTML dashboard for a run.
- `ui/SimUniverseHeatmap.tsx`: React + Tailwind component that consumes the exported JSON payload and mirrors the HTML experience inside a web app.

## Evidence-aware reporting
Generate a Markdown table that aligns MUH/Faizal scores with the corpus evidence supporting (or contesting) each TOE candidate:

```bash
python scripts/run_toe_heatmap_with_evidence.py \
  --config configs/rex_simuniverse.yaml \
  --corpus corpora/REx.SimUniverseCorpus.v0.2.json \
  --output docs/sim_universe_heatmap.md \
  --html reports/simuniverse_report.html \
  --notebook reports/SimUniverse_Results.ipynb \
  --react-json reports/simuniverse_payload.json \
  --trust-json reports/simuniverse_trust_summary.json \
  --prom-metrics reports/simuniverse_metrics.prom
```

Notes:

1. `--output` controls the Markdown destination; omit it to print to stdout.
2. `--html` renders `templates/simuniverse_report.html` via Jinja2 (install `jinja2` if it is not already present).
3. `--notebook` builds `SimUniverse_Results.ipynb` using `nbformat`/`matplotlib` so you can archive the run inside CI or LawBinder packages.
4. `--react-json` writes a payload that can be fed directly into `ui/SimUniverseHeatmap.tsx` for dashboards.
5. `--trust-json` emits an aggregate trust summary where MUH/Faizal averages are computed per TOE candidate and low-trust flags are derived from the heuristics described in `src/rex/sim_universe/governance.py`.
6. `--prom-metrics` writes Prometheus exposition text mirroring the trust summary so Gate DSL / Meta-Router rules can react to SimUniverse outcomes.

All outputs link each TOE/world cell with up to three high-weight claims (e.g., Faizal Sec. 3 or Tegmark Ch. 12) drawn from `REx.SimUniverseCorpus.v0.2`.

## Governance and router integration

SimUniverse trust signals can be pushed into ASDP/Meta-Router workflows in two steps:

1. Run `scripts/run_toe_heatmap_with_evidence.py` with `--trust-json` and (optionally) `--prom-metrics` enabled. The JSON payload lists MUH/Faizal/undecidability/energy averages per TOE candidate plus a `low_trust_flag`. The Prometheus exposition mirrors the same values so Gate DSL rules can watch them in real time.
2. Feed the trust summary into `scripts/update_toe_trust.py`:

   ```bash
   python scripts/update_toe_trust.py \
     --registry registry/toe_candidates.json \
     --trust-summary reports/simuniverse_trust_summary.json \
     --failure-counts reports/stage5_failure_counts.json \
     --failure-threshold 3
   ```

   The helper updates each registry entry's `trust.tier` (demoting repeat offenders to `low`) and maintains a `simuniverse.low_trust` sovereign tag that the Meta-Router can reference when routing or gating TOE candidates.

## License
MIT License (see `LICENSE` for details).
