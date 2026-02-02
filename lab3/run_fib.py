import os

# Get user input
core = input("Enter CPU core (0 or 1): ").strip()

# Validate input
if core not in ("0", "1"):
    print("Error: input must be 0 or 1")
    exit(1)

# Build the command using taskset
command = f"taskset -c {core} python3 fib.py"

print(f"Running fib.py on CPU core {core}...")
os.system(command)

