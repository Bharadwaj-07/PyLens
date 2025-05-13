import time
import random
import os

def generate_random_list(size):
    return [random.randint(0, 100000) for _ in range(size)]

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def matrix_multiply(a, b):
    result = [[0]*len(b[0]) for _ in range(len(a))]
    for i in range(len(a)):
        for j in range(len(b[0])):
            for k in range(len(b)):
                result[i][j] += a[i][k] * b[k][j]
    return result

def simulate_file_io(filename, lines=1000):
    with open(filename, 'w') as f:
        for i in range(lines):
            f.write(f"Line {i}: {random.random()}\n")
    with open(filename, 'r') as f:
        _ = f.readlines()
    os.remove(filename)

def cpu_bound_task():
    print("Sorting...")
    arr = generate_random_list(1000)
    bubble_sort(arr)
    
    print("Calculating Fibonacci...")
    fib = fibonacci(25)  # recursive and slow
    print("Fibonacci(25):", fib)

def io_bound_task():
    print("Simulating file I/O...")
    simulate_file_io("tempfile.txt")

def matrix_task():
    print("Performing matrix multiplication...")
    a = [[random.randint(0, 10) for _ in range(50)] for _ in range(50)]
    b = [[random.randint(0, 10) for _ in range(50)] for _ in range(50)]
    result = matrix_multiply(a, b)
    print("Matrix multiplication done.")

def sleep_task():
    print("Sleeping for a bit...")
    time.sleep(3)

def main():
    start = time.time()
    cpu_bound_task()
    io_bound_task()
    matrix_task()
    sleep_task()
    end = time.time()
    print(f"\nTotal execution time: {end - start:.2f} seconds")

if __name__ == "__main__":
    main()
