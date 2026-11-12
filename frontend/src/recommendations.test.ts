import {describe,it,expect} from 'vitest';
import {topOpportunities,priority,inSection} from './recommendations';
import type {Opportunity} from './types';
const now=Date.parse('2026-11-12T12:00:00Z');
const make=(x:Partial<Opportunity>={})=>({id:'0123456789abcdef0123',title:'PhD AI research',organization:'University',category:'research',subcategory:'PhD',relevance_score:85,recommendation_score:90,eligibility:'unknown',graduation_compatibility:'needs_confirmation',reviewed_at:'2026-11-12T10:00:00Z',review_sources:['https://example.org/call'],deadline:null,deadline_precision:'unknown',application_status:'unknown',...x} as Opportunity);
describe('evidence-aware personal recommendations',()=>{
 it('never features unreviewed or stale records',()=>{expect(topOpportunities([make({reviewed_at:undefined}),make({reviewed_at:'2026-10-01T00:00:00Z'})],now)).toEqual([])});
 it('removes expiry, academic conflicts and startup requirements',()=>{expect(topOpportunities([make({eligibility:'restricted'}),make({graduation_compatibility:'incompatible'}),make({assessment:{startup_required:true}}),make({deadline:'2026-11-11T00:00:00Z',deadline_precision:'timestamp'})],now)).toEqual([])});
 it('uses urgency only after relevance and eligibility screening',()=>{const urgent=make({deadline:'2026-11-14T12:00:00Z',deadline_precision:'timestamp'});expect(priority(urgent,now)).toBeGreaterThan(priority(make(),now));expect(topOpportunities([make({...urgent,relevance_score:20})],now)).toEqual([])});
 it('requires evidence for fully funded doctoral collection',()=>{expect(inSection(make(),'Fully Funded PhDs',now)).toBe(false);expect(inSection(make({fully_funded_verified:true}),'Fully Funded PhDs',now)).toBe(true)});
 it('limits a single employer in curated selections',()=>{expect(topOpportunities(Array.from({length:10},(_,i)=>make({id:String(i)})),now)).toHaveLength(3)});
});
