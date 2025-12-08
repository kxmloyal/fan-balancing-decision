data = open('templates/index.html', 'r', encoding='utf-8').read()

# Count occurrences
if_count = data.count('{% if')
endif_count = data.count('{% endif %}')

print('Number of if tags: {}'.format(if_count))
print('Number of endif tags: {}'.format(endif_count))

# Find all if and endif positions
lines = data.split('\n')
if_positions = []
endif_positions = []

for i, line in enumerate(lines):
    if '{% if' in line:
        if_positions.append((i+1, line.strip()))
    if '{% endif %}' in line:
        endif_positions.append((i+1, line.strip()))

print("\nIF statements:")
for pos, line in if_positions:
    print("  Line {}: {}".format(pos, line))

print("\nENDIF statements:")
for pos, line in endif_positions:
    print("  Line {}: {}".format(pos, line))

print("\nDifference: {} unclosed if blocks".format(len(if_positions) - len(endif_positions)))
