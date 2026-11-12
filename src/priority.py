"""Original-announcement evidence extraction and doctoral feed adapters."""
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit,parse_qs
from .core import plain,extract_deadline
from .parsers import Document,identified,field,article_detail

def snippet(text,pattern,size=220):
    m=re.search(pattern,text,re.I)
    return text[max(0,m.start()-45):m.end()+size].strip() if m else ''

def page_text(body):
    doc=Document(body.decode('utf-8','replace')).root
    node=doc.find(lambda n:n.tag=='main') or identified(doc,'main-content') or identified(doc,'maincontent') or doc.find(lambda n:n.tag=='article') or doc
    return node.text()

def date_from_text(text):
    dated=extract_deadline(text)
    if dated:return dated
    m=re.search(r'Application due\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})',text,re.I)
    if m:return {'deadline':datetime.strptime(m[1],'%d/%m/%Y').date().isoformat(),'deadline_precision':'date','deadline_timezone':None,'deadline_evidence':m[0]+'; time unspecified'}
    # German institutional feeds explicitly label their DD.MM.YYYY closing dates.
    m=re.search(r'(?:Bewerbungsfrist|Bewerbungsschluss|application deadline|closing date|deadline)\s*:?\s*(\d{1,2}\.\d{1,2}\.\d{4})',text,re.I)
    if m:return {'deadline':datetime.strptime(m[1],'%d.%m.%Y').date().isoformat(),'deadline_precision':'date','deadline_timezone':None,'deadline_evidence':m[0]+'; time unspecified'}
    m=re.search(r'(?:until|by|deadline\s*:)\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',text,re.I)
    if m:return extract_deadline('Deadline: '+m[1])
    return None

def mark_review(raw,facts,urls):
    raw['assessment']=facts;raw['review_sources']=list(dict.fromkeys(urls))
    return raw

