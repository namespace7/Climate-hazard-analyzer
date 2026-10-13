from scipy.stats import linregress

def calculate_heatwave_trend(annual_statistics):
    """
    Estimate the linear trend in annual heatwave days.
    the slope is measured in heatwave days per year.
    """
    if len(annual_statistics) < 2:
        raise ValueError("At least two years are required")

    years = [item["year"] for item in annual_statistics]
    heatwave_days = [
        item["total_heatwave_days"]
        for item in annual_statistics
    ]

    result = linregress(years, heatwave_days)

    if result.slope > 0:
        direction = "increasing"
    elif result.slope < 0:
        direction = "decreasing"
    else:
        direction = "no_change"

    return {
        "slope_days_per_year": round(result.slope, 4),
        "direction": direction,
        "p_value": round(result.pvalue, 4),
        "r_squared": round(result.rvalue ** 2, 4),
    }