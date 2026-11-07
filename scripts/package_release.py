"""Commit the prepared local source and export source/build ZIP artifacts."""
from pathlib import Path
import shutil
import subprocess
import zipfile

root=Path(__file__).resolve().parents[1]
git=shutil.which('git') or str(root/'.tools/git/cmd/git.exe')
base=[git,'-c',f'safe.directory={root.as_posix()}','-C',str(root)]
subprocess.run([*base,'rm','--cached','--ignore-unmatch','frontend/tsconfig.tsbuildinfo'],check=True)
subprocess.run([*base,'add','-A'],check=True)
subprocess.run([*base,'diff','--cached','--check'],check=True)
tracked=subprocess.check_output([*base,'ls-files','-z']).decode().split('\0')
for name in filter(None,tracked):
    assert not name.startswith(('.tools/','private/','frontend/node_modules/'))
    assert name!='.env' and not name.endswith(('.pdf','.docx'))
if subprocess.run([*base,'diff','--cached','--quiet']).returncode:
    subprocess.run([*base,'commit','-m','Finalize verified feeds, conservative eligibility, browser QA and publication docs'],check=True)
source=root.parent/'OpportunityRadar-source.zip'
subprocess.run([*base,'archive','--format=zip',f'--output={source}','HEAD'],check=True)
build=root.parent/'OpportunityRadar-dashboard.zip'
with zipfile.ZipFile(build,'w',zipfile.ZIP_DEFLATED) as archive:
    for file in (root/'frontend/dist').rglob('*'):
        if file.is_file():archive.write(file,file.relative_to(root/'frontend/dist'))
subprocess.run([*base,'status','--short'],check=True)
print('Source:',source)
print('Static dashboard:',build)
subprocess.run([*base,'log','-1','--format=%h %s'],check=True)