def annotate_known(raw,source):
    """Re-evaluated on every API/feed refresh; no permanent featured flag."""
    url=raw['url'];text=plain(raw.get('description',''));low=text.lower();facts={};urls=[url]
    if source['id']=='anthropic' and any(x in url for x in ('5183051008','5183044008')):
        # The later full-time-role visa policy explicitly does NOT apply to fellows.
        text=re.split(r'The below are Anthropic.s policies for full.time roles',text,flags=re.I)[0]
        raw['description']=text
        facts['qualifications']='Python programming and full-time availability; confirm the research workstream criteria'
        if re.search(r'work authorization.*(?:US|UK|Canada)|work authorization in the (?:US|U.S.)',text,re.I):
            facts.update(work_authorization_required=True,conditions=['Must live and be authorized to work in the US, UK or Canada; no fellow visa sponsorship'])
        if re.search(r'stipend|3,850|2,310|4,300',text,re.I):facts.update(funding_level='paid',funding_evidence=snippet(text,r'weekly stipend|base stipend'),salary='Published weekly stipend: USD 3,850 / GBP 2,310 / CAD 4,300; country-specific terms')
        start=re.search(r'(January|September)\s+(20\d{2})',text,re.I)
        if start:facts.update(start_date=start[2]+('-01' if start[1].lower()=='january' else '-09'),intake=start[0]+' cohort')
        facts['start_flexible']=bool(re.search(r'outside the usual cohort|starting outside|off.cycle',text,re.I))
        if '5183044008' in url and re.search(r'October\s+30|30\s+October',text,re.I) and start and start[0].lower()=='january 2027':
            facts.update(application_status='closed',status_note='Published January 2027 cohort gives a 30 October application deadline (year omitted). That cohort cutoff has elapsed as of November 2026; no deadline year or time has been invented.',conditions=facts.get('conditions',[])+['Check the organizer for a new cohort; generic rolling language does not supersede the cohort cutoff'])
            raw.update(deadline=None,deadline_precision='unknown',deadline_evidence=snippet(text,r'October\s+30|30\s+October'))
        elif re.search(r'rolling basis|applications on a rolling',text,re.I):raw.update(deadline=None,deadline_precision='rolling',deadline_evidence=snippet(text,r'rolling basis|applications on a rolling'))
    elif source['id']=='cohere' and any(x in url for x in ('73bd3e2b-6597-4124-b64b-1e5dbc32e785','36d1f52f-8270-4652-adf5-5303a0ff341b')):
        facts.update(intake='Winter 2027 internship',start_date='2027-01',qualifications='Currently enrolled student; full-time internship availability and host-country work authorization need confirmation',conditions=['Winter 2027 full-time term may overlap with the MSc; agree availability before applying'])
        if re.search(r'work authori[sz]ation|authorized to work|authorised to work|legally.*work',text,re.I):facts['work_authorization_required']=True
        if '73bd3e2b' in url:facts['conditions'].append('Primarily targets PhD students; exceptional non-PhD applicants may be considered')
        facts['status_note']='Official listing available; no fixed application deadline verified. Remote does not establish Rwanda work eligibility.'
    elif source['id']=='daad-phd':
        ident=parse_qs(urlsplit(url).query).get('phd-id',[''])[0]
        if ident in ('10489','10504','8990','10374'):
            facts['qualifications']=snippet(text,r'master|MSc|M.Sc') or 'Consult the original degree and discipline requirements'
            facts['conditions']=['Degree must satisfy the published discipline requirements; start-date agreement after May 2027 is not established']
            if ident=='8990':
                if re.search(r'E13|E.?13|TV.?L',text,re.I):facts.update(funding_level='paid',funding_evidence=snippet(text,r'E13|E.?13|TV.?L'))
                if re.search(r'FPGA|mixed.signal|microelectronic',text,re.I):facts.update(specialist_requirements_unverified=True,conditions=facts['conditions']+['FPGA, analog/mixed-signal IC and microelectronics requirements are not established by the CV'])
            if ident=='10374':
                facts['conditions']+=['Experimental membrane/chemical-process qualification equivalence and any driving-license requirement need confirmation']
                facts['status_note']='Financing is indicated by the source; full financial coverage and May 2027 start flexibility are not verified'
            if ident=='10489':facts['conditions'].append('Employer deadline-year conflict is checked in the Hereon source; retain the conservative date')
            if ident=='10504':facts['conditions'].append('Completed relevant MSc and software/automated-driving requirements need confirmation')
            if ident=='10504' and re.search(r'C1|C 1',text,re.I):facts.update(language_requirement='German C1',conditions=facts['conditions']+['German C1 and a Germany-valid category B driving license are mandatory; the CV lists basic German'],specialist_requirements_unverified=True)
    if facts:return mark_review(raw,facts,urls)
    if raw.get('detail_verified') and source['id'] in ('euraxess','oxford-research','bath-research'):
        return mark_review(raw,{'qualifications':snippet(text,r'master|bachelor|MSc|M.Sc|qualifications') or 'Confirm qualifications in the original announcement','conditions':['Nationality, qualifications and intended start date require organizer confirmation']},urls)
    return raw

def hereon_records(body,source):
    root=ET.fromstring(body)
    if root.tag!='HELMHOLTZ':raise ValueError('Unexpected Hereon feed schema')
    for job in root.findall('.//JOB'):
        text=plain(job.findtext('DESCRIPTION',''));title=plain(job.findtext('TITLE',''));url=job.findtext('LINK','')
        if not title or not url:continue
        if not re.search(r'PhD|doctoral|Doktorand|research|scientist|engineer|postdoc',title,re.I):continue
        # The feed's JOB_TYPE has mislabeled administrative roles; never classify by it.
        where=re.search(r'Location:\s*(.*?)(?=Application deadline|Job ID|$)',text,re.I)
        raw={'title':title,'url':url.replace('/cms60/','/'),'description':text,'organization':'Helmholtz-Zentrum Hereon','location':(where[1].strip()+', Germany') if where else 'Germany','source_category':'PhD' if re.search(r'PhD|doctoral|Doktorand',title,re.I) else 'research'}
        structured=job.findtext('CLOSING_DATE','');dates=[]
        if structured:
            try:dates.append(datetime.strptime(structured,'%d.%m.%Y').date().isoformat())
            except ValueError:pass
        described=date_from_text(text)
        # Hereon's English descriptions use explicit US numeric dates in labeled fields.
        numeric=re.search(r'Application deadline:\s*(\d{1,2}/\d{1,2}/\d{4})',text,re.I)
        if numeric:
            parsed=datetime.strptime(numeric[1],'%m/%d/%Y').date().isoformat();dates.append(parsed)
        if described:dates.append(described['deadline'])
        facts={'qualifications':plain(job.findtext('QUALIFICATIONS','')) or snippet(text,r'master|PhD|MSc'),'conditions':['Confirm degree completion and start-date flexibility with the employer']}
        if dates:raw.update(deadline=min(dates),deadline_precision='date',deadline_timezone=None,deadline_evidence=f'Hereon CLOSING_DATE: {structured}; description: '+(described['deadline_evidence'] if described else numeric[0] if numeric else 'not specified'))
        if len(set(dates))>1:facts['conflicts']=[f'Official structured field and description disagree: {", ".join(sorted(set(dates)))}. Earlier date retained pending organizer clarification.']
        if re.search(r'E.?13|public.service.*remuneration|remuneration.*public',text,re.I):facts.update(funding_level='paid',funding_evidence=snippet(text,r'E.?13|remuneration'))
        yield mark_review(raw,facts,[raw['url'],source['url']])

