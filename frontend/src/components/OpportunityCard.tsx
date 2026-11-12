import {Bookmark,ArrowUpRight,CalendarDays,ChevronDown,MapPin,ExternalLink} from 'lucide-react';
import {labels} from '../recommendations';
import type {Opportunity,Tracker} from '../types';
import {status,deadline,remaining,safeUrl,download,calendar} from '../logic';


const stageLabels:Record<string,string>={interested:'Interested',preparing:'Application in Progress',submitted:'Applied',interview:'Interview',accepted:'Accepted',rejected:'Rejected',withdrawn:'Withdrawn'};
export const emptyTracker:Tracker={saved:false,stage:'interested',notes:'',preparationDeadline:''};
interface Props {personal?:boolean;opportunity:Opportunity;now:number;tracking:Tracker;expanded:boolean;toggle:()=>void;update:(change:Partial<Tracker>)=>void}
export function OpportunityCard({opportunity:o,now,tracking:t,expanded,update,toggle,personal=false}:Props){
 const s=status(o,now),warning=['Urgent','Closing Soon'].includes(s)&&(!personal||(o.relevance_score>=55&&o.eligibility!=='restricted'));
 const institution=o.organization==='unknown'?o.source_name:o.organization;
 const funded=o.fully_funded_verified?'Fully funded · verified':o.funding_level==='paid'?'Paid position · verified':o.funding_status==='funded'?'Funding available · confirm coverage':'Funding not confirmed';
 const date=o.deadline?(o.deadline_precision==='date'?new Intl.DateTimeFormat('en',{dateStyle:'medium',timeZone:'UTC'}).format(new Date(o.deadline.slice(0,10)+'T12:00:00Z')):new Intl.DateTimeFormat('en',{dateStyle:'medium',timeStyle:'short',timeZone:'Africa/Kigali'}).format(new Date(o.deadline))+' CAT'):o.deadline_precision==='rolling'?'Rolling applications':'Deadline not specified.';
 return <article data-opportunity-id={o.id} className={'opportunity-card '+(warning?'urgent-card':'')}>
  <div className="card-top"><div className={'org-icon '+o.category} aria-hidden="true">{institution.slice(0,2).toUpperCase()}</div><div className="card-org"><strong>{institution}</strong><span><MapPin size={17}/>{o.location==='unknown'?'Location to confirm':o.location}</span></div><button aria-label={t.saved?'Unsave opportunity':'Save Opportunity'} aria-pressed={t.saved} className={'save-button '+(t.saved?'saved':'')} onClick={()=>update({saved:!t.saved})}><Bookmark size={22} fill={t.saved?'currentColor':'none'}/></button></div>
  <h3>{o.title}</h3>
  <dl className="card-facts"><div><dt>Category</dt><dd>{o.subcategory}</dd></div><div><dt>Funding</dt><dd>{o.funding_verified?funded:'Funding not confirmed'}</dd></div></dl>
  {personal&&<div className="personal-card-facts"><p><strong>{o.relevance_score}/100 relevance</strong> · {o.eligibility==='restricted'?'Restriction identified':o.eligibility==='verified'?'Verified eligibility conditions':'Eligibility needs confirmation'}</p><p><strong>Qualifications:</strong> {o.required_qualifications}</p><div className="evidence-labels">{labels(o,now).map(label=><span key={label}>{label}</span>)}</div><p>{o.relevance_explanation.find(x=>!x.startsWith('Score is'))}</p></div>}
  <div className={'deadline-row '+(warning?'approaching':'')}><CalendarDays size={23}/><div><strong>{date}</strong>{personal&&<small className="countdown">{remaining(o,now)}</small>}</div>{(warning||['Expired','Closed'].includes(s))&&<span>{s}</span>}</div>
  <div className="card-actions"><button onClick={toggle} aria-expanded={expanded} aria-controls={'details-'+o.id}>{expanded?'Hide details':'View details'}<ChevronDown size={19}/></button><a className="apply-button" target="_blank" rel="noopener noreferrer" href={safeUrl(o.application_url)}>{o.application_url!==o.original_url?'Apply Now':'View Announcement'}<ArrowUpRight size={19}/></a></div>
  {expanded&&<div className="details" id={'details-'+o.id}>
   <h4>Overview</h4><p>{o.description}</p>
   <button className="secondary-button" onClick={async()=>{const url=new URL(window.location.href);url.searchParams.set('opportunity',o.id);try{if(navigator.share)await navigator.share({title:o.title,url:url.href});else await navigator.clipboard.writeText(url.href)}catch{ /* Sharing can be cancelled. The link remains selectable below. */ }}}>Share opportunity</button><label>Shareable link<input readOnly aria-label="Shareable opportunity link" value={new URL('?opportunity='+o.id,window.location.href).href} onFocus={e=>e.target.select()}/></label>
   <p className="supporting">{now-Date.parse(o.last_verified)>7*86400000?'Not recently verified — check current availability with the organizer.':'Source listing checked recently; eligibility still needs confirmation.'} Status: {s}. {['Open','Upcoming'].includes(s)?'A future deadline is available.':''}</p>
   <details><summary>Optional personal profile match</summary><h4>Why this opportunity matches the MSc AI profile</h4><ul>{o.relevance_explanation.filter(x=>!x.startsWith('Score is')).map(x=><li key={x}>{x}</li>)}</ul><p className="supporting">Relevance is a prioritization signal, not proof of eligibility or an acceptance probability.</p>
   </details><h4>Qualifications & eligibility</h4><p>{o.required_qualifications}</p><ul>{o.eligibility_evidence.map(x=><li key={x}>{x}</li>)}</ul>
   <p><strong>Graduation timing:</strong> {o.graduation_compatibility?.replaceAll('_',' ')||'needs confirmation'}{o.intake&&o.intake!=='unknown'?' · '+o.intake:''}</p>
   {!!o.skills_not_demonstrated.length&&<p><strong>Interests, not established qualifications:</strong> {o.skills_not_demonstrated.join(', ')}</p>}
   {o.category==='innovation'&&<p><strong>Startup / team:</strong> {o.startup_requirements}</p>}
   <h4>Funding & source evidence</h4><p>{o.funding_evidence||'No verified funding coverage has been extracted. Check the organizer’s conditions.'}</p><p>Salary / amount: {o.salary||'unknown'}</p><p>{o.deadline_evidence}</p>
   {o.review_conflicts?.map(x=><p className="condition-warning" key={x}>{x}</p>)}{o.review_status&&<p>{o.review_status}</p>}
   <p className="supporting">Date precision: {o.deadline_precision}. Original timezone: {o.deadline_timezone||'not verified'}. A date-only deadline uses end of that date for comparison; it does not assert an exact closing time.</p>
   <a className="source-link" href={safeUrl(o.original_url)} target="_blank" rel="noopener noreferrer">Original announcement · {o.source_name}<ExternalLink size={17}/></a>
   {o.review_sources?.filter(u=>u!==o.original_url).map(u=><a className="source-link" href={safeUrl(u)} key={u} target="_blank" rel="noopener noreferrer">Supporting original evidence<ExternalLink size={17}/></a>)}
   <p className="supporting">Source checked {o.last_verified.slice(0,10)}. {o.link_validation}</p>
   <h4>How to apply</h4><p>Open the original announcement for application instructions, required documents and current eligibility conditions.</p>
   {deadline(o)!==null&&<button className="secondary-button" onClick={()=>download(o.id+'.ics',calendar(o),'text/calendar')}><CalendarDays size={19}/>Export Deadline to Calendar</button>}
   <div className="application-tracker"><h4>My private application</h4><label>Application stage<select value={t.stage} onChange={e=>update({stage:e.target.value,saved:true})}>{Object.entries(stageLabels).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label>Preparation deadline<input type="date" value={t.preparationDeadline} onChange={e=>update({preparationDeadline:e.target.value,saved:true})}/></label><label>Personal notes<textarea placeholder="Next steps, questions, and ideas…" maxLength={20000} value={t.notes} onChange={e=>update({notes:e.target.value,saved:true})}/></label><p className="supporting">Saved only in this browser. Export your tracker to back it up or transfer it. Notes are never added to the public database.</p></div>
  </div>}
 </article>
}
