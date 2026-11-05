"""Bounded public checks. No credentials, browser analytics, or server mutations."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlsplit, urljoin
import datetime, fcntl, hashlib, json, os, re, tempfile, time

ROOT = Path(os.environ.get('BIZNTOOLS_STATUS_DIR', Path(__file__).resolve().parent / 'status'))
ROOT.mkdir(parents=True, exist_ok=True)
ORIGIN = 'https://bizntools.com'
PAGES = [('/', 'Free Business Calculators'), ('/tools', 'BiznTools'),
         ('/inventory-operations/acres-per-hour-calculator', 'Acres Per Hour Calculator'),
         ('/documents/merge-pdf', 'Merge PDF')]

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def get_response(url):
    # Handle the production 308 explicitly; system Python versions differ.
    opener = build_opener(NoRedirect())
    for _ in range(5):
        try:
            return opener.open(Request(url, headers={
                'User-Agent': 'BiznTools-availability-check/1.0'}), timeout=12)
        except HTTPError as exc:
            if exc.code not in (301, 302, 303, 307, 308) or not exc.headers.get('Location'):
                raise
            target = urljoin(url, exc.headers['Location'])
            parsed = urlsplit(target)
            exc.close()
            if parsed.scheme != 'https' or parsed.netloc not in ('bizntools.com', 'www.bizntools.com'):
                raise ValueError('Unexpected redirect destination')
            url = target
    raise ValueError('Too many redirects')

def fetch(url, marker=None, content_type=None):
    started = time.monotonic()
    row = {'url': url, 'ok': False}
    try:
        with get_response(url) as response:
            body = response.read(2_000_001)
            row.update(status=response.status, final_url=response.url,
                       content_type=response.headers.get('Content-Type', ''))
            if response.status != 200:
                row['error'] = 'HTTP status is not 200'
            elif urlsplit(response.url).netloc != 'bizntools.com':
                row['error'] = 'Unexpected final host'
            elif len(body) > 2_000_000:
                row['error'] = 'Response exceeds probe size limit; review probe scope'
            elif marker and marker.encode() not in body:
                row['error'] = 'Expected page content missing'
            elif content_type and content_type not in row['content_type']:
                row['error'] = 'Unexpected content type'
            else:
                row['ok'] = True
        row['elapsed_seconds'] = round(time.monotonic() - started, 3)
        return row, body.decode('utf-8', errors='replace')
    except Exception as exc:
        if isinstance(exc, HTTPError): row['status'] = exc.code
        row['error'] = str(exc)[:300]
        row['elapsed_seconds'] = round(time.monotonic() - started, 3)
        return row, ''

def probe():
    jobs = [(ORIGIN + path, marker, 'text/html') for path, marker in PAGES]
    jobs += [('https://www.bizntools.com/', 'Free Business Calculators', 'text/html'),
             (ORIGIN + '/sitemap.xml', '<urlset', 'xml')]
    with ThreadPoolExecutor(max_workers=3) as pool:
        fetched = list(pool.map(lambda args: fetch(*args), jobs))
    rows = [row for row, _ in fetched]
    homepage = fetched[0][1]
    assets = []
    for kind, pattern, mime in [('script', r'<script[^>]+src="(/_next/static/[^\"]+\.js)"', 'javascript'),
                                ('stylesheet', r'<link[^>]+href="(/_next/static/[^\"]+\.css)"', 'text/css')]:
        match = re.search(pattern, homepage)
        if match:
            assets.append((ORIGIN + match[1], None, mime))
        else:
            rows.append({'url': ORIGIN + '/', 'check': kind, 'ok': False,
                         'error': 'Expected first-party asset reference missing'})
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows += [row for row, _ in pool.map(lambda args: fetch(*args), assets)]
    return rows

def classify(rows):
    failures = [row for row in rows if not row['ok']]
    signature = hashlib.sha256(json.dumps(sorted(
        (row['url'], row.get('check', ''), row.get('status'), row.get('error', ''))
        for row in failures), sort_keys=True).encode()).hexdigest() if failures else 'healthy'
    return {'healthy': not failures, 'signature': signature, 'failures': failures}

def event(previous, current):
    if not previous:
        return 'baseline_healthy' if current['healthy'] else 'incident_started'
    if previous['signature'] == current['signature']:
        return 'unchanged'
    if current['healthy']:
        return 'recovered'
    return 'incident_started' if previous['healthy'] else 'incident_changed'

def save(path, value):
    fd, name = tempfile.mkstemp(dir=ROOT, prefix='.probe-')
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(value, handle, indent=2); handle.write('\n')
            handle.flush(); os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

if __name__ == '__main__':
    with (ROOT / '.probe-lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        first = probe(); rows = first
        if not classify(first)['healthy']:
            time.sleep(3)
            rows = probe()
        current = classify(rows)
        prior_path = ROOT / 'state.json'
        previous = json.loads(prior_path.read_text()) if prior_path.exists() else None
        result = {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'event': event(previous, current), **current, 'checks': rows,
                  'retried': rows is not first, 'first_attempt': first if rows is not first else None}
        save(ROOT / 'latest.json', result)
        if result['event'] != 'unchanged':
            path = ROOT / 'events.json'
            history = json.loads(path.read_text()) if path.exists() else []
            save(path, (history + [result])[-200:])
        save(prior_path, {key: result[key] for key in ['at_utc', 'healthy', 'signature']})
        print(json.dumps({'at_utc': result['at_utc'], 'event': result['event'],
                          'healthy': result['healthy'], 'checked': len(rows),
                          'failures': result['failures'], 'retried': result['retried']}))
        raise SystemExit(0 if result['healthy'] else 1)
