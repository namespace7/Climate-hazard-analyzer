from weather_service import fetch_weather_data
from climate_threshold import calculate_heatwave_threshold
from heatwave import detect_heatwaves
from datetime import date
from climate_trend import calculate_heatwave_trend
from climate_mann_kendall import calculate_mann_kendall_trend

def summarise_events_by_year(events, start_date, end_date):
    """
    Summarise heatwave events for every calender year in the 
    requested date range, including years with zero events.
    """
    start_year = date.fromisoformat(start_date).year
    end_year = date.fromisoformat(end_date).year

    annual_statistics = {}

    # Create an entry for every year in the requested range.
    for year in range(start_year, end_year +1):
        annual_statistics[year] = {
            "year": year,
            "event_count": 0,
            "total_heatwave_days": 0,
            "longest_event_days": 0
        }

    # Add each detected event to the year in which it starts.
    for event in events:
        year = date.fromisoformat(event["start_date"]).year

        if year not in annual_statistics:
            continue

        stats = annual_statistics[year]

        stats["event_count"] += 1
        stats["total_heatwave_days"] += event["duration"]

        stats["longest_event_days"] = max(
            stats["longest_event_days"],
            event["duration"]
        )

    return list(annual_statistics.values())


def analyze_climate(latitude, longitude, start_date, end_date):
    data = fetch_weather_data(
        latitude,
        longitude,
        start_date,
        end_date
    )

    if data is None:
        raise RuntimeError("Could not fetch weather data")

    daily = data.get("daily")

    if not isinstance(daily, dict):
        raise ValueError("Weather response has no daily data")

    dates = daily.get("time", [])
    temperatures = daily.get("temperature_2m_max", [])

    if not dates or len(dates) != len(temperatures):
        raise ValueError("Invalid or empty weather records")

    valid_temperatures = [
        temperature
        for temperature in temperatures
        if temperature is not None
    ]

    if not valid_temperatures:
        raise ValueError("No valid temperatures available")

    threshold = calculate_heatwave_threshold(
        valid_temperatures
    )

    events = detect_heatwaves(
        dates,
        temperatures,
        threshold= threshold,
        min_duration=3
    )

    annual_statistics = summarise_events_by_year(
    events,
    start_date,
    end_date,
    )

    trend = calculate_heatwave_trend(annual_statistics)

    mann_kendall = calculate_mann_kendall_trend(
    [
        item["total_heatwave_days"]
        for item in annual_statistics
    ])

    return {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "threshold_celsius": round(threshold, 2),
        "valid_temperature_records": len(valid_temperatures),
        "heatwave_event_count": len(events),
        "total_heatwave_days": sum(
            event["duration"] for event in events
        ),
        "annual_statistics": annual_statistics,
        "trend": trend,
        "mann_kendall": mann_kendall,
        "events": events
    }

if __name__ == "__main__":
    results = analyze_climate(
        latitude=26.12,
        longitude=85.39,
        start_date="1990-01-01",
        end_date="2020-12-31"
    )

    for key, value in results.items():
        print(f"{key}: {value}")

    for item in results["annual_statistics"]:
        print(item)