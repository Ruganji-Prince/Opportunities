"""Exit 0 for meaningful changes, 1 for timestamp/count-only refresh changes."""
import json
from pathlib import Path
import sys
VOLATILE={'last_verified','reviewed_at','last_attempt','last_successful_refresh','checked_at','last_success','new','modified','expired','notifications'}
def clean(value):
    if isinstance(value,str) and value.startswith('HTTP GET succeeded'):return value.split('20')[0].strip()
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in VOLATILE}
    if isinstance(value,list):return [clean(v) for v in value]
    return value
def snapshot(folder):return {p.name:clean(json.loads(p.read_text(encoding='utf-8'))) for p in Path(folder).glob('*.json')}
def changed(before,after):
    if snapshot(before)!=snapshot(after):return True
    # Publish a daily health refresh even when listings are unchanged, so freshness
    # remains honest without six-hour timestamp-only commits.
    from datetime import datetime
    old=json.loads((Path(before)/'refresh_status.json').read_text())
    new=json.loads((Path(after)/'refresh_status.json').read_text())
    a=old.get('last_successful_refresh');b=new.get('last_successful_refresh')
    return bool(a and b and (datetime.fromisoformat(b)-datetime.fromisoformat(a)).total_seconds()>=86400)
if __name__=='__main__':raise SystemExit(0 if changed(sys.argv[1],sys.argv[2]) else 1)
