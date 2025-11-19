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

## Omega + SimUniverse badges

Display Ω certification data and SimUniverse trust signals consistently across dashboards or standalone HTML reports with the `OmegaSimUniverseHeader` React component:

```tsx
import { OmegaSimUniverseHeader } from "../ui/OmegaSimUniverseHeader";

<OmegaSimUniverseHeader
  tenant="flamehaven"
  service="REx SimUniverse"
  environment="prod"
  omegaLevel="Ω-2"
  omegaScore={0.864}
  simUniverseScore={0.78}
  simUniverseStatus="SimUniverse-Qualified"
  lowTrustToeCount={1}
  lastUpdatedIso="2025-11-18T13:45:00Z"
/>;
```

Key details:

1. Ω badge colors adapt to the level (Ω-3 violet/cyan gradient, Ω-2 indigo/sky, Ω-1 slate, Ω-0 muted slate).
2. SimUniverse status badges support `SimUniverse-Uncertified`, `SimUniverse-Classical`, `SimUniverse-Qualified`, and `SimUniverse-Aligned` states.
3. The header shows the normalized `simuniverse_consistency` score plus an optional low-trust warning if any TOE candidates are demoted.
4. Tailwind classes are baked in so it can drop into the existing dashboard layout without extra wiring.

If you need the same layout in a plain Jinja2/HTML context, reuse the inline-styled snippet below (swap in your values when rendering):

```html
<header style="width:100%;border-bottom:1px solid #1f2933;background-color:rgba(15,23,42,0.9);">
  <div style="max-width:72rem;margin:0 auto;padding:0.75rem 1rem;display:flex;justify-content:space-between;align-items:center;gap:1rem;">
    <div style="display:flex;flex-direction:column;gap:0.25rem;">
      <div style="display:flex;align-items:center;gap:0.5rem;">
        <h1 style="font-size:0.9rem;font-weight:600;color:#f9fafb;">REx SimUniverse</h1>
        <span style="display:inline-flex;align-items:center;gap:0.25rem;border-radius:999px;border:1px solid #374151;padding:0.125rem 0.5rem;font-size:0.6rem;color:#e5e7eb;">
          <span style="width:0.3rem;height:0.3rem;border-radius:999px;background-color:#34d399;"></span>
          flamehaven
        </span>
        <span style="display:inline-flex;align-items:center;gap:0.25rem;border-radius:999px;background:#020617;padding:0.125rem 0.5rem;font-size:0.6rem;color:#e5e7eb;">
          <span style="width:0.3rem;height:0.3rem;border-radius:999px;background-color:#38bdf8;"></span>
          prod
        </span>
      </div>
      <p style="font-size:0.6rem;color:#6b7280;">
        Last Ω / SimUniverse certification update:
        <time datetime="2025-11-18T13:45:00Z">2025-11-18T13:45:00Z</time>
      </p>
    </div>
    <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-end;gap:0.5rem;font-size:0.7rem;">
      <div style="display:inline-flex;align-items:center;gap:0.25rem;border-radius:999px;padding:0.25rem 0.75rem;background:linear-gradient(to right,#4f46e5,#38bdf8);box-shadow:0 10px 25px rgba(0,0,0,0.6);color:#020617;">
        <div style="display:flex;align-items:center;justify-content:center;width:1.25rem;height:1.25rem;border-radius:999px;background:rgba(15,23,42,0.4);font-size:0.6rem;font-weight:600;">Ω</div>
        <span style="font-weight:600;">Ω-2</span>
        <span style="margin-left:0.25rem;font-size:0.6rem;color:rgba(15,23,42,0.75);">0.864</span>
      </div>
      <div style="display:inline-flex;align-items:center;gap:0.25rem;border-radius:999px;border:1px solid rgba(34,197,235,0.6);padding:0.25rem 0.75rem;background:rgba(15,23,42,0.8);color:#a5f3fc;">
        <span style="width:0.3rem;height:0.3rem;border-radius:999px;background-color:#22c55e;"></span>
        <span style="font-weight:500;">SimUniverse-Qualified</span>
      </div>
      <div style="display:inline-flex;align-items:center;gap:0.25rem;border-radius:999px;background:#020617;padding:0.25rem 0.75rem;color:#e5e7eb;">
        <span style="font-size:0.6rem;text-transform:uppercase;letter-spacing:0.05em;color:#9ca3af;">simuniverse_consistency</span>
        <span style="font-family:monospace;font-size:0.75rem;">0.780</span>
      </div>
      <div style="display:inline-flex;align-items:center;gap:0.25rem;border-radius:999px;background:rgba(190,24,93,0.4);padding:0.25rem 0.75rem;color:#fecaca;">
        <span style="display:flex;align-items:center;justify-content:center;width:1rem;height:1rem;border-radius:999px;background:#f97373;font-size:0.6rem;">!</span>
        <span style="font-weight:500;">1 low-trust TOE</span>
      </div>
    </div>
  </div>
</header>
```

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

## Omega certification with SimUniverse consistency

SimUniverse is also exposed as an Ω certification dimension so that SIDRCE / ASDP tooling can reason about "simulation alignment" alongside safety and robustness:

1. Produce a trust summary via the evidence-aware CLI (see above). Optionally capture real traffic weights for each TOE route over the certification window.
2. Build an Ω report that merges the baseline dimensions with the new `simuniverse_consistency` axis:

   ```bash
   python scripts/build_omega_report.py \
     --tenant flamehaven \
     --service rex-simuniverse \
     --stage stage5 \
     --run-id ${RUN_ID} \
     --base-dimensions artifacts/base_dims.json \
     --trust-summary reports/simuniverse_trust_summary_${RUN_ID}.json \
     --traffic-weights artifacts/toe_traffic_weights.json \
     --lawbinder-report artifacts/lawbinder_stage5_${RUN_ID}.json \
     --output reports/omega_${RUN_ID}.json
   ```

   `base_dims.json` is a simple `{"safety": 0.91, "robustness": 0.87, "alignment": 0.83}` map. The script automatically injects the SimUniverse dimension, derives the traffic-weighted score, imports LawBinder attachment URLs (HTML, notebook, trust summary, etc.), and normalizes Ω + level thresholds (Ω-3/Ω-2/Ω-1/Ω-0) so that `simuniverse_consistency` is a first-class lever.

3. Export the resulting metrics to Prometheus/Gate DSL. The report captures per-TOE SimUniverse quality, the aggregated global score, and attachment links so auditors can trace back to the raw HTML/notebook outputs. Meta-Router rules or Gate DSL policies can now depend on the published `simuniverse_consistency_score` just like `omega`, `coverage`, or FinOps signals.

## License
MIT License (see `LICENSE` for details).
