import type {Opportunity} from './types';
import {status,deadline,compare} from './logic';

export function activeMatch(o:Opportunity,now:number,minimum=55){return !['Expired','Closed'].includes(status(o,now))&&o.eligibility!=='restricted'&&o.graduation_compatibility!=='incompatible'&&o.relevance_score>=minimum}
export function reviewed(o:Opportunity,now:number){return !!o.reviewed_at&&now-Date.parse(o.reviewed_at)<7*86400000&&!!o.review_sources?.length}
export function priority(o:Opportunity,now:number){
 const d=deadline(o);const urgent=d!==null&&d>now&&d-now<=7*86400000?4:0;
 return (o.recommendation_score??o.relevance_score)+urgent;
}
export function topOpportunities(records:Opportunity[],now:number,limit=12){
 const pool=records.filter(o=>activeMatch(o,now)&&reviewed(o,now)&&!o.assessment?.startup_required);
 pool.sort((a,b)=>priority(b,now)-priority(a,now)||compare(a,b,'deadline'));
 const selected:Opportunity[]=[];const employers=new Map<string,number>();let industry=0;
 // Research and internship rankings remain distinct; ordinary corporate vacancies cannot dominate.
 for(const o of pool){
  const employer=o.organization==='unknown'?o.source_name:o.organization;
  const corporate=o.category==='industry'&&o.subcategory!=='internship';
  if((employers.get(employer)||0)>=3||(corporate&&industry>=2))continue;
  selected.push(o);employers.set(employer,(employers.get(employer)||0)+1);if(corporate)industry++;
  if(selected.length>=limit)break;
 }
 return selected;
}
export function inSection(o:Opportunity,view:string,now:number){
 if(view==='Fully Funded PhDs')return o.subcategory==='PhD'&&!!o.fully_funded_verified&&reviewed(o,now);
 if(view==='Fall 2027 Doctoral Opportunities')return o.subcategory==='PhD'&&/2027/.test(o.intake||'')&&o.graduation_compatibility!=='incompatible';
 if(view==='Research Assistantships & Fellowships')return o.category==='research'&&o.subcategory!=='PhD';
 if(view==='AI/ML Internships')return o.subcategory==='internship';
 if(view==='Rwanda & East Africa')return o.geographic_scope.some(x=>['Rwanda','East Africa'].includes(x));
 if(view==='Research & PhD')return o.category==='research';
 if(view==='Jobs & Internships')return o.category==='industry'||o.subcategory==='internship';
 if(view==='Innovation & Hackathons')return o.category==='innovation';
 if(view==='Closing Soon')return activeMatch(o,now)&&['Urgent','Closing Soon'].includes(status(o,now));
 return true;
}
export function labels(o:Opportunity,now:number){
 const result:string[]=[];
 if(o.category==='research'&&o.relevance_score>=85&&o.eligibility!=='restricted')result.push('Excellent Research Match');
 if(o.fully_funded_verified&&reviewed(o,now))result.push('Fully Funded — Verified');
 if(o.intake&&o.intake!=='unknown')result.push(o.intake);
 if(o.eligibility==='unknown'||o.eligibility==='likely'||o.eligibility_conditions?.length)result.push('Eligibility Needs Confirmation');
 return result.slice(0,3);
}
