"""One incident issue; recovery closes it. No duplicate unchanged notifications."""
import json
import os
from pathlib import Path
import subprocess

TITLE = 'BiznTools public availability check needs attention'

def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)

if __name__ == '__main__':
    path = Path('status/latest.json')
    if not path.exists():
        raise SystemExit('Probe did not produce an observation; inspect the workflow failure.')
    row = json.loads(path.read_text())
    issues = json.loads(gh('issue', 'list', '--state', 'open', '--json', 'number,title,author', '--limit', '100'))
    issue = next((i for i in issues if i['title'] == TITLE and i['author']['login'] in ('github-actions[bot]', 'github-actions', 'app/github-actions')), None)
    run = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    if row['healthy']:
        if issue:
            gh('issue', 'close', str(issue['number']), '--comment', f"The checks passed at {row['at_utc']}. Observation: {run}. Root cause is not inferred from this recovery.")
    elif not issue:
        details = '\n'.join(f"- {r['url']}: {r.get('error', 'failed check')}" for r in row['failures'])
        body = f"Both bounded attempts failed at {row['at_utc']}.\n\n{details}\n\nWorkflow: {run}\n\nThis is a GitHub runner observation. Confirm from a second network and inspect DNS, TLS and provider state before attributing a global outage. No automatic production mutation is performed."
        gh('issue', 'create', '--title', TITLE, '--body', body)
    elif row['event'] == 'incident_changed':
        gh('issue', 'comment', str(issue['number']), '--body', f"The failure pattern changed at {row['at_utc']}. Inspect {run}.")
