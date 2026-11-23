def calculate(operation: str, numbers: list[float]) -> float:
    """Do one simple calculation on a list of numbers.

    operations: add, multiply, average, difference (a - b), divide (a / b),
    percent_change (from a to b), percent_of (a as a percent of b)
    """
    if not numbers:
        raise ValueError("There are no numbers to calculate.")

    if operation == "add":
        result = sum(numbers)
    elif operation == "multiply":
        result = 1
        for n in numbers:
            result *= n
    elif operation == "average":
        result = sum(numbers) / len(numbers)
    elif operation in ("difference", "divide", "percent_change", "percent_of"):
        if len(numbers) != 2:
            raise ValueError(f"{operation} needs exactly 2 numbers.")
        a, b = numbers
        if operation == "difference":
            result = a - b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero.")
            result = a / b
        elif operation == "percent_change":
            if a == 0:
                raise ValueError("Cannot calculate a percent change from zero.")
            result = (b - a) / a * 100
        else:
            if b == 0:
                raise ValueError("Cannot divide by zero.")
            result = a / b * 100
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return round(result, 4)
