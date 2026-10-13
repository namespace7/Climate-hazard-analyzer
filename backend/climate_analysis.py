def calculate_average(temperatures):
    if not temperatures:
        return None

    return sum(temperatures)/len(temperatures)

def find_highest_temperature(temperatures):
    if not temperatures:
        return None

    return max(temperatures)


def count_hot_days(temperatures):
    total = 0

    for temperature in temperatures:
        if temperature > 38:
            total += 1

    return total


temperatures = [36, 39, 41, 38, 40, 35, 42]


print("Average:", calculate_average(temperatures))
print("Highest:", find_highest_temperature(temperatures))
print("Hot days:", count_hot_days(temperatures))