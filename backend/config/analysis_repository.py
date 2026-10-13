
from datetime import datetime, timedelta, timezone

from config.database import analysis_collection

ANALYSIS_VERSION = 1
CACHE_TTL_HOURS = 24


def _analysis_key(latitude, longitude, start_date, end_date):
    return {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
    }


def get_cached_analysis(latitude, longitude, start_date, end_date):
    cutoff = datetime.now(timezone.utc) - timedelta(
        hours=CACHE_TTL_HOURS
    )

    query = _analysis_key(
        latitude, longitude, start_date, end_date
    )
    query["algorithm_version"] = ANALYSIS_VERSION
    query["updated_at"] = {"$gte": cutoff}

    document = analysis_collection.find_one(
        query,
        {"_id": 0},
    )

    if document is None:
        return None

    document.pop("updated_at", None)
    document.pop("algorithm_version", None)
    return document


def save_analysis(result):
    query = _analysis_key(
        result["latitude"],
        result["longitude"],
        result["start_date"],
        result["end_date"],
    )

    document = dict(result)
    document["algorithm_version"] = ANALYSIS_VERSION
    document["updated_at"] = datetime.now(timezone.utc)

    analysis_collection.update_one(
        query,
        {"$set": document},
        upsert=True,
    )
