from datetime import date

from fastapi import FastAPI, HTTPException, Query
from pymongo.errors import PyMongoError
from analyze_climate import analyze_climate
from config.analysis_repository import (
    get_cached_analysis,
    save_analysis,
)

app = FastAPI(
    title="Climate Hazard Analyzer",
    description= "Analyze historical heatwave events and trends.",
    version= "1.0.0"
    )

@app.get("/")
def home():
    return {
        "message": "Climate Hazard Analyzer is running"
    }

@app.get("/api/analyze")
def get_climate_analysis(
    latitude: float = Query(26.12, ge=-90, le=90),
    longitude: float = Query(85.39, ge=-180, le=180),
    start_date: date = Query(date(1990, 1, 1)),
    end_date: date = Query(date(2020, 12, 31)),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be on or before end_date",
        )

    start = start_date.isoformat()
    end = end_date.isoformat()

    # 1. Look for a cached result.
    try:
        cached_result = get_cached_analysis(
            latitude, longitude, start, end
        )
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Analysis storage is temporarily unavailable",
        )

    if cached_result is not None:
        return cached_result

    # 2. Calculate a fresh result.
    try:
        result = analyze_climate(
            latitude=latitude,
            longitude=longitude,
            start_date=start,
            end_date=end,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )
    except RuntimeError:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve or process weather data",
        )

    # 3. Persist the result for future requests.
    try:
        save_analysis(result)
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Analysis completed but could not be saved",
        )

    return result