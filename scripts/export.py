"""Reapply local profile/ranking rules to cached data without network requests."""
import sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.pipeline import ROOT,validate
from src.storage import read,write
from src.core import relevant,match,deadline_status,sort_key,deduplicate
profile=read(ROOT/'config/profile.yaml',{});weights=read(ROOT/'config/scoring.yaml',{})
now=datetime.now(timezone.utc);active=[];archived=[]
for o in deduplicate(read(ROOT/'data/opportunities.json',[])+read(ROOT/'data/archived_opportunities.json',[])):
    o=match(o,profile,weights)
    if not relevant(o):continue
    o['deadline_status']=deadline_status(o,now)
    (archived if o['deadline_status'] in ('Expired','Closed') else active).append(o)
for name,items in [('opportunities',active),('archived_opportunities',archived)]:write(ROOT/f'data/{name}.json',sorted(items,key=sort_key))
status=read(ROOT/'data/refresh_status.json',{})
status.update(active=len(active),archived=len(archived),local_rules_reapplied=now.isoformat())
write(ROOT/'data/refresh_status.json',status)
print('Cached records validated:',validate())
