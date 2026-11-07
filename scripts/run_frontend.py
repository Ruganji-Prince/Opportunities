"""Local helper for the portable Node installation on Windows."""
from pathlib import Path
import os
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
node=next((root/'.tools').glob('node-*-win-x64'))
env=os.environ.copy();env['PATH']=str(node)+os.pathsep+env['PATH']
args=sys.argv[1:] or ['run','build']
raise SystemExit(subprocess.call([str(node/'node.exe'),str(node/'node_modules/npm/bin/npm-cli.js'),*args],cwd=root/'frontend',env=env))
