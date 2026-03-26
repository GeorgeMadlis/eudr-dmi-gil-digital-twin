import re
import json
import ssl
import socket
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed

REPOS = [
    Path('/Users/server/projects/eudr-dmi-gil'),
    Path('/Users/server/projects/eudr-dmi-gil-digital-twin'),
]

md_link_re = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
bare_url_re = re.compile(r'(?<!\()(?<!<)(https?://[^\s)>]+)')


def normalize_url(raw: str) -> str:
    cleaned = raw.strip().strip('<>').strip()
    cleaned = cleaned.rstrip('.,;:!?')
    cleaned = cleaned.rstrip('`')
    cleaned = cleaned.rstrip('"')
    cleaned = cleaned.rstrip("'")
    cleaned = cleaned.rstrip(']')
    cleaned = cleaned.rstrip(')')
    cleaned = cleaned.rstrip('}')
    return cleaned

urls_to_sources = {}

for repo in REPOS:
    for md in repo.rglob('*.md'):
        if '.git' in md.parts or '.venv' in md.parts or 'build' in md.parts or 'out' in md.parts:
            continue
        text = md.read_text(encoding='utf-8', errors='ignore')

        for raw in md_link_re.findall(text):
            link = normalize_url(raw)
            if link.startswith(('http://', 'https://')):
                link = link.split('#', 1)[0]
                urls_to_sources.setdefault(link, set()).add(str(md))

        for raw in bare_url_re.findall(text):
            link = normalize_url(raw).split('#', 1)[0]
            if link.startswith(('http://', 'https://')):
                urls_to_sources.setdefault(link, set()).add(str(md))

urls = sorted(urls_to_sources.keys())
ctx = ssl.create_default_context()


def check_url(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; EUDR-Docs-LinkCheck/1.0)',
        'Accept': '*/*',
    }
    try:
        req = Request(url, headers=headers, method='HEAD')
        with urlopen(req, timeout=12, context=ctx) as response:
            return (url, True, getattr(response, 'status', 200), None)
    except HTTPError as err:
        if err.code in (403, 405):
            try:
                req2 = Request(url, headers=headers, method='GET')
                with urlopen(req2, timeout=12, context=ctx) as response2:
                    return (url, True, getattr(response2, 'status', 200), f'HEAD->{err.code}, GET ok')
            except Exception as err2:
                return (url, False, None, f'HEAD->{err.code}; GET failed: {type(err2).__name__}: {err2}')
        return (url, False, err.code, f'HTTPError: {err}')
    except (URLError, socket.timeout, ssl.SSLError) as err:
        try:
            req2 = Request(url, headers=headers, method='GET')
            with urlopen(req2, timeout=12, context=ctx) as response2:
                return (url, True, getattr(response2, 'status', 200), f'HEAD failed ({type(err).__name__}), GET ok')
        except Exception as err2:
            return (url, False, None, f'{type(err).__name__}: {err}; GET failed: {type(err2).__name__}: {err2}')
    except Exception as err:
        return (url, False, None, f'{type(err).__name__}: {err}')

results = []
with ThreadPoolExecutor(max_workers=16) as executor:
    futures = [executor.submit(check_url, url) for url in urls]
    for future in as_completed(futures):
        results.append(future.result())

results.sort(key=lambda item: item[0])
failed = [item for item in results if not item[1]]
passed = [item for item in results if item[1]]

report = {
    'total_unique_urls': len(urls),
    'passed': len(passed),
    'failed': len(failed),
    'failures': [
        {
            'url': url,
            'status': status,
            'error': error,
            'sources': sorted(urls_to_sources.get(url, [])),
        }
        for (url, _ok, status, error) in failed
    ],
}

out = Path('/Users/server/projects/eudr-dmi-gil-digital-twin/docs/link_check_strict.json')
out.write_text(json.dumps(report, indent=2), encoding='utf-8')

print(f'Checked unique external URLs: {len(urls)}')
print(f'Passed: {len(passed)}')
print(f'Failed: {len(failed)}')
print(f'Wrote report: {out}')

if failed:
    print('\nTop failures:')
    for (url, _ok, _status, error) in failed[:20]:
        print(f'- {url} :: {error}')
