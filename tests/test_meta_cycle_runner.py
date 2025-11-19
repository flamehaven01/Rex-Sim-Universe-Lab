from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.meta_cycle_runner import run_meta_cycles


def test_meta_cycle_runner_basic():
    history = run_meta_cycles(cycles=2, threshold=0.0)
    assert len(history) == 2
    assert all(res.passed for res in history)

