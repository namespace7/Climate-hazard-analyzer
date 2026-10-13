
from datetime import datetime, timedelta, timezone

import config.analysis_repository as repository


class FakeCollection:
    def __init__(self, document=None):
        self.document = document
        self.query = None
        self.updated_document = None

    def find_one(self, query, projection):
        self.query = query
        if self.document is None:
            return None
        return dict(self.document)

    def update_one(self, query, update, upsert=False):
        self.updated_document = {
            "query": query,
            "update": update,
            "upsert": upsert,
        }


def test_cache_miss_returns_none(monkeypatch):
    fake_collection = FakeCollection()
    monkeypatch.setattr(
        repository, "analysis_collection", fake_collection
    )

    result = repository.get_cached_analysis(
        26.12, 85.39, "2020-01-01", "2020-12-31"
    )

    assert result is None
    assert fake_collection.query["algorithm_version"] == (
        repository.ANALYSIS_VERSION
    )


def test_save_analysis_sets_version_and_timestamp(monkeypatch):
    fake_collection = FakeCollection()
    monkeypatch.setattr(
        repository, "analysis_collection", fake_collection
    )

    result = {
        "latitude": 26.12,
        "longitude": 85.39,
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
        "heatwave_event_count": 2,
    }

    repository.save_analysis(result)

    saved = fake_collection.updated_document

    assert saved["upsert"] is True
    assert saved["update"]["$set"]["algorithm_version"] == (
        repository.ANALYSIS_VERSION
    )
    assert isinstance(
        saved["update"]["$set"]["updated_at"], datetime
    )


def test_cache_hit_removes_internal_fields(monkeypatch):
    fake_collection = FakeCollection({
        "latitude": 26.12,
        "longitude": 85.39,
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
        "algorithm_version": repository.ANALYSIS_VERSION,
        "updated_at": datetime.now(timezone.utc),
        "heatwave_event_count": 2,
    })

    monkeypatch.setattr(
        repository, "analysis_collection", fake_collection
    )

    result = repository.get_cached_analysis(
        26.12, 85.39, "2020-01-01", "2020-12-31"
    )

    assert result["heatwave_event_count"] == 2
    assert "updated_at" not in result
    assert "algorithm_version" not in result
