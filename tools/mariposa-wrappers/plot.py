import sys
import csv
import os

import matplotlib.pyplot as plt

# Take the name of the CSV file as a command-line argument

if len(sys.argv) != 2:
    print("Usage: python plot.py <csv_file>")
    sys.exit(1)

csv_file = sys.argv[1]

# Check if file exists
if not os.path.exists(csv_file):
    print(f"Error: File '{csv_file}' not found")
    sys.exit(1)

# Read data from CSV file
data = []
with open(csv_file, 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Extract elapsed_milli and convert to seconds
        elapsed_milli = float(row['elapsed_milli'])
        data.append(elapsed_milli / 1000)

# Extract query name from filename (remove .csv extension and path)
query_name = os.path.basename(csv_file).replace('.csv', '')

# Plot histogram
plt.hist(data, bins=50, edgecolor='black')
plt.xlabel('Time (seconds)')
plt.ylabel('Frequency')
plt.title(f'Histogram of time to solve `{query_name}`')
# plt.show()
# Save the plot as a PDF file
plt.savefig(f'{query_name}.histogram.pdf')