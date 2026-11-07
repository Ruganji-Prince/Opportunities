import type {Opportunity,Tracking} from './types';
export function deadline(o:Opportunity):number|null {
 if(!o.deadline||['unknown','rolling'].includes(o.deadline_precision))return null;
 if(o.deadline_precision==='date') {
  const [year,month,day]=o.deadline.slice(0,10).split('-').map(Number);
  // Find the end of the calendar date in its original IANA zone (DST aware).
  const target=Date.UTC(year,month-1,day+1), zone=o.deadline_timezone||'Africa/Kigali';
  let instant=target;
  const formatter=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
  for(let i=0;i<3;i++){
   const p=Object.fromEntries(formatter.formatToParts(instant).map(x=>[x.type,x.value]));
   const local=Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute,+p.second);
   instant+=target-local;
  }
  return instant;
 }
 const result=Date.parse(o.deadline);return Number.isFinite(result)?result:null;
}
export function status(o:Opportunity,now:number):string {
 if(o.application_status==='closed')return 'Closed';
 const end=deadline(o);if(end===null)return o.deadline_precision==='rolling'?'Rolling':'Deadline Unknown';
 const h=(end-now)/3600000;return h<=0?'Expired':h<=72?'Urgent':h<=168?'Closing Soon':h<=336?'Upcoming':'Open';
}
export function compare(a:Opportunity,b:Opportunity,sort:string):number {
 const tie=()=>b.relevance_score-a.relevance_score||a.id.localeCompare(b.id);
 if(sort==='relevance')return tie();
 if(sort==='discovered')return Date.parse(b.first_discovered)-Date.parse(a.first_discovered)||tie();
 if(sort==='updated')return Date.parse(b.last_updated)-Date.parse(a.last_updated)||tie();
 if(sort==='funding')return (b.funding_amount??-1)-(a.funding_amount??-1)||tie();
 const ad=deadline(a),bd=deadline(b);
 const group=(o:Opportunity,d:number|null)=>d!==null?0:o.deadline_precision==='rolling'?1:2;
 return group(a,ad)-group(b,bd)||(ad!==null&&bd!==null?(ad-bd)*(sort==='latest'?-1:1):0)||tie();
}
export function remaining(o:Opportunity,now:number):string {
 const d=deadline(o);if(d===null)return o.deadline_precision==='rolling'?'Applications are rolling':'Confirm deadline with organizer';
 const h=(d-now)/3600000;if(h<=0)return 'Deadline passed';
 return o.deadline_precision==='date'?`${Math.ceil(h/24)} calendar days · time unspecified`:h<24?`${Math.ceil(h)} hours remaining`:`${Math.ceil(h/24)} days remaining`;
}
export function safeUrl(value:string):string {try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)?u.href:'#'}catch{return '#'}}
export function parseTracking(input:unknown):Tracking {
 if(!input||typeof input!=='object'||Array.isArray(input))throw Error('Expected tracker JSON object');
 const result:Tracking={};const entries=Object.entries(input);if(entries.length>10000)throw Error('Too many records');
 for(const [id,v] of entries){
  if(!/^[a-f0-9]{20}$/.test(id)||!v||typeof v!=='object')throw Error('Invalid record ID');
  const x=v as Record<string,unknown>;
  if(typeof x.saved!=='boolean'||typeof x.stage!=='string'||!['interested','preparing','submitted','interview','accepted','rejected','withdrawn'].includes(x.stage)||typeof x.notes!=='string'||typeof x.preparationDeadline!=='string')throw Error('Invalid tracker record');
  result[id]={saved:x.saved,stage:x.stage,notes:x.notes.slice(0,20000),preparationDeadline:x.preparationDeadline.slice(0,10)};
 }return result;
}
export function download(name:string,content:string,type='application/json'){
 const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export function calendar(o:Opportunity):string {
 const esc=(s:string)=>s.replace(/\\/g,'\\\\').replace(/\n/g,'\\n').replace(/,/g,'\\,').replace(/;/g,'\\;');
 const d=deadline(o);if(d===null)throw Error('No confirmed deadline');
 const dt=o.deadline_precision==='date'?`DTSTART;VALUE=DATE:${o.deadline!.slice(0,10).replaceAll('-','')}`:`DTSTART:${new Date(d).toISOString().replace(/[-:]/g,'').replace(/\.\d{3}/,'')}`;
 return ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//OpportunityRadar//EN','BEGIN:VEVENT',`UID:${o.id}@opportunityradar`,`DTSTAMP:${new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}/,'')}`,dt,`SUMMARY:${esc(o.title)}`,`DESCRIPTION:${esc(o.deadline_evidence+' '+o.original_url)}`,`URL:${safeUrl(o.original_url)}`,'END:VEVENT','END:VCALENDAR'].join('\r\n');
}
