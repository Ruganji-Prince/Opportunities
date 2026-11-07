"""Download a verified portable Node LTS into ignored .tools (no global install)."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

root = Path(__file__).resolve().parents[1]
versions = json.load(urllib.request.urlopen('https://nodejs.org/dist/index.json', timeout=30))
version = next(v['version'] for v in versions if v['lts'] and v['version'].startswith('v22.'))
name = f'node-{version}-win-x64.zip'
base = f'https://nodejs.org/dist/{version}/'
payload = urllib.request.urlopen(base + name, timeout=120).read()
checksums = urllib.request.urlopen(base + 'SHASUMS256.txt', timeout=30).read().decode()
expected = next(line.split()[0] for line in checksums.splitlines() if line.endswith('  ' + name))
assert hashlib.sha256(payload).hexdigest() == expected, 'Node checksum mismatch'
directory = root / '.tools'
directory.mkdir(exist_ok=True)
archive = directory / name
archive.write_bytes(payload)
with zipfile.ZipFile(archive) as z:
    z.extractall(directory)
print(directory / f'node-{version}-win-x64')
