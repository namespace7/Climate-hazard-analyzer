from analyze_climate import summarise_events_by_year

def test_includes_years_with_zero_events():
    events = [
        {
            "start_date": "1990-06-01",
            "end_date": "1990-06-03",
            "duration": 3,
        },
        {
            "start_date": "1992-07-01",
            "end_date": "1992-07-05",
            "duration": 5,
        }
    ]

    result = summarise_events_by_year(
        events,
        "1990-01-01",
        "1993-12-31",
    )

    assert len(result) == 4
    assert result[0]["year"] == 1990
    assert result[0]["event_count"] == 1
    assert result[1]["year"] == 1991
    assert result[1]["event_count"] == 0
    assert result[1]["total_heatwave_days"] == 0
    assert result[2]["year"] == 1992
    assert result[2]["total_heatwave_days"] == 5
    assert result[3]["year"] == 1993
    assert result[3]["event_count"] == 0