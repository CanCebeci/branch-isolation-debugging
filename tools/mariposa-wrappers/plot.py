import sys

import matplotlib.pyplot as plt

# Take the name of the query as a command-line argument

if len(sys.argv) != 2:
    print("Usage: python plot.py <query_name>")
    sys.exit(1)

query_name = sys.argv[1]

# Read data from time.txt
with open('time.txt', 'r') as file:
    data = file.readlines()

# Convert data to float
data = [float(line.strip()) / 1000 for line in data]

# Plot histogram
plt.hist(data, bins=50, edgecolor='black')
plt.xlabel('Time (seconds)')
plt.ylabel('Frequency')
plt.title(f'Histogram of time to solve `{query_name}`')
# plt.show()
# Save the plot as a PDF file
plt.savefig('histogram.pdf')