import weather_service

def test_repeated_request_uses_cache(monkeypatch):
    weather_service._cache.clear()

    calls={"count":0}

    fake_data = {
        "daily": {
            "time": ["2020-06-01"],
            "temperature_2m_max": [39.0],
        }
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return fake_data

    class FakeClient:
        def __init__(self, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url, params):
            calls["count"] +=1
            return FakeResponse()

    monkeypatch.setattr(
        weather_service.httpx,
        "Client",
        FakeClient,
    )

    first_result = weather_service.fetch_weather_data(
        26.12, 85.39, "2020-06-01", "2020-06-01"
    )

    second_result = weather_service.fetch_weather_data(
        26.12, 85.39, "2020-06-01", "2020-06-01"
    )

    assert first_result==fake_data
    assert second_result==fake_data
    assert calls["count"]== 1

    weather_service._cache.clear()