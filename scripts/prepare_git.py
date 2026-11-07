"""Optional Windows helper: prepare a local commit with portable MinGit."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
import zipfile

root=Path(__file__).resolve().parents[1]
directory=root/'.tools/git'
git=directory/'cmd/git.exe'
if not git.exists():
    request=urllib.request.Request('https://api.github.com/repos/git-for-windows/git/releases/latest',headers={'User-Agent':'OpportunityRadar-setup'})
    release=json.load(urllib.request.urlopen(request,timeout=30))
    asset=next(a for a in release['assets'] if a['name'].startswith('MinGit-') and a['name'].endswith('-64-bit.zip') and 'busybox' not in a['name'])
    payload=urllib.request.urlopen(asset['browser_download_url'],timeout=120).read()
    digest=asset.get('digest')
    if not digest or digest!='sha256:'+hashlib.sha256(payload).hexdigest(): raise RuntimeError('MinGit release asset checksum did not verify')
    directory.mkdir(parents=True,exist_ok=True)
    archive=directory/'download.zip';archive.write_bytes(payload)
    with zipfile.ZipFile(archive) as z:z.extractall(directory)
base=[str(git),'-c',f'safe.directory={root.as_posix()}','-C',str(root)]
def run(*args):subprocess.run([*base,*args],check=True)
if not (root/'.git').exists():run('init','-b','main')
run('config','user.name','Ruganji-Prince')
run('config','user.email','240843418+Ruganji-Prince@users.noreply.github.com')
run('add','.')
changed=subprocess.run([*base,'diff','--cached','--quiet']).returncode
if changed:run('commit','-m','Build OpportunityRadar collection, matching, deadline dashboard and automation')
remotes=subprocess.check_output([*base,'remote']).decode().splitlines()
if 'origin' not in remotes:run('remote','add','origin','https://github.com/Ruganji-Prince/Opportunities.git')
run('status','--short')
run('log','-1','--format=%h %s')
