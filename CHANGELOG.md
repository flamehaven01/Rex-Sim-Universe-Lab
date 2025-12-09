# Changelog

## 2025-12-06
- Added optional lab demos:
  - `scripts/universe_sim_lab.py` now supports multi-backend runs, fine-structure target override (`--fine-structure`), optional GodelProbe diagnostics (`--godel-probe`), and JSON export (`--save`).
  - `scripts/statistical_reality_test.py` provides a lightweight Monte Carlo reality check with configurable size/trials and optional LaTeX/JSON output.
  - `nnsl_toe_lab/experiments/godel_probe.py` supplies Lyapunov/compressibility/perturbation metrics for undecidability-themed experiments.
- Core undecidability helpers extended with Lyapunov/compressibility/perturbation utilities.
- Documentation updates: new `docs/lab_demos.md`, README lab demo section, CI matrix samples, and lab-ui optional dependency (rich) noted.

## 2025-12-09
- CI: added GitHub Actions workflow (`.github/workflows/ci.yml`) running pytest with coverage reporting and XML artifact upload.
- Quality: coverage threshold enforced at 50% to prevent regressions while keeping CI green during pipeline bootstrap.
