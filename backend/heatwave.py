from datetime import date, timedelta

def detect_heatwaves(dates, temperatures, threshold, min_duration=3):
    if len(dates) != len(temperatures):
        raise ValueError("Dates and temperatures must have equal lengths")

    events = []
    start_date = None
    previous_date = None
    duration = 0

    for date_text, temperature in zip(dates, temperatures):
        current_date = date.fromisoformat(date_text)

        # A missing value or a gap in dates ends the current sequence.
        consecutive = (
            previous_date is not None
            and current_date == previous_date + timedelta(days=1)
        )

        if temperature is None or (
            previous_date is not None and not consecutive
        ):
            if duration >= min_duration:
                events.append({
                    "start_date": start_date,
                    "end_date": previous_date.isoformat(),
                    "duration": duration
                })

            start_date = None
            duration = 0

        if temperature is not None and temperature > threshold:
            if duration == 0:
                start_date = date_text

            duration +=1

        else:
            if duration >= min_duration:
                events.append({
                    "start_date": start_date,
                    "end_date": previous_date.isoformat(),
                    "duration": duration
                })

            start_date = None
            duration = 0

        previous_date = current_date

    # Don't forget an event that continues through the final record.
    if duration >= min_duration:
        events.append({
            "start_date": start_date,
            "end_date": previous_date.isoformat(),
            "duration": duration
        })

    return events

if __name__ == "__main__":
    dates= [
        "2020-06-01",
        "2020-06-02",
        "2020-06-03",
        "2020-06-04",
        "2020-06-05",
        "2020-06-06"
    ]

    temperatures = [39,40,41,35,39,40]

    events = detect_heatwaves(
        dates,
        temperatures,
        threshold=38
    )

    print("Heatwave events:", events)