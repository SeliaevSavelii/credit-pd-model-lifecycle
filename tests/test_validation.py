import numpy as np
import pytest
from scipy.stats import beta
from sklearn.metrics import roc_auc_score

from src.validation import (
    assign_grades, binomial_pvalue, delong_test, gini, grade_edges,
    hosmer_lemeshow, jeffreys_pvalue, ks_statistic, psi,
)


def test_gini_perfect_reversed_and_random():
    y = np.array([0, 0, 1, 1])
    assert gini(y, [0.1, 0.2, 0.8, 0.9]) == pytest.approx(1.0)
    assert gini(y, [0.9, 0.8, 0.2, 0.1]) == pytest.approx(-1.0)
    assert gini(y, [0.5, 0.5, 0.5, 0.5]) == pytest.approx(0.0)


def test_gini_hand_example():
    # 4 bad-good pairs: 3 correctly ordered, 1 reversed -> AUC 0.75 -> Gini 0.5
    y = np.array([1, 1, 0, 0])
    s = np.array([0.9, 0.4, 0.5, 0.1])
    assert gini(y, s) == pytest.approx(0.5)


def test_ks_perfect_separation():
    assert ks_statistic([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == pytest.approx(1.0)


def test_psi_identical_and_hand_value():
    assert psi([0.5, 0.5], [0.5, 0.5]) == pytest.approx(0.0)
    expected = 0.1 * np.log(1.2) + 0.1 * np.log(1 / 0.8)
    assert psi([0.5, 0.5], [0.6, 0.4]) == pytest.approx(expected)
    assert psi([0.5, 0.5], [0.6, 0.4]) == pytest.approx(0.0405, abs=1e-4)


def test_jeffreys_matches_beta_definition_and_direction():
    assert jeffreys_pvalue(1000, 20, 0.02) == pytest.approx(beta.cdf(0.02, 20.5, 980.5))
    # More observed defaults than predicted -> stronger evidence of underestimation -> smaller p.
    assert jeffreys_pvalue(1000, 40, 0.02) < 0.01 < jeffreys_pvalue(1000, 20, 0.02)


def test_binomial_direction():
    assert binomial_pvalue(1000, 40, 0.02) < 0.01
    assert binomial_pvalue(1000, 10, 0.02) > 0.5


def test_delong_matches_sklearn_and_identical_scores():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 2000)
    a = y + rng.normal(0, 1, 2000)
    b = y + rng.normal(0, 2, 2000)
    result = delong_test(y, a, b)
    assert result["gini_a"] == pytest.approx(2 * roc_auc_score(y, a) - 1)
    assert result["gini_b"] == pytest.approx(2 * roc_auc_score(y, b) - 1)
    assert result["p_value"] < 0.001
    assert delong_test(y, a, a)["p_value"] == pytest.approx(1.0)


def test_grades_cover_all_values():
    pd_ref = np.linspace(0.01, 0.5, 800)
    edges = grade_edges(pd_ref, n_grades=8)
    grades = assign_grades(np.array([0.0, 0.01, 0.25, 0.5, 0.99]), edges)
    assert grades.min() == 1 and grades.max() == 8
    assert np.bincount(assign_grades(pd_ref, edges))[1:].tolist() == [100] * 8


def test_hosmer_lemeshow_well_calibrated_is_not_rejected():
    rng = np.random.default_rng(2)
    p = rng.uniform(0.05, 0.3, 50_000)
    y = rng.uniform(size=p.size) < p
    assert hosmer_lemeshow(y, p)["p_value"] > 0.01
