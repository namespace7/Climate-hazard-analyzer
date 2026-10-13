import pytest

from climate_trend import calculate_heatwave_trend

def test_detects_increasing_trend():
    annual_statistics = [
        {"year": 2020, "total_heatwave_days": 2},
        {"year": 2021, "total_heatwave_days": 4},
        {"year": 2022, "total_heatwave_days": 6},
        {"year": 2023, "total_heatwave_days": 8},
    ]

    result = calculate_heatwave_trend(annual_statistics)

    assert result ["direction"] == "increasing"
    assert result ["slope_days_per_year"] == 2.0

def test_require_at_least_two_years():
    with pytest.raises(ValueError):
        calculate_heatwave_trend([
            {"year":2020, "total_heatwave_days": 2}
        ])