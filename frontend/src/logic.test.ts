import {describe,it,expect} from 'vitest';
import {deadline,status,compare,parseTracking,safeUrl} from './logic';
import type {Opportunity} from './types';
const make=(x:Partial<Opportunity>={}):Opportunity=>({id:'0123456789abcdef0123',deadline:'2026-11-09T12:00:00Z',deadline_precision:'timestamp',deadline_timezone:null,application_status:'unknown',relevance_score:80,...x} as Opportunity);
describe('deadline display and automatic ordering',()=>{
 it('expires and leaves the active list when the clock passes',()=>{const a=make();const b=make({id:'b',deadline:'2026-11-10T12:00:00Z'});const active=(now:number)=>[a,b].filter(o=>!['Expired','Closed'].includes(status(o,now))).sort((x,y)=>compare(x,y,'deadline'));expect(active(Date.parse('2026-11-09T11:59:00Z'))[0]).toBe(a);expect(active(Date.parse('2026-11-09T12:00:00Z'))[0]).toBe(b)});
 it('handles equivalent timezones',()=>expect(deadline(make({deadline:'2026-11-09T07:00:00-05:00'}))).toBe(deadline(make())));
 it('preserves date-only end of day Kigali convention',()=>expect(deadline(make({deadline:'2026-11-09',deadline_precision:'date'}))).toBe(Date.parse('2026-11-09T22:00:00Z')));
 it('handles DST in original timezone',()=>expect(deadline(make({deadline:'2026-03-08',deadline_precision:'date',deadline_timezone:'America/New_York'}))).toBe(Date.parse('2026-03-09T04:00:00Z')));
 it('places unknown after rolling after dated',()=>{const a=make(),b=make({deadline:null,deadline_precision:'rolling'}),c=make({deadline:null,deadline_precision:'unknown'});expect([c,b,a].sort((x,y)=>compare(x,y,'deadline'))).toEqual([a,b,c])});
 it('breaks date ties by relevance',()=>expect(compare(make({relevance_score:90}),make({relevance_score:60}),'deadline')).toBeLessThan(0));
 it('returns empty results for no matches',()=>expect([make()].filter(o=>o.relevance_score>100)).toEqual([]));
 it('rejects unsafe URLs and invalid imports',()=>{expect(safeUrl('javascript:alert(1)')).toBe('#');expect(()=>parseTracking({bad:{}})).toThrow()});
 it('round trips validated private records',()=>{const input={'0123456789abcdef0123':{saved:true,stage:'preparing',notes:'Private',preparationDeadline:'2026-11-08'}};expect(parseTracking(JSON.parse(JSON.stringify(input)))).toEqual(input)});
});
