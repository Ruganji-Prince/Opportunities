import {mkdir,readFile,writeFile,rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const target=new URL('../public/data/',import.meta.url);
await rm(target,{recursive:true,force:true});await mkdir(new URL('details/',target),{recursive:true});
const load=async n=>JSON.parse(await readFile(new URL(`../../data/${n}.json`,import.meta.url),'utf8'));
const active=await load('opportunities'),archived=await load('archived_opportunities'),health=await load('refresh_status');
const listings=[];
for(const original of [...active,...archived]){
 const o={...original};
 // Public summaries are factual templates, not full copyrighted source descriptions.
 o.description=`${o.organization==='unknown'?o.source_name:o.organization} lists ${o.title} in ${o.location}. Category: ${o.subcategory}. Consult the original announcement for the full role, application instructions and eligibility.`;
 for(const key of ['required_qualifications','funding_evidence','deadline_evidence','startup_requirements'])if(typeof o[key]==='string')o[key]=o[key].slice(0,600);
 delete o.provenance;delete o.identity_urls;
 await writeFile(new URL(`details/${o.id}.json`,target),JSON.stringify(o));
 const {description,eligibility_evidence,skills_not_demonstrated,startup_requirements,funding_evidence,deadline_evidence,review_conflicts,review_status,...listing}=o;
 listings.push(listing);
}
const text=JSON.stringify(listings),version=createHash('sha256').update(text+JSON.stringify(health)).digest('hex').slice(0,20);
await writeFile(new URL('listings.json',target),text);
await writeFile(new URL('refresh_status.json',target),JSON.stringify(health));
await writeFile(new URL('manifest.json',target),JSON.stringify({version,last_successful_refresh:health.last_successful_refresh,active:active.length}));
console.log(`Public feed: ${active.length} active, ${archived.length} archived, ${(Buffer.byteLength(text)/1024).toFixed(0)} KiB listings; details load on demand.`);
