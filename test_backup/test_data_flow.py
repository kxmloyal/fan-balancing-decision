#!/usr/bin/env python3
import csv
import json
from chart_generation import generate_chart_data

# Read test data from CSV
with open('test_data.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)
    data = []
    for row in reader:
        for i, value in enumerate(row):
            if i < len(headers):
                speed = headers[i]
                data.append({"转速": speed, "不平衡量": float(value)})

print(f"Test data loaded: {len(data)} entries")
print(f"Speed values found: {set(item['转速'] for item in data)}")

# Test box plot data generation
print("\nTesting box plot data generation...")
box_data = generate_chart_data(data, "box")
print(f"Generated box plot data: {len(box_data)} items")
for item in box_data:
    print(f"  - Name: {item['name']}, Data: {item['data']}")

# Test trend plot data generation
print("\nTesting trend plot data generation...")
trend_data = generate_chart_data(data, "trend")
print(f"Generated trend plot data: {len(trend_data)} items")
for item in trend_data:
    print(f"  - Name: {item['name']}, Value: {item['value']}")

# Test scatter plot data generation
print("\nTesting scatter plot data generation...")
scatter_data = generate_chart_data(data, "scatter")
print(f"Generated scatter plot data: {len(scatter_data)} items")
for i, item in enumerate(scatter_data[:5]):  # Show first 5 items
    print(f"  - {item}")
if len(scatter_data) > 5:
    print(f"  ... and {len(scatter_data) - 5} more items")
