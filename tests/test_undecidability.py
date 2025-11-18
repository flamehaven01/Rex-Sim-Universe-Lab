import math

import pytest

from nnsl_toe_lab.undecidability import summarize_undecidability_sweep


def test_summarize_handles_empty():
    result = summarize_undecidability_sweep([], [], [])
    assert result == (0.0, 0.0, 1.0, 0.0)


def test_summarize_combines_complexity_sensitivity_and_failures():
    values = [1.0, 1.2, None]
    runtimes = [0.2, 0.4, 0.3]
    flags = [False, False, True]

    u_index, time_to_partial, complexity_growth, sensitivity = summarize_undecidability_sweep(
        values, runtimes, flags
    )

    assert pytest.approx(time_to_partial, rel=1e-6) == 0.2
    assert pytest.approx(complexity_growth, rel=1e-6) == 2.0
    assert sensitivity > 0.08 and sensitivity < 0.1
    assert 0.4 < u_index < 0.5
