import type {Opportunity} from './types';
import {deadline,status} from './logic';
export const categories=['All Opportunities','Scholarships & PhDs','Research','Jobs & Internships','Competitions & Grants'];
export function categoryMatch(o:Opportunity,c:string){
 if(c===categories[1])return /PhD|scholarship|studentship/i.test(o.subcategory+' '+o.title);
 if(c===categories[2])return o.category==='research';
 if(c===categories[3])return o.category==='industry'||o.subcategory==='internship';
 if(c===categories[4])return o.category==='innovation'||/grant|accelerator/i.test(o.title);
 return true;
}
export function countryName(value:string){return ({UK:'United Kingdom',USA:'United States',US:'United States'} as Record<string,string>)[value]||value}
export const searchKey=(v:string)=>v.normalize('NFKD').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();
export function matchesQuery(o:Opportunity,q:string){const text=searchKey([o.title,o.organization,countryName(o.host_country),o.host_country,o.location,...o.tags].join(' '));return searchKey(q).split(' ').every(w=>text.includes(w))}
export function available(o:Opportunity,now:number){return !['Closed','Expired'].includes(status(o,now))}
export function publicRank(o:Opportunity,now:number){
 const age=Math.max(0,(now-Date.parse(o.last_verified))/86400000),d=deadline(o),days=d===null?Infinity:(d-now)/86400000;
 const senior=/\b(senior|staff|principal|director|head of|manager|postdoc)\b/i.test(o.title);
 return (senior?-35:15)+(o.category==='research'?8:0)+(o.fully_funded_verified?10:0)+(days>0&&days<=7?25:days<=30?12:0)+Math.max(0,14-age);
}
// Take turns across publishers. Personal CV scores never gate the public feed.
export function diverseRank(rows:Opportunity[],now:number){
 const sorted=[...rows].sort((a,b)=>publicRank(b,now)-publicRank(a,now)||a.id.localeCompare(b.id));
 const groups=new Map<string,Opportunity[]>();for(const o of sorted){const key=o.organization==='unknown'?o.source_id:o.organization;groups.set(key,[...(groups.get(key)||[]),o])}
 const out:Opportunity[]=[];while(out.length<rows.length)for(const group of groups.values()){const o=group.shift();if(o)out.push(o)}return out;
}
