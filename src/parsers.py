"""Small, source-specific public feed/page parsers; no scripts are executed."""
from datetime import datetime
from html.parser import HTMLParser
import re
from urllib.parse import urljoin,urlsplit
import xml.etree.ElementTree as ET
from .core import plain

class Node:
    def __init__(self,tag='',attrs=()): self.tag=tag;self.attrs=dict(attrs);self.children=[]
    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child,Node):yield from child.walk()
    def find(self,predicate):return next((n for n in self.walk() if predicate(n)),None)
    def text(self):
        if self.tag in ('script','style','nav','footer'):return ''
        return re.sub(r'\s+',' ',' '.join(c.text() if isinstance(c,Node) else c for c in self.children)).strip()

class Document(HTMLParser):
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self,html):
        super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.feed(html)
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs);self.stack[-1].children.append(n)
        if tag not in self.VOID:self.stack.append(n)
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:del self.stack[i:];break
    def handle_data(self,text):self.stack[-1].children.append(text)

def field(root,token):return root.find(lambda n:token in n.attrs.get('class','').split())
def identified(root,value):return root.find(lambda n:n.attrs.get('id')==value)

def feed_records(body,source):
    # Some Drupal sites put theme-debug comments before the XML declaration.
    start=body.find(b'<?xml')
    if start>0:body=body[start:]
    root=ET.fromstring(body)
    local=lambda tag:tag.rsplit('}',1)[-1]
    if local(root.tag) not in ('rss','feed','RDF'):raise ValueError('Response is not an RSS/Atom feed')
    for item in root.iter():
        if local(item.tag) not in ('item','entry'):continue
        def value(name):return next((x.text or '' for x in item if local(x.tag)==name),'')
        title=plain(value('title'))
        link=value('link') or next((x.attrib.get('href','') for x in item if local(x.tag)=='link' and x.attrib.get('rel','alternate')=='alternate'),'')
        if not title or not link:continue
        description=value('encoded') or value('content') or value('description') or value('summary')
        categories=[plain(x.text or '') for x in item if local(x.tag)=='category']
        category='; '.join(categories+[source.get('source_category','')]).strip('; ')
        organization=source.get('organization','unknown')
        if source.get('creator_is_organization'):organization=plain(value('creator')) or organization
        company=next((x for x in item if local(x.tag)=='company'),None)
        if company is not None:
            name=next((x.text or '' for x in company if local(x.tag)=='name'),'')
            if name:organization=plain(name)
        resolved=urljoin(source['url'],link)
        if urlsplit(source['url']).scheme=='https' and urlsplit(resolved).scheme=='http' and urlsplit(resolved).netloc==urlsplit(source['url']).netloc:resolved='https:'+resolved[5:]
        raw={'title':title,'url':resolved,'description':description,'organization':organization,'location':source.get('location','unknown'),'source_category':category}
        if source.get('structured_phd'):
            raw['location']=plain(value('location'))+(', '+source['host_country'] if source.get('host_country') else '')
            published=value('applicationDeadline')
            if published:
                date=datetime.strptime(published.strip(),'%d. %b %Y').date().isoformat()
                raw.update(deadline=date,deadline_precision='date',deadline_timezone=None,deadline_evidence='DAAD RSS applicationDeadline: '+published+'; exact closing time not supplied')
        if source.get('deadline_timezone'):raw['deadline_timezone']=source['deadline_timezone']
        if source.get('funding_evidence'):raw['funding_evidence']=source['funding_evidence']
        yield raw

def euraxess_detail(html,raw):
    root=Document(html).root;values={}
    for dl in (n for n in root.walk() if n.tag=='dl'):
        label=None
        for child in dl.children:
            if not isinstance(child,Node):continue
            if child.tag=='dt':label=child.text()
            elif child.tag=='dd' and label:values.setdefault(label,child)
    content=identified(root,'block-rtd-euraxess-main-page-content')
    if content:raw['description']=content.text()
    for key,target in [('Organisation/Company','organization'),('Country','location')]:
        if key in values:raw[target]=values[key].text()
    if 'Application Deadline' in values:
        n=values['Application Deadline'];time=n.find(lambda x:x.tag=='time' and 'datetime' in x.attrs)
        if time:
            date=time.attrs['datetime'];parsed=datetime.fromisoformat(date.replace('Z','+00:00'))
            if parsed.tzinfo is not None:
                zone=re.search(r'\(([^)]+/[^)]+)\)',time.text())
                raw.update(deadline=date,deadline_precision='timestamp',deadline_timezone=zone[1] if zone else None,deadline_evidence='EURAXESS Application Deadline: '+time.text()+'; datetime='+date)
    # Use only the organizer-provided application website, never contact/sidebar links.
    for n in root.walk():
        if n.tag=='a' and 'job-apply-button' in n.attrs.get('class','').split():
            application=urljoin(raw['url'],n.attrs.get('href',''))
            if urlsplit(application).scheme in ('https','http'):raw['application_url']=application;break
    raw['detail_verified']=True
    return raw

def article_detail(html,raw):
    root=Document(html).root
    content=field(root,'entry-content') or identified(root,'maincontent') or root.find(lambda n:n.tag=='article')
    if content:raw['description']=content.text();raw['detail_verified']=True
    return raw

def jobinrwanda_links(html,url):
    root=Document(html).root;seen=set()
    for n in root.walk():
        if n.tag=='a' and n.attrs.get('href','').startswith('/job/'):
            link=urljoin(url,n.attrs['href']);title=n.text()
            if link not in seen and title:seen.add(link);yield {'title':title,'url':link,'description':''}

def jobinrwanda_detail(html,raw):
    root=Document(html).root
    description=field(root,'field--name-field-job-full-description')
    summary=identified(root,'block-jobsummaryblock')
    if not description or not summary:raise ValueError('Job in Rwanda listing structure changed')
    raw['description']=description.text();summary_text=summary.text()
    title=root.find(lambda n:n.tag=='h1')
    if title:raw['title']=title.text()
    employer=identified(root,'block-jobemployerblock')
    if employer:
        n=employer.find(lambda n:n.tag=='a' and n.attrs.get('href','').startswith('/employer/'))
        if n:raw['organization']=n.text()
    # This source displays DD/MM/YYYY; no timezone is asserted for its local time.
    date=re.search(r'Deadline:\s*(?:[A-Za-z]+,?\s*)?(\d{2}/\d{2}/\d{4})(?:\s+\d{2}:\d{2})?',summary_text)
    if date:raw.update(deadline=datetime.strptime(date[1],'%d/%m/%Y').date().isoformat(),deadline_precision='date',deadline_timezone=None,deadline_evidence='Job in Rwanda '+date[0]+'; source uses DD/MM/YYYY, timezone not verified')
    location=re.search(r'Location:\s*(.*?)(?:\s+(?:Purpose|Reports|About|Job|Department|Contract)\b|$)',raw['description'],re.I)
    if location:raw['location']=location[1][:200]
    elif re.search(r'\b(?:Kigali|Rwanda)\b',summary_text,re.I):raw['location']='Rwanda'
    raw['detail_verified']=True
    return raw
