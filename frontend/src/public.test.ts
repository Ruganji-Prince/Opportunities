import {describe,it,expect} from 'vitest';
import {available,categoryMatch,countryName,diverseRank,matchesQuery,publicRank} from './public';
import type {Opportunity} from './types';
const now=Date.parse('2026-11-11T12:00:00Z');
const make=(x:Partial<Opportunity>={})=>({id:'0123456789abcdef0123',title:'Machine-learning internship',organization:'Institute',location:'Kigali, Rwanda',host_country:'Rwanda',tags:['AI','data science'],category:'research',subcategory:'internship',deadline:null,deadline_precision:'unknown',application_status:'unknown',last_verified:'2026-11-11T10:00:00Z',relevance_score:0,eligibility:'restricted',...x} as Opportunity);
describe('public discovery independent of private CV matching',()=>{
 it('keeps low personal scores and personal restrictions publicly discoverable',()=>expect(available(make(),now)).toBe(true));
 it('searches location and tolerates punctuation and case',()=>{expect(matchesQuery(make(),'MACHINE learning Rwanda')).toBe(true);expect(matchesQuery(make(),'nonexistent')).toBe(false)});
 it('normalizes equivalent country names',()=>{expect(countryName('UK')).toBe('United Kingdom');expect(countryName('USA')).toBe('United States');expect(matchesQuery(make({host_country:'UK',location:'London'}),'United Kingdom')).toBe(true)});
 it('provides functional category filters',()=>{expect(categoryMatch(make({subcategory:'PhD'}),'Scholarships & PhDs')).toBe(true);expect(categoryMatch(make(),'Jobs & Internships')).toBe(true);expect(categoryMatch(make(),'Competitions & Grants')).toBe(false)});
 it('removes confirmed expiry and closure while retaining unknown deadlines',()=>{expect(available(make({deadline:'2026-11-11T11:00:00Z',deadline_precision:'timestamp'}),now)).toBe(false);expect(available(make({application_status:'closed'}),now)).toBe(false);expect(available(make(),now)).toBe(true)});
 it('prevents one publisher from occupying the first page',()=>{const rows=[...Array.from({length:20},(_,i)=>make({id:String(i),organization:'Big company'})),make({id:'research',organization:'University'}),make({id:'regional',organization:'Regional institute'})];expect(new Set(diverseRank(rows,now).slice(0,3).map(o=>o.organization)).size).toBe(3)});
 it('promotes urgent deadlines and deprioritizes senior roles',()=>{const ordinary=make(),urgent=make({deadline:'2026-11-13T12:00:00Z',deadline_precision:'timestamp'}),senior=make({title:'Senior ML engineer'});expect(publicRank(urgent,now)).toBeGreaterThan(publicRank(ordinary,now));expect(publicRank(senior,now)).toBeLessThan(publicRank(ordinary,now))});
});
