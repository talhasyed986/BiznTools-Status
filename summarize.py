import json
from pathlib import Path

row = json.loads(Path('status/latest.json').read_text())
print('# BiznTools availability')
print(f"\nObserved: {row['at_utc']}\n\nHealthy: {row['healthy']} · Event: {row['event']}\n")
for check in row['checks']:
    print(f"- {'PASS' if check['ok'] else 'FAIL'} {check['url']}: {check.get('status', check.get('error', 'unknown'))}")
print('\nA probe result is one network observation, not proof of global reachability or a hosting root cause.')
