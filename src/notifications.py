"""Persist successful deliveries only. Threshold keys include changed deadlines."""
import json
import os
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from .core import deadline_instant

def deliver(url,payload,token):
    request=Request(url,data=json.dumps(payload).encode(),headers={'Authorization':f'Bearer {token}','Content-Type':'application/json','Accept':'application/vnd.github+json'},method='POST')
    with urlopen(request,timeout=25) as response:
        if response.status not in (200,201,202): raise RuntimeError('Notification rejected')
        return json.load(response)

def notify(records,history,settings,now=None):
    now=now or datetime.now(timezone.utc); report=[]
    for o in records:
        end=deadline_instant(o)
        if not end or o['eligibility']=='restricted' or o['relevance_score']<settings['minimum_score']: continue
        hours=(end-now).total_seconds()/3600
        # Only the most urgent reached threshold is sent after a missed run.
        reached=[t for t in settings['alert_threshold_hours'] if 0<hours<=t]
        if not reached: continue
        threshold=min(reached)
        for channel in ('github','email'):
            key=f'{o["id"]}:{o["deadline"]}:{threshold}:{channel}'
            if key in history: continue
            title=f'Opportunity deadline within {threshold}h: {o["title"]}'
            body=f'{o["organization"]}\n\nDeadline: {o["deadline"]} ({o["deadline_precision"]}; {o.get("deadline_timezone") or "timezone unknown"})\n\n{o["original_url"]}\n\nEligibility: {o["eligibility"]}. Confirm details with organizer.'
            try:
                if channel=='github' and os.getenv('ENABLE_GITHUB_ALERTS','').lower()=='true':
                    repo=os.environ['GITHUB_REPOSITORY']; token=os.environ['GITHUB_TOKEN']
                    result=deliver(f'https://api.github.com/repos/{repo}/issues',{'title':title,'body':body},token)
                elif channel=='email' and all(os.getenv(k) for k in ('RESEND_API_KEY','ALERT_FROM','ALERT_TO')):
                    result=deliver('https://api.resend.com/emails',{'from':os.environ['ALERT_FROM'],'to':[os.environ['ALERT_TO']],'subject':title,'text':body},os.environ['RESEND_API_KEY'])
                else: continue
                history[key]={'sent_at':now.isoformat(),'delivery_id':str(result.get('id',''))}; report.append({'channel':channel,'status':'sent','id':o['id']})
            except Exception as e: report.append({'channel':channel,'status':'failed','error':type(e).__name__,'id':o['id']})
    return report
