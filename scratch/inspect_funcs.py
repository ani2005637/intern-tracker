with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

for idx, line in enumerate(lines, 1):
    if 'dash-stat' in line or 'stat-card' in line or 'stats-grid' in line or 'Total Interns' in line or 'total-hours' in line:
        print(f"Line {idx}: {line}")
