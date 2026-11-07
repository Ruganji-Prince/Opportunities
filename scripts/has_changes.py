"""Exit 0 for meaningful changes, 1 for timestamp/count-only refresh changes."""
import json
from pathlib import Path
import sys
VOLATILE={'last_verified','last_attempt','last_successful_refresh','checked_at','last_success','new','modified','expired','notifications'}
def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in VOLATILE}
    if isinstance(value,list):return [clean(v) for v in value]
    return value
def snapshot(folder):return {p.name:clean(json.loads(p.read_text(encoding='utf-8'))) for p in Path(folder).glob('*.json')}
if __name__=='__main__': raise SystemExit(0 if snapshot(sys.argv[1])!=snapshot(sys.argv[2]) else 1)
