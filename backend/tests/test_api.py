from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Climate Hazard Analyzer is running"
    )


def test_analyze_endpoint(monkeypatch):
    fake_result = {
        "latitude": 26.12,
        "longitude": 85.39,
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
        "threshold_celsius": 39.2,
        "valid_temperature_records": 366,
        "heatwave_event_count": 2,
        "total_heatwave_days": 8,
        "annual_statistics": [],
        "trend": {
            "slope_days_per_year": 0.5,
            "direction": "increasing",
            "p_value": 0.1,
            "r_squared": 0.5,
        },
        "events": [],
    }

    def fake_analyze_climate(
        latitude, longitude, start_date, end_date
    ):
        return fake_result

    monkeypatch.setattr(
        main, "analyze_climate", fake_analyze_climate
    )

    monkeypatch.setattr(main, "save_analysis", lambda result: None)

    monkeypatch.setattr(
    main, "get_cached_analysis", lambda *args: None)

    response = client.get(
        "/api/analyze",
        params={
            "latitude": 26.12,
            "longitude": 85.39,
            "start_date": "2020-01-01",
            "end_date": "2020-12-31",
        },
    )

    assert response.status_code == 200
    assert response.json()["trend"]["direction"] == "increasing"
    assert response.json()["annual_statistics"] == []


def test_rejects_start_date_after_end_date():
    response = client.get(
        "/api/analyze",
        params={
            "start_date": "2021-01-01",
            "end_date": "2020-01-01",
        },
    )

    assert response.status_code == 400


def test_invalid_coordinates_are_rejected():
    response = client.get(
        "/api/analyze",
        params={"latitude": 100, "longitude": 85.39},
    )

    assert response.status_code == 422


def test_invalid_date_order_is_rejected():
    response = client.get(
        "/api/analyze",
        params={
            "start_date": "2021-01-01",
            "end_date": "2020-01-01",
        },
    )

    assert response.status_code == 400


def test_weather_failure_returns_502(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_cached_analysis",
        lambda *args: None,
    )

    def fail_analysis(*args, **kwargs):
        raise RuntimeError("Weather provider unavailable")

    monkeypatch.setattr(main, "analyze_climate", fail_analysis)

    response = client.get(
        "/api/analyze",
        params={
            "start_date": "2020-01-01",
            "end_date": "2020-12-31",
        },
    )

    assert response.status_code == 502
