import numpy as np

def calculate_heatwave_threshold(temperatures):
    valid_temperatures = [
        temperature
        for temperature in temperatures
        if temperature is not None
    ]

    if not valid_temperatures:
        raise ValueError("No valid temperatures available")

    return float(np.percentile(valid_temperatures, 95))

if __name__ == "__main__":
    temperatures = [
        30, 31, 32, 33, 34, 35, 36, 37, 38, 40,
        31, 32, 33, 34, 35, 36, 37, 38, 39, 41
    ]

    threshold = calculate_heatwave_threshold(temperatures)

    print("95th percentile threshold:", round(threshold, 2))