#!/usr/bin/env python3
"""
End-to-end test to verify the data flow from CSV to frontend
"""
import json
import html
from data_processing import parse_single_surface_file
from chart_generation import generate_chart_data

# Test with the sample CSV file
print("Testing end-to-end data flow...")

# Step 1: Parse the CSV file
print("\nStep 1: Parsing CSV file...")
try:
    parsed_data = parse_single_surface_file('test_data.csv')
    print(f"Parsed data keys: {list(parsed_data.keys())}")
    print(f"First speed data: {list(parsed_data.keys())[0]} -> {parsed_data[list(parsed_data.keys())[0]]}")
except Exception as e:
    print(f"Error parsing CSV: {e}")
    exit(1)

# Step 2: Convert parsed data to chart data format
print("\nStep 2: Converting to chart data format...")
chart_input_data = []
for speed, values in parsed_data.items():
    for value in values:
        chart_input_data.append({"转速": speed, "不平衡量": value})

# Step 3: Generate box plot data
print("\nStep 3: Generating box plot data...")
box_data = generate_chart_data(chart_input_data, "box")
print(f"Generated box plot data: {len(box_data)} items")
for item in box_data:
    print(f"  - Name: {item['name']}, Data: {item['data']}")

# Step 4: Simulate HTML escaping (as done in generate_generic_charts)
print("\nStep 4: Simulating HTML escaping...")
json_str = json.dumps(box_data)
print(f"JSON string before escaping: {json_str}")

html_escaped = html.escape(json_str)
print(f"JSON string after escaping: {html_escaped}")

# Step 5: Simulate frontend parsing
print("\nStep 5: Simulating frontend parsing...")
# This is what happens in the frontend:
# const data = JSON.parse(chartData);
try:
    parsed_frontend = json.loads(html_escaped)
    print(f"Frontend parsed data: {len(parsed_frontend)} items")
    for item in parsed_frontend:
        print(f"  - Name: {item['name']}, Data: {item['data']}")
except Exception as e:
    print(f"Error parsing in frontend: {e}")

print("\nEnd-to-end test completed!")
