"""Shared national shocks must not masquerade as independent regional evidence."""
import numpy as np
import pytest

from research import estimate
from research.housing_robustness import synchronized_block_mean


def test_synchronized_blocks_preserve_common_shocks_across_regions():
    common = np.repeat([-8.0, -4.0, 2.0, 6.0, 4.0, -6.0], 8)
    one = [{"ccaa": "A", "t": t, "ipv_yoy": float(x)} for t, x in enumerate(common)]
    many = [{**r, "ccaa": f"r{i}"} for i in range(19) for r in one]
    primary = estimate.pooled_mean(many, "ipv_yoy", "ccaa")
    single_boot = synchronized_block_mean(one, n_boot=300, block_length=8)
    panel_boot = synchronized_block_mean(many, n_boot=300, block_length=8)

    # Identical regional histories have no between-region uncertainty, even
    # though substantial uncertainty remains over which time blocks recur.
    assert primary is not None and primary.se < 1e-10
    assert panel_boot["se"] > 0.5
    assert panel_boot["ci_low"] < panel_boot["mean"] < panel_boot["ci_high"]
    for key in ("mean", "se", "ci_low", "ci_high"):
        assert panel_boot[key] == pytest.approx(single_boot[key])


def test_block_bootstrap_does_not_treat_a_calendar_gap_as_consecutive():
    rows = [{"ccaa": "A", "t": t, "ipv_yoy": 1.0} for t in [0, 1, 2, 4, 5, 6]]
    with pytest.raises(ValueError, match="consecutive"):
        synchronized_block_mean(rows, block_length=4)
