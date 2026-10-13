
import analyze_climate as climate_module


def test_analysis_includes_regression_and_mann_kendall(monkeypatch):
    dates = [
        f"{year}-01-{day:02d}"
        for year in range(2020, 2023)
        for day in range(1, 6)
    ]

    temperatures = [
        20, 21, 22, 23, 24,
        20, 21, 22, 23, 24,
        20, 21, 22, 23, 24,
    ]

    monkeypatch.setattr(
        climate_module,
        "fetch_weather_data",
        lambda *args: {
            "daily": {
                "time": dates,
                "temperature_2m_max": temperatures,
            }
        },
    )

    result = climate_module.analyze_climate(
        latitude=26.12,
        longitude=85.39,
        start_date="2020-01-01",
        end_date="2022-01-05",
    )

    assert "trend" in result
    assert "mann_kendall" in result

    mk = result["mann_kendall"]
    assert "s_statistic" in mk
    assert "z_statistic" in mk
    assert "kendall_tau" in mk
    assert "p_value" in mk
    assert "direction" in mk
