import random
import math


# A large class with many methods and too many responsibilities
class SuperCalculator:
    def __init__(self):
        self.history = []

    def add(self, x, y):
        result = x + y
        self.history.append(f"Add: {x} + {y} = {result}")
        return result

    def subtract(self, x, y):
        result = x - y
        self.history.append(f"Subtract: {x} - {y} = {result}")
        return result

    def multiply(self, x, y):
        result = x * y
        self.history.append(f"Multiply: {x} * {y} = {result}")
        return result

    def divide(self, x, y):
        if y == 0:
            return "Error: Division by Zero"
        result = x / y
        self.history.append(f"Divide: {x} / {y} = {result}")
        return result

    def power(self, x, y):
        result = x ** y
        self.history.append(f"Power: {x} ** {y} = {result}")
        return result

    def sqrt(self, x):
        if x < 0:
            return "Error: Negative number cannot have a square root"
        result = math.sqrt(x)
        self.history.append(f"Sqrt: sqrt({x}) = {result}")
        return result

    def get_history(self):
        return self.history


# A function with too many parameters (over 5)
def calculate_statistics(numbers, mean=False, median=False, mode=False, standard_deviation=False, range_=False):
    if mean:
        print(f"Mean: {sum(numbers)/len(numbers)}")
    if median:
        numbers.sort()
        length = len(numbers)
        if length % 2 == 0:
            median_value = (numbers[length // 2 - 1] + numbers[length // 2]) / 2
        else:
            median_value = numbers[length // 2]
        print(f"Median: {median_value}")
    if mode:
        mode_value = max(set(numbers), key=numbers.count)
        print(f"Mode: {mode_value}")
    if standard_deviation:
        mean_value = sum(numbers) / len(numbers)
        variance = sum((x - mean_value) ** 2 for x in numbers) / len(numbers)
        print(f"Standard Deviation: {math.sqrt(variance)}")
    if range_:
        print(f"Range: {max(numbers) - min(numbers)}")


# A nested function with excessive nesting
def complex_calculation():
    x = random.randint(1, 10)
    y = random.randint(1, 10)

    if x > 5:
        if y > 5:
            if x + y > 15:
                result = x * y
            else:
                result = x + y
        else:
            if x - y < 2:
                result = x / y
            else:
                result = x + y * y
    else:
        if y < 3:
            if x * y < 5:
                result = x + y
            else:
                result = x - y
        else:
            result = x + y
    return result


# A class with deep inheritance
class Shape:
    def __init__(self, name):
        self.name = name

    def area(self):
        raise NotImplementedError("Subclasses should implement this method")

    def perimeter(self):
        raise NotImplementedError("Subclasses should implement this method")


class Rectangle(Shape):
    def __init__(self, width, height):
        super().__init__("Rectangle")
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)


class Square(Rectangle):
    def __init__(self, side):
        super().__init__(side, side)

    def area(self):
        return self.width ** 2


class Cube(Square):
    def __init__(self, side):
        super().__init__(side)

    def volume(self):
        return self.width ** 3


# A function with duplicate code and long body
def compute_values():
    x = random.randint(1, 10)
    y = random.randint(1, 10)
    z = random.randint(1, 10)

    sum_xy = x + y
    sum_yz = y + z
    sum_xz = x + z

    print(f"Sum of {x} and {y} is {sum_xy}")
    print(f"Sum of {y} and {z} is {sum_yz}")
    print(f"Sum of {x} and {z} is {sum_xz}")
    
    # Duplicated logic here, computing sum in multiple places
    sum_xy = x + y
    sum_yz = y + z
    sum_xz = x + z

    print(f"Sum of {x} and {y} again is {sum_xy}")
    print(f"Sum of {y} and {z} again is {sum_yz}")
    print(f"Sum of {x} and {z} again is {sum_xz}")

    return sum_xy, sum_yz, sum_xz


# Code with nested loops that can be complex
def nested_loops_example():
    for i in range(10):
        for j in range(10):
            for k in range(10):
                print(f"i: {i}, j: {j}, k: {k}")
                if i == j and j == k:
                    print(f"Special condition met: i = j = k = {i}")
                    return


# Another function with unnecessary parameters and complexity
def more_complex_function(a, b, c, d, e, f, g, h):
    if a > b:
        if c > d:
            return a + b
        else:
            return c + d
    elif e > f:
        if g > h:
            return e + f
        else:
            return g + h
    return a * b


# Calling functions to simulate complex flow
if __name__ == "__main__":
    sc = SuperCalculator()
    sc.add(1, 2)
    sc.subtract(10, 5)
    sc.multiply(3, 4)
    sc.divide(8, 2)
    sc.power(2, 3)
    sc.sqrt(16)
    sc.get_history()

    numbers = [random.randint(1, 100) for _ in range(100)]
    calculate_statistics(numbers, mean=True, median=True, mode=True, standard_deviation=True, range_=True)
    complex_calculation()
    
    shape = Rectangle(4, 5)
    print(f"Area of rectangle: {shape.area()}")

    cube = Cube(3)
    print(f"Volume of cube: {cube.volume()}")
    
    compute_values()
    nested_loops_example()
    more_complex_function(1, 2, 3, 4, 5, 6, 7, 8)
