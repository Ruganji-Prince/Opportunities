import argparse
from datetime import datetime,timezone
import logging
from pathlib import Path
import time
from .collectors import collect,fetch
from .core import normalize,match,deduplicate,deadline_status,sort_key,relevant
from .storage import read,write
from .notifications import notify

ROOT=Path(__file__).resolve().parents[1]
log=logging.getLogger('opportunityradar')

def refresh(root=ROOT, collector=collect, now=None, only=None):
    now=now or datetime.now(timezone.utc); stamp=now.isoformat()
    settings=read(root/'config/settings.yaml',{}); profile=read(root/'config/profile.yaml',{}); weights=read(root/'config/scoring.yaml',{})
    sources=read(root/'config/sources.yaml',[])
    previous=read(root/'data/opportunities.json',[])+read(root/'data/archived_opportunities.json',[])
    records={o['id']:o for o in previous if relevant(o)}; old={o['id']:o.copy() for o in previous}
    prior_status=read(root/'data/refresh_status.json',{})
    prior_health={s['id']:s for s in prior_status.get('sources',[])}
    health=[]; successes=0; new=0; modified=0
    for source in sources:
        state={**source,'checked_at':stamp,'status':'skipped','count':0,'last_success':prior_health.get(source['id'],{}).get('last_success')}
        if not source['enabled'] or (only and source['id'] not in only):
            state['message']='Not enabled or not selected'; health.append(state); continue
        if source['id']=='remotive' and state['last_success'] and (now-datetime.fromisoformat(state['last_success'])).total_seconds()<6*3600:
            state.update(status='cached',count=prior_health[source['id']].get('count',0),message='Six-hour minimum interval; retained last successful feed')
            health.append(state); successes+=1; continue
        try:
            # Stage a whole source before merging; partial failures never erase prior data.
            staged=[]
            source_settings={**settings,'retries':0} if source['id']=='remotive' else settings
            for raw in collector(source,source_settings):
                o=match(normalize(raw,source,stamp),profile,weights)
                # Do not fill the public database with unrelated business roles.
                if relevant(o): staged.append(o)
            for o in staged:
                existing=records.get(o['id'])
                if existing:
                    o['first_discovered']=existing['first_discovered']
                    o['last_updated']=existing.get('last_updated',existing['first_discovered'])
                    fields=('title','description','deadline','deadline_precision','application_status','location','relevance_score')
                    if any(o.get(k)!=existing.get(k) for k in fields): modified+=1; o['last_updated']=stamp
                    o['link_validation']=existing.get('link_validation',o['link_validation'])
                else: new+=1; o['last_updated']=stamp
                records[o['id']]=o
            state.update(status='ok',count=len(staged),last_success=stamp,message='Public source retrieved and schema parsed')
            successes+=1
        except Exception as e:
            log.warning('%s: %s',source['id'],str(e))
            state.update(status='failed',message=f'{type(e).__name__}: {str(e)[:240]}')
        health.append(state); time.sleep(settings['request_delay_seconds'])
    active=[]; archived=[]
    for o in deduplicate(records.values()):
        o=match(o,profile,weights)
        o['deadline_status']=deadline_status(o,now)
        (archived if o['deadline_status'] in ('Expired','Closed') else active).append(o)
    active.sort(key=sort_key); archived.sort(key=sort_key)
    history=read(root/'data/alert_history.json',{})
    alerts=notify(active,history,settings,now)
    status={'last_attempt':stamp,'last_successful_refresh':stamp if successes else prior_status.get('last_successful_refresh'),'status':'ok' if successes==sum(s['enabled'] for s in sources) else 'partial' if successes else 'failed','new':new,'modified':modified,'expired':sum(o['id'] in old and old[o['id']].get('deadline_status') not in ('Expired','Closed') for o in archived),'active':len(active),'archived':len(archived),'sources':health,'notifications':alerts,'notice':'Unknown deadlines remain unknown; source outages do not close listings. Data-only dates use end-of-day comparison; no exact closing time is asserted.'}
    write(root/'data/opportunities.json',active); write(root/'data/archived_opportunities.json',archived)
    write(root/'data/refresh_status.json',status); write(root/'data/alert_history.json',history)
    return status

def validate(root=ROOT):
    all_records=read(root/'data/opportunities.json',[])+read(root/'data/archived_opportunities.json',[])
    ids=set()
    from .core import canonical,deadline_instant
    for o in all_records:
        assert o['id'] not in ids, 'Duplicate ID'; ids.add(o['id'])
        assert 0<=o['relevance_score']<=100
        for key in ('original_url','application_url'): canonical(o[key])
        deadline_instant(o)
        assert o['eligibility'] in ('verified','likely','restricted','unknown')
    return len(ids)

def verify_links(limit=15):
    path=ROOT/'data/opportunities.json'; records=read(path,[]); settings=read(ROOT/'config/settings.yaml',{})
    ranked=sorted(records,key=lambda o:-o['relevance_score'])
    for o in ranked[:limit]:
        try: fetch(o['original_url'],settings); o['link_validation']='HTTP GET succeeded '+datetime.now(timezone.utc).isoformat()
        except Exception as e: o['link_validation']='Link check failed; not evidence of closure: '+type(e).__name__
        time.sleep(settings['request_delay_seconds'])
    write(path,records)

def main():
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    parser=argparse.ArgumentParser(); parser.add_argument('--validate',action='store_true'); parser.add_argument('--verify-links',type=int); parser.add_argument('--sources',nargs='+'); args=parser.parse_args()
    if args.validate: print(f'Validated {validate()} records')
    elif args.verify_links is not None: verify_links(args.verify_links)
    else:
        result=refresh(only=args.sources); print({k:v for k,v in result.items() if k!='sources'})
        if result['status']=='failed': raise SystemExit(1)

if __name__=='__main__': main()
