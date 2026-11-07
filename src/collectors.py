"""Read-only public APIs and RSS. No authentication or anti-bot bypass."""
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
from .core import plain,relevant
from .parsers import feed_records,euraxess_detail,article_detail,jobinrwanda_links,jobinrwanda_detail

AGENT = 'OpportunityRadar/1.0 (+https://github.com/Ruganji-Prince/Opportunities)'

def fetch(url, settings, method='GET'):
    for attempt in range(settings['retries']+1):
        try:
            request = Request(url, headers={'User-Agent':AGENT,'Accept':'application/json, application/rss+xml, text/xml;q=0.9, */*;q=0.5'}, method=method)
            with urlopen(request,timeout=settings['timeout_seconds']) as r:
                if int(r.headers.get('Content-Length','0')) > 15000000: raise ValueError('Response too large')
                data = r.read(15000001)
                if len(data)>15000000: raise ValueError('Response too large')
                return data
        except HTTPError as e:
            if e.code not in (429,500,502,503,504) or attempt==settings['retries']: raise
        except (OSError,TimeoutError):
            if attempt==settings['retries']: raise
        time.sleep(min(8,2**attempt))

def check_robots(source, settings, url=None, cache=None):
    # Documented public API endpoints are explicitly exposed for reading.
    if source['adapter'] not in ('rss','euraxess','jobinrwanda'): return
    url=url or source['url'];base = urlsplit(url)
    robots_url = f'{base.scheme}://{base.netloc}/robots.txt'
    parser=(cache or {}).get(robots_url)
    if parser is None:
        parser = RobotFileParser()
        try:rules=fetch(robots_url,settings).decode('utf-8','replace').splitlines()
        except HTTPError as e:
            if e.code!=404:raise
            # A missing robots file is not an access denial. Never ignore 401/403/429.
            rules=[]
        parser.parse(rules)
        if cache is not None:cache[robots_url]=parser
    if not parser.can_fetch(AGENT,url): raise PermissionError('robots.txt disallows this URL')

def collect(source, settings):
    if source.get('permission_required') and not source.get('permission_granted'):raise PermissionError('Source requires prior written permission; collection disabled')
    robots={};check_robots(source,settings,cache=robots)
    body = fetch(source['url'],settings)
    adapter = source['adapter']
    if adapter in ('rss','euraxess','jobinrwanda'):
        rows=jobinrwanda_links(body.decode('utf-8','replace'),source['url']) if adapter=='jobinrwanda' else feed_records(body,source)
        detailed=0
        for raw in rows:
            if not relevant(raw):continue
            if source.get('details') or adapter in ('euraxess','jobinrwanda'):
                if detailed>=source.get('detail_limit',20):
                    if adapter=='jobinrwanda':break
                else:
                    try:
                        check_robots(source,settings,raw['url'],robots)
                        time.sleep(settings['request_delay_seconds'])
                        html=fetch(raw['url'],settings).decode('utf-8','replace')
                        parser=euraxess_detail if adapter=='euraxess' else jobinrwanda_detail if adapter=='jobinrwanda' else article_detail
                        raw=parser(html,raw)
                    except Exception as e:
                        raw['detail_error']=f'{type(e).__name__}: {str(e)[:160]}'
                        if adapter=='jobinrwanda':continue
                    detailed+=1
            yield raw
        return
    data=json.loads(body)
    if adapter=='greenhouse':
        for j in data['jobs']:
            if not plain(j.get('title')): continue
            location=(j.get('location') or {}).get('name') or 'unknown'
            if source.get('location_keywords') and not any(k.lower() in location.lower() for k in source['location_keywords']):continue
            yield {'title':j['title'],'url':j['absolute_url'],'description':j.get('content',''),'location':location}
    elif adapter=='ashby':
        for j in data['jobs']:
            if not j.get('isListed',True): continue
            if not plain(j.get('title')): continue
            address=(j.get('address') or {}).get('postalAddress') or {}
            country=address.get('addressCountry','')
            yield {'title':j['title'],'url':j['jobUrl'],'application_url':j.get('applyUrl') or j['jobUrl'],'description':j.get('descriptionPlain',''),'location':(j.get('location') or 'unknown')+(' / '+country if country else ''),'remote':(j.get('workplaceType') or 'unknown').lower()}
    elif adapter=='lever':
        for j in data:
            description=j.get('descriptionPlain','')+' '+ ' '.join(plain(x.get('content','')) for x in j.get('lists',[]))+' '+j.get('additionalPlain','')
            yield {'title':j['text'],'url':j['hostedUrl'],'application_url':j.get('applyUrl') or j['hostedUrl'],'description':description,'location':j.get('categories',{}).get('location','unknown'),'remote':j.get('workplaceType','unknown')}
    elif adapter=='smartrecruiters':
        # Listing endpoint is paginated. Follow all pages, bounded at 10.
        for page in range(10):
            if page: data=json.loads(fetch(source['url']+f'&offset={page*100}',settings))
            for j in data.get('content',[]):
                # Descriptions and closing dates are only accepted from the detail endpoint.
                title=j.get('name','')
                if not any(k in title.lower() for k in ('machine','data','research','comput','engineer','student','fellow','graduate','doctoral','technical')): continue
                time.sleep(settings['request_delay_seconds'])
                detail=json.loads(fetch(j['ref'],settings))
                sections=detail.get('jobAd',{}).get('sections',{})
                description=' '.join(plain(v.get('text','')) for v in sections.values() if isinstance(v,dict))
                location=detail.get('location',{})
                yield {'title':title,'url':detail.get('postingUrl') or f'https://jobs.smartrecruiters.com/CERN/{j["id"]}','application_url':detail.get('applyUrl') or detail.get('postingUrl') or f'https://jobs.smartrecruiters.com/CERN/{j["id"]}','description':description,'location':', '.join(str(location.get(k,'')) for k in ('city','country')),'remote':'remote' if location.get('remote') else 'on-site'}
            if (page+1)*100>=data.get('totalFound',0): break
    elif adapter=='remotive':
        for j in data['jobs']:
            yield {'title':j['title'],'url':j['url'],'organization':j['company_name'],'description':j.get('description',''),'location':j.get('candidate_required_location','unknown'),'remote':'remote','salary':j.get('salary')}
    else: raise ValueError(f'Unknown adapter {adapter}')
