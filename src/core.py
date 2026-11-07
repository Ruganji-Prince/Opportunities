"""Pure, testable normalization, matching, deduplication and deadline rules."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from zoneinfo import ZoneInfo

UTC = timezone.utc

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.hidden = max(0, self.hidden - 1)
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)

def plain(value):
    p = Text(); p.feed(unescape(str(value or '')))
    return re.sub(r'\s+', ' ', ' '.join(p.parts)).strip()

def canonical(url):
    parts = urlsplit(url)
    if parts.scheme not in ('https', 'http') or not parts.netloc: raise ValueError('Unsafe URL')
    query = [(k,v) for k,v in parse_qsl(parts.query) if not k.lower().startswith('utm_') and k not in ('ref','source')]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/'), urlencode(sorted(query)), ''))

def deadline_instant(o):
    value = o.get('deadline')
    if not value or o.get('deadline_precision') in ('unknown','rolling'): return None
    if o.get('deadline_precision') == 'date':
        # End of the stated date; this is a comparison convention, never a claimed time.
        zone = ZoneInfo(o.get('deadline_timezone') or 'Africa/Kigali')
        return (datetime.fromisoformat(value[:10]).replace(tzinfo=zone) + timedelta(days=1)).astimezone(UTC)
    parsed = datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None: raise ValueError('Timestamp deadline must have timezone')
    return parsed.astimezone(UTC)

def deadline_status(o, now=None):
    now = now or datetime.now(UTC)
    if o.get('application_status') == 'closed': return 'Closed'
    end = deadline_instant(o)
    if end:
        hours = (end-now).total_seconds()/3600
        if hours <= 0: return 'Expired'
        if hours <= 72: return 'Urgent'
        if hours <= 168: return 'Closing Soon'
        if hours <= 336: return 'Upcoming'
        return 'Open'
    return 'Rolling' if o.get('deadline_precision') == 'rolling' else 'Deadline Unknown'

def sort_key(o):
    end = deadline_instant(o)
    return (0 if end else 1 if o.get('deadline_precision') == 'rolling' else 2,
            end or datetime.max.replace(tzinfo=UTC), -o.get('relevance_score',0), o['id'])

COUNTRIES = {'Rwanda':'Africa','Kenya':'Africa','Uganda':'Africa','Tanzania':'Africa','Burundi':'Africa','South Sudan':'Africa','South Africa':'Africa','Ghana':'Africa','Nigeria':'Africa','Ethiopia':'Africa','United Kingdom':'Europe','UK':'Europe','Germany':'Europe','France':'Europe','Switzerland':'Europe','Netherlands':'Europe','Portugal':'Europe','Spain':'Europe','Sweden':'Europe','Denmark':'Europe','Italy':'Europe','Poland':'Europe','Belgium':'Europe','Austria':'Europe','United States':'North America','USA':'North America','Canada':'North America','Brazil':'South America','Japan':'Asia','India':'Asia','Singapore':'Asia','Australia':'Oceania'}

def match(o, profile, weights):
    text = (o['title']+' '+o['description']).lower()
    title = o['title'].lower()
    verified_skills=sorted(set(profile['verified_skills']+profile.get('cv_documented_skills',[])))
    verified = [k for k in verified_skills if re.search(r'(?<!\w)'+re.escape(k)+r'(?!\w)',text)]
    interests = [k for k in profile['interests'] if k in text]
    hard = []
    if re.search(r'\b(postdoc\w*|post[- ]doctoral|professor|faculty)\b',title) or re.search(r'(ph\.?d\.?|doctorate)(?: in [^.;]{1,100})? (?:is )?(required|mandatory)|must (?:have|hold|possess) (?:a )?(?:ph\.?d\.?|doctorate)',text): hard.append('Completed doctorate required; profile has no completed PhD')
    if re.search(r'currently enrolled in (?:a )?(?:ph\.?d\.?|doctoral)',text): hard.append('Current doctoral enrollment required; profile is an MSc candidate')
    if re.search(r'\b(senior|staff|principal|director|head of|lead)\b',title): hard.append('Senior role; extensive experience not demonstrated')
    if re.search(r'(?:minimum |at least |requires? )([5-9]|1\d)\+? years',text): hard.append('Extensive professional experience required')
    if re.search(r'(?:us|u\.s\.|united states) citizens? only|must be (?:a |an )?(?:us|u\.s\.) citizen',text): hard.append('Citizenship restriction; eligibility not established')
    global_access = bool(re.search(r'^(?:worldwide|anywhere(?: in the world)?|global)$',o.get('location','').strip(),re.I) or re.search(r'(?:open to|accept(?:s|ing)?|applicants? from|candidates? from|applications? from) [^.;]{0,65}(?:all nationalities|any nationality|all countries|any country|worldwide|anywhere in the world)',text))
    o['eligibility'] = 'restricted' if hard else 'likely' if global_access else 'unknown'
    o['eligibility_evidence'] = hard or (['Worldwide applicant coverage explicitly stated; confirm other requirements'] if global_access else ['Nationality, work authorization and start-date requirements must be checked with the organizer'])
    o['applicant_coverage'] = 'Global' if global_access else 'unknown'
    if re.search(r'\b(phd|ph\.d|doctoral)\b',title+' '+o.get('source_category','').lower()): category, kind = 'research','PhD'
    elif re.search(r'hackathon|competition|challenge|accelerator|incubator',title): category,kind='innovation','competition'
    elif re.search(r'summer school|bootcamp|conference|workshop|travel grant',title): category,kind='development','training'
    elif re.search(r'research|fellow|scholarship|studentship',title): category,kind='research','fellowship' if 'fellow' in title else 'research'
    else: category,kind='industry','internship' if re.search(r'\b(?:intern(?:ship)?s?|graduate|student)\b',title) else 'job'
    o['category'],o['subcategory'] = category,kind
    academic = .0 if hard else .6
    career = 1 if kind in ('PhD','fellowship','internship') else .75 if category in ('research','innovation') else .5
    technical = min(1, len(verified)*.24 + len(interests)*.12)
    o['funding_status'] = 'funded' if o.get('funding_evidence') or re.search(r'(?<!not )fully[- ]funded|full scholarship',text) else 'unknown'
    score = round(weights['technical']*technical + weights['academic']*academic + weights['career']*career + weights['geographic']*(1 if global_access else .3) + weights['funding']*(1 if o['funding_status']=='funded' else .3))
    if not verified and not interests: score=min(score,weights['minimum']-1)
    o['relevance_score'] = min(score,30) if hard else score
    o['relevance_explanation'] = [f'Profile skills mentioned: {", ".join(verified) or "none"}', f'Research interests mentioned: {", ".join(interests) or "none"}',f'Career category: {category}; eligibility: {o["eligibility"]}', 'Score is prioritization, not an acceptance probability']
    o['tags'] = sorted(set(verified+interests))
    o['skills_not_demonstrated'] = interests
    o['required_qualifications'] = 'unknown; consult original announcement'
    o['startup_requirements'] = 'unknown; check company, team and prototype requirements' if category=='innovation' else 'not applicable'
    location = o.get('location','unknown')
    country = next((c for c in COUNTRIES if re.search(r'\b'+re.escape(c)+r'\b',location,re.I)), 'unknown')
    o['host_country'],o['host_continent'] = country,COUNTRIES.get(country,'unknown')
    o['geographic_scope'] = (['Global'] if global_access else []) + ([o['host_continent']] if country!='unknown' else [])
    if country in ('Rwanda','Kenya','Uganda','Tanzania','Burundi','South Sudan'): o['geographic_scope'].append('East Africa')
    if country=='Rwanda': o['geographic_scope'].append('Rwanda')
    return o

def relevant(o):
    return bool(re.search(r'\b(?:ai|ml|machine learning|data|research\w*|scientist\w*|engineer\w*|phd|doctoral|intern(?:ship)?s?|fellow\w*|scholarship\w*|studentship\w*|hackathon\w*|competition\w*|innovation|grant\w*|accelerator\w*|bootcamp\w*|summer school)\b',o['title']+' '+o.get('source_category',''),re.I) or len(o.get('tags',[]))>=5)

def normalize(raw, source, now):
    url = canonical(raw['url'])
    o = {'id':sha256(url.encode()).hexdigest()[:20], 'title':plain(raw['title']), 'organization':plain(raw.get('organization') or source.get('organization','unknown')), 'description':plain(raw.get('description',''))[:16000], 'location':plain(raw.get('location','unknown')), 'remote':raw.get('remote','unknown'), 'deadline':raw.get('deadline'), 'deadline_precision':raw.get('deadline_precision','unknown'), 'deadline_timezone':raw.get('deadline_timezone'), 'deadline_evidence':raw.get('deadline_evidence','No verified application deadline extracted'), 'source_id':source['id'], 'source_name':source['name'], 'original_url':url, 'application_url':canonical(raw.get('application_url') or url), 'first_discovered':now,'last_verified':now,'application_status':raw.get('application_status','unknown'),'funding_amount':None,'funding_currency':None,'salary':raw.get('salary') or 'unknown','application_opening_date':None,'eligible_nationalities':'unknown','required_skills':'unknown','scholarship_information':'unknown','provenance':{'listing':source['url'],'deadline':raw.get('deadline_evidence','Not provided by source')}, 'link_validation':'Source supplied URL; individual link not yet checked'}
    if not o['title']: raise ValueError('Missing title')
    o['source_category']=plain(raw.get('source_category',''))
    o['funding_evidence']=plain(raw.get('funding_evidence',''))
    if raw.get('detail_verified'):o['link_validation']='HTTP GET succeeded; opportunity detail parsed '+now
    if not o['deadline']:
        extracted = extract_deadline(o['description'])
        if extracted:
            o.update(extracted)
            if raw.get('deadline_timezone'):o['deadline_timezone']=raw['deadline_timezone']
        elif re.search(r'rolling (?:applications|admissions|basis)|applications (?:are )?(?:accepted|reviewed) on a rolling',o['description'],re.I):
            o.update(deadline_precision='rolling',deadline_evidence='Source explicitly describes rolling applications')
    o['provenance']['deadline']=o['deadline_evidence']
    deadline_instant(o)
    return o

def extract_deadline(text):
    # Require an explicit deadline label, a day, a written month, and a four-digit year.
    # Never infer a deadline from event dates or the discovery date.
    month=r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
    label=r'(?:application deadline|deadline for applications|closing date|applications? (?:close|deadline)|deadline|submit (?:your )?application(?:s)? by)\s*(?:is|:|on|by)?\s*'
    pattern=label+r'(?P<date>(?:\d{1,2}(?:st|nd|rd|th)?\s+'+month+r'\s*,?\s*\d{4}|'+month+r'\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4}))'
    found=re.search(pattern,text,re.I)
    if not found: return None
    value=re.sub(r'(\d)(st|nd|rd|th)',r'\1',found['date'],flags=re.I).replace(',','')
    value=re.sub(r'\s+',' ',value).strip()
    for fmt in ('%d %B %Y','%B %d %Y','%d %b %Y','%b %d %Y'):
        try:
            date=datetime.strptime(value,fmt).date().isoformat()
            return {'deadline':date,'deadline_precision':'date','deadline_timezone':None,'deadline_evidence':found[0]+' [exact time and timezone not verified]'}
        except ValueError: pass
    return None

def deduplicate(records):
    seen = {}; aliases = {}
    for o in records:
        key = (re.sub(r'\W+','',o['title'].lower()), re.sub(r'\W+','',o['organization'].lower()),o.get('location','').lower())
        # A missing institution is not evidence that two similarly titled roles are the same.
        known_organization=o['organization'].strip().lower() not in ('','unknown')
        existing = aliases.get(key) if known_organization else None
        if o['id'] in seen: seen[o['id']] = o
        elif existing:
            links=set(seen[existing].get('additional_sources',[]));links.add(o['original_url'])
            seen[existing]['additional_sources']=sorted(links)
        else:
            seen[o['id']] = o
            if known_organization:aliases[key] = o['id']
    return list(seen.values())
