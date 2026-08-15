def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def calculate_average(total, count):
    if count == 0:
        raise ValueError("Cannot calculate average with zero count")
    return total / count


result = divide(10, 2)
print("Result:", result)

average = calculate_average(100, 10)
print("Average:", average)