import json
from pathlib import Path

row = json.loads(Path('status/latest.json').read_text())
print('# BiznTools availability')
print(f"\nObserved: {row['at_utc']}\n\nHealthy: {row['healthy']} · Event: {row['event']}\n")
interval = row.get('seconds_since_previous_observation')
if interval is not None:
    hours, remainder = divmod(interval, 3600)
    print(f"Time since the previous recorded probe: {hours}h {remainder // 60}m {remainder % 60}s.")
    if interval >= 7200:
        print("The interval spans at least two hourly check periods. Site availability between the two observations is unknown.")
    print()
for check in row['checks']:
    print(f"- {'PASS' if check['ok'] else 'FAIL'} {check['url']}: {check.get('status', check.get('error', 'unknown'))}")
print('\nA probe result is one network observation, not proof of global reachability or a hosting root cause.')
