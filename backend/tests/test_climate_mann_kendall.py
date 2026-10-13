
from climate_mann_kendall import calculate_mann_kendall_trend


def test_detects_significant_increasing_trend():
    result = calculate_mann_kendall_trend([1, 2, 3, 4, 5])

    assert result["s_statistic"] == 10
    assert result["direction"] == "increasing"
    assert result["p_value"] < 0.05


def test_detects_significant_decreasing_trend():
    result = calculate_mann_kendall_trend([5, 4, 3, 2, 1])

    assert result["s_statistic"] == -10
    assert result["direction"] == "decreasing"
    assert result["p_value"] < 0.05


def test_constant_series_has_no_significant_trend():
    result = calculate_mann_kendall_trend([4, 4, 4, 4, 4])

    assert result["s_statistic"] == 0
    assert result["kendall_tau"] == 0
    assert result["p_value"] == 1.0
    assert result["direction"] == "no significant trend"


def test_tied_values_are_handled():
    result = calculate_mann_kendall_trend([1, 1, 2, 2, 3])

    assert result["s_statistic"] == 8
    assert 0 <= result["p_value"] <= 1
    assert result["direction"] == "no significant trend"


def test_single_observation_has_no_significant_trend():
    result = calculate_mann_kendall_trend([7])

    assert result["p_value"] == 1.0
    assert result["direction"] == "no significant trend"


def test_empty_series_has_no_significant_trend():
    result = calculate_mann_kendall_trend([])

    assert result["p_value"] == 1.0
    assert result["direction"] == "no significant trend"
