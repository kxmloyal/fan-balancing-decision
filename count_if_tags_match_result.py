import re

# Read the match_result.html file
with open('templates/match_result.html', 'r', encoding='utf-8') as f:
    data = f.read()

# Count occurrences of if and endif tags
if_count = len(re.findall(r'{%\s*if\s+.*?%}', data))
endif_count = len(re.findall(r'{%\s*endif\s*%}', data))

print(f"Number of if tags: {if_count}")
print(f"Number of endif tags: {endif_count}")

# Extract all if statements
if_statements = []
for i, line in enumerate(data.split('\n'), 1):
    if re.search(r'{%\s*if\s+.*?%}', line):
        if_statements.append(f"  Line {i}: {line.strip()}")

# Extract all endif statements
endif_statements = []
for i, line in enumerate(data.split('\n'), 1):
    if re.search(r'{%\s*endif\s*%}', line):
        endif_statements.append(f"  Line {i}: {line.strip()}")

# Print all if statements
print("\nIF statements:")
for stmt in if_statements:
    print(stmt)

# Print all endif statements
print("\nENDIF statements:")
for stmt in endif_statements:
    print(stmt)

# Calculate difference
diff = if_count - endif_count
print(f"\nDifference: {diff} unclosed if blocks")