
from math import isfinite, sqrt

from scipy.stats import norm


def calculate_mann_kendall_trend(values, alpha=0.05):
    """
    Detect a monotonic trend in an ordered time series.

    Args:
        values: Ordered numeric observations, such as annual
                heatwave-day counts.
        alpha: Significance level, default 0.05.

    Returns:
        S statistic, standardized Z statistic, Kendall's tau,
        p-value, and trend direction.
    """
    observations = [
        float(value)
        for value in values
        if value is not None and isfinite(float(value))
    ]

    n = len(observations)

    if n < 2:
        return {
            "s_statistic": 0,
            "z_statistic": 0.0,
            "kendall_tau": 0.0,
            "p_value": 1.0,
            "direction": "no significant trend",
            "alpha": alpha,
        }

    # Calculate S by comparing every pair of observations.
    s_statistic = 0

    for i in range(n - 1):
        for j in range(i + 1, n):
            if observations[j] > observations[i]:
                s_statistic += 1
            elif observations[j] < observations[i]:
                s_statistic -= 1

    # Count tied values to correct the variance.
    tie_counts = {}
    for value in observations:
        tie_counts[value] = tie_counts.get(value, 0) + 1

    tie_correction = sum(
        count * (count - 1) * (2 * count + 5)
        for count in tie_counts.values()
        if count > 1
    )

    variance = (
        n * (n - 1) * (2 * n + 5) - tie_correction
    ) / 18

    denominator = n * (n - 1) / 2
    kendall_tau = s_statistic / denominator

    if variance <= 0:
        z_statistic = 0.0
        p_value = 1.0
    else:
        standard_deviation = sqrt(variance)

        # Continuity correction for the normal approximation.
        if s_statistic > 0:
            z_statistic = (
                s_statistic - 1
            ) / standard_deviation
        elif s_statistic < 0:
            z_statistic = (
                s_statistic + 1
            ) / standard_deviation
        else:
            z_statistic = 0.0

        p_value = float(
            2 * norm.sf(abs(z_statistic))
        )

    if p_value < alpha and s_statistic > 0:
        direction = "increasing"
    elif p_value < alpha and s_statistic < 0:
        direction = "decreasing"
    else:
        direction = "no significant trend"

    return {
        "s_statistic": int(s_statistic),
        "z_statistic": float(z_statistic),
        "kendall_tau": float(kendall_tau),
        "p_value": p_value,
        "direction": direction,
        "alpha": alpha,
    }
