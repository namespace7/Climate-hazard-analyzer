from time import monotonic

import httpx

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Cache format: {request_key: (expiry_time, weather-data)}
_cache = {}

# Cache weather responses for one hour.
CACHE_TTL_SECONDS = 60 * 60

def fetch_weather_data(latitude, longitude, start_date, end_date):
    cache_key = (
        round(latitude, 4),
        round(longitude, 4),
        start_date,
        end_date,
    )

    now = monotonic()
    cached_entry = _cache.get(cache_key)

    if cached_entry is not None:
        expires_at, cached_data = cached_entry

        if now < expires_at:
            print("Weather cache: HIT")
            return cached_data

        # Remove an expired entry.
        del _cache[cache_key]
    
    print("Weather cache: MISS")
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max",
        "timezone": "Asia/Kolkata",
        "temperature_unit": "celsius"
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPError as error:
        print(f"Weather API request failed: {error}")
        return None

    _cache[cache_key] = (
        monotonic() + CACHE_TTL_SECONDS,
        data,
    )

    return data



if __name__ == "__main__":
    data = fetch_weather_data(
        latitude=26.12,
        longitude=85.39,
        start_date="2020-06-01",
        end_date="2020-06-10"
    )

    if data is not None:
        daily = data.get("daily", {})

        dates= daily.get("time", [])

        temperatures = daily.get("temperature_2m_max", [])

        #Exclude missing temperatures.
        valid_temperatures = [
            temperature
            for temperature in temperatures
            if temperature is not None
        ]

        print("Records received:", len(dates))
        print("Valid temperature records:", len(valid_temperatures))

        if valid_temperatures:
            average = sum(valid_temperatures)/len(valid_temperatures)
            highest = max(valid_temperatures)

            print("Average maximum temperature:", round(average, 2))
            print("Highest maximum temperature:", highest)
        else:
            print("No valid temperature records available.")

        for date,temperature in zip(dates, temperatures):
            print(date, temperature)