def reviewed_announcement(source,settings,fetch,check_robots):
    urls=[source['url']]+source.get('companion_urls',[]);cache={};texts={}
    for url in urls:
        check_robots(source,settings,url,cache);texts[url]=page_text(fetch(url,settings))
    text=texts[source['url']];all_text=' '.join(texts.values());rule=source['rule']
    raw={'title':source['title'],'url':source.get('record_url',source['url']),'application_url':source['url'],'description':text[:12000],'organization':source['organization'],'location':source.get('location','unknown'),'source_category':source.get('source_category','research')}
    facts={'conditions':[]}
    if rule=='bmai':
        m=re.search(r'September\s+1\s+to\s+December\s+1,?\s+(20\d{2})',text,re.I)
        if not m:raise ValueError('Current explicitly dated Max Planck application cycle not found')
        deadline=m[1]+'-12-01';intake=re.search(r'program\s+starts\s+in\s+September\s+(20\d{2})',text,re.I)
        raw.update(deadline=deadline,deadline_precision='date',deadline_evidence=m[0])
        if re.search(r'11:59\s*pm\s*CET',all_text,re.I):raw.update(deadline=deadline+'T23:59:00+01:00',deadline_precision='timestamp',deadline_timezone='Europe/Berlin',deadline_evidence=m[0]+'; FAQ: 11:59 pm CET')
        if intake:facts.update(start_date=intake[1]+'-09',intake='Fall '+intake[1]+' Intake')
        facts['degree_in_progress_allowed']=bool(re.search(r'apply with a current transcript|not yet completed.*current academic degree',all_text,re.I))
        facts['qualifications']='Relevant MSc in computer science, mathematics, statistics, engineering, physics or life sciences with substantial computational education; final MSc documents before entry'
        facts['conditions']=['Confirm foreign-degree equivalence, English-language evidence, supervisor fit and references']
        if re.search(r'contract.*E13',all_text,re.I) and re.search(r'cover.*living|living expenses',all_text,re.I):facts.update(funding_level='fully_funded',funding_evidence='Official FAQ: three-year E13 public-service contract. Program: employment contracts cover living expenses for the PhD program.')
    elif rule=='sintef':
        dated=date_from_text(text)
        if not dated:
            due=re.search(r'Application due\s*(\d{2}/\d{2}/\d{4})',text,re.I)
            if due:dated={'deadline':datetime.strptime(due[1],'%d/%m/%Y').date().isoformat(),'deadline_precision':'date','deadline_evidence':due[0]+'; source DD/MM/YYYY, closing time unspecified'}
        if not dated:raise ValueError('SINTEF current closing date not found')
        raw.update(dated)
        cutoff=re.search(r'completed and documented before\s+(\d{1,2}\s+[A-Za-z]+\s+20\d{2})',text,re.I)
        if cutoff:facts['degree_completion_by']=datetime.strptime(cutoff[1],'%d %B %Y').date().isoformat()
        facts.update(qualifications='Relevant two-year / 120-ECTS-equivalent MSc, academic requirements and Brunel doctoral admission',conditions=['MSCA mobility: no more than 12 months in Norway during the preceding 36 months','Daily on-site availability and doctoral admission required'])
        if re.search(r'funded through.*MSCA',text,re.I):facts.update(funding_level='paid',funding_evidence=snippet(text,r'funded through'),status_note='EU/MSCA doctoral employment; funding/admission conditions apply')
    elif rule=='sussex-quantum':
        m=re.search(r'Deadline\s+(\d{1,2}\s+[A-Za-z]+\s+20\d{2})\s+(\d{2}:\d{2})',text,re.I)
        if not m:raise ValueError('Sussex final scholarship deadline not found')
        date=datetime.strptime(m[1],'%d %B %Y').date().isoformat();raw.update(deadline=date,deadline_precision='date',deadline_evidence=m[0]+'; organizer timezone must be confirmed')
        if re.search(r'fully funded.*tuition fees.*stipends',text,re.I):facts.update(funding_level='fully_funded',funding_evidence=snippet(text,r'fully funded',350))
        intake=re.search(r'September\s+(20\d{2})',text,re.I)
        if intake:facts.update(start_date=intake[1]+'-09',intake='Fall '+intake[1]+' Intake')
        facts.update(qualifications=snippet(text,r'eligible|entry requirements|2:1|first.class'),conditions=['Quantum-specialization and academic entry requirements need confirmation','Final-year degree acceptance and priority-round dates should be checked with the organizer; places may fill before the final deadline'])
        if not re.search(r'international',text,re.I):facts['conditions'].append('International fee eligibility needs confirmation')
    elif rule=='movenow':
        m=re.search(r'(?:18th\s+DEC|18\s+December|December\s+18)',text,re.I)
        if not m:raise ValueError('MoveNow closing-day evidence not found')
        # The official timeline explicitly places scoring in January 2027 after December submissions.
        following=re.search(r'JAN(?:UARY)?\s+(20\d{2}).{0,50}Scoring',text,re.I)
        if not following:raise ValueError('Current MoveNow cycle not verified')
        year=int(following[1])-1
        raw.update(deadline=f'{year}-12-18T17:00:00+00:00',deadline_precision='timestamp',deadline_timezone='UTC',deadline_evidence=f'Official timeline: 18 December submissions close 5pm UTC; January {following[1]} scoring follows (closing year derived from this explicit cycle)')
        facts.update(qualifications='Founder or decision-maker of a social-impact project or venture',age_requirement='Age 18–30',conditions=['Project ownership, measurable impact and challenge criteria need confirmation'],funding_level='competitive_grant',funding_evidence='Competitive grants of USD 5,000 / 10,000; award is not guaranteed')
    elif rule=='imagine':
        year=re.search(r'Imagine Cup\s+(20\d{2})',text,re.I)
        closing=re.search(r'February\s+28,?\s+(20\d{2})',text,re.I)
        if not year or not closing:raise ValueError('Current Imagine Cup cycle/deadline evidence not found')
        raw.update(deadline=closing[1]+'-02-28',deadline_precision='date',deadline_evidence=snippet(text,r'February\s+28'))
        if re.search(r'23:59\s*CST|11:59\s*p\.?m\.?\s*CST',text,re.I):raw.update(deadline=closing[1]+'-02-28T23:59:00-06:00',deadline_precision='timestamp',deadline_timezone='America/Chicago')
        facts.update(qualifications='Early-stage registered startup with commercial software potential; student enrollment alone is not sufficient',funding_level='competitive_prize',conditions=['Azure usage, incorporation date, funding-stage and competition-country rules require confirmation'])
        if re.search(r'registered legal entity',text,re.I):facts.update(startup_required=True,startup_evidence=snippet(text,r'registered legal entity'))
        if re.search(r'at least 18',text,re.I):facts['age_requirement']='At least 18 years old'
    else:raise ValueError('Unknown reviewed announcement parser')
    raw['detail_verified']=True
    return mark_review(raw,facts,urls)
