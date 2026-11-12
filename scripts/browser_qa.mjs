// Real Chrome DevTools QA using Node's native WebSocket; no extra browser packages.
import {spawn} from 'node:child_process';
import {createServer} from 'node:http';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url)),dist=path.join(root,'frontend/dist'),output=path.join(root,'.tools/qa');
await mkdir(output,{recursive:true});
const server=createServer(async(req,res)=>{try{const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);const filename=path.resolve(dist,'.'+(pathname==='/'?'/index.html':pathname));if(!filename.startsWith(dist+path.sep)){res.writeHead(403).end();return}const body=await readFile(filename);res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'})[path.extname(filename)]||'application/octet-stream');res.end(body)}catch{res.writeHead(404).end()}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const url=process.env.RADAR_QA_URL||`http://127.0.0.1:${server.address().port}/`;
const profile=path.join(output,'chrome-'+Date.now());await mkdir(profile);
const browser=spawn(process.env.CHROME_BINARY||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let ws;
try{
 let port;for(let i=0;i<100;i++){try{port=(await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break}catch{await pause(100)}}
 if(!port)throw Error('Chrome did not start');
 const tabs=await(await fetch(`http://127.0.0.1:${port}/json`)).json();const tab=tabs.find(t=>t.type==='page');
 ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
 let seq=0;const pending=new Map();const runtimeErrors=[];
 ws.onmessage=event=>{const m=JSON.parse(event.data);if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}}else if(m.method==='Runtime.exceptionThrown')runtimeErrors.push(m.params)};
 const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))});
 const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const assert=async(expression,message)=>{if(!await evaluate(expression)){console.error('Browser exceptions:',JSON.stringify(runtimeErrors));console.error('Page state:',await evaluate(`document.body.innerText.slice(-2500)`));throw Error(message)}console.log('PASS',message)};
 const click=async text=>evaluate(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()===${JSON.stringify(text)}||b.querySelector('span')?.textContent===${JSON.stringify(text)})?.click()`);
 await call('Runtime.enable');await call('Page.enable');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url});
 for(let i=0;i<100;i++){if(await evaluate(`document.querySelectorAll('.opportunity-card').length>0`))break;await pause(100)}
 await assert(`document.querySelectorAll('.opportunity-card').length>0`,'production feed renders cards');

 await assert(`document.querySelectorAll('main .opportunity-card').length===12`,'initial results limited to 12 cards');
 await assert(`!document.querySelector('main .opportunity-card .description')&&!document.querySelector('main .opportunity-card textarea')`,'cards contain essentials without descriptions or private tracking controls');
 await assert(`new Set([...document.querySelectorAll('main .card-org strong')].map(x=>x.textContent)).size>=4`,'homepage includes diverse publishers');
 await evaluate(`(()=>{const s=document.querySelector('[aria-label="Sort opportunities"]');Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(s,'earliest');s.dispatchEvent(new Event('change',{bubbles:true}))})()`);await pause(150);
 await evaluate(`(async()=>{window.__feed=await(await fetch(new URL('data/listings.json',location.href))).json();window.__manifest=await(await fetch(new URL('data/manifest.json',location.href))).json();return true})()`);
 await assert(`new Set(window.__feed.map(o=>o.id)).size===window.__feed.length`,'public feed has no duplicate IDs');
 await assert(`(()=>{const rows=[...document.querySelectorAll('main .opportunity-card')].map(x=>window.__feed.find(o=>o.id===x.dataset.opportunityId));return rows.every((o,i)=>!i||!rows[i-1].deadline||!o.deadline||rows[i-1].deadline.slice(0,10)<=o.deadline.slice(0,10))})()`,'earliest-deadline sorting works');
 await assert(`document.documentElement.scrollWidth<=innerWidth`,'desktop has no horizontal overflow');
 await assert(`parseFloat(getComputedStyle(document.body).fontSize)>=17&&parseFloat(getComputedStyle(document.querySelector('.opportunity-card h3')).fontSize)>=20`,'body and card title typography are readable');
 await writeFile(path.join(output,'desktop.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 await evaluate(`window.__savedID=document.querySelector('main .opportunity-card').dataset.opportunityId;document.querySelector('main .save-button').click()`);await pause(100);await click('Saved');await pause(150);
 await assert(`document.querySelectorAll('main .opportunity-card').length===1`,'bookmark appears in Saved');
 await evaluate(`document.querySelector('main .card-actions button').click()`);
 for(let i=0;i<100;i++){if(await evaluate(`!!document.querySelector('dialog textarea')`))break;await pause(100)}
 await assert(`document.querySelector('dialog').open&&!!document.querySelector('dialog textarea')`,'accessible modal loads detail and tracker on demand');
 await assert(`new URL(location.href).searchParams.get('opportunity')===window.__savedID`,'details have a stable shareable link');
 await evaluate(`(()=>{const input=document.querySelector('textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(input,'QA private note');input.dispatchEvent(new Event('input',{bubbles:true}))})()`);await pause(150);
 await assert(`Object.values(JSON.parse(localStorage.getItem('opportunityradar-tracker-v1'))).some(t=>t.notes==='QA private note')`,'private notes persist in existing tracker schema');
 const shared=await evaluate(`location.href`);await call('Page.reload');await pause(500);
 for(let i=0;i<100;i++){if(await evaluate(`!!document.querySelector('dialog textarea')`))break;await pause(100)}
 await assert(`document.querySelector('dialog').open&&document.querySelector('textarea').value==='QA private note'`,'direct shared URL restores details and private local tracking');
 await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await pause(100);
 await assert(`!document.querySelector('dialog').open`,'Escape closes details');
 await click('Saved');await pause(150);await assert(`document.querySelectorAll('main .opportunity-card').length===1`,'bookmark survives reload');
 await click('Home');await pause(100);
 await evaluate(`(()=>{const input=document.querySelector('[aria-label="Search opportunities"]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,'NO_MATCH_8e60adc');input.dispatchEvent(new Event('input',{bubbles:true}))})()`);await pause(150);
 await assert(`document.querySelectorAll('main .opportunity-card').length===0&&document.body.innerText.includes('No opportunities match')`,'search empty state works');
 await click('Reset filters');await pause(100);await click('Scholarships & PhDs');await pause(100);
 await assert(`document.querySelectorAll('main .opportunity-card').length>0&&[...document.querySelectorAll('main .opportunity-card')].every(n=>/PhD|scholarship|studentship/i.test(n.innerText))`,'scholarship and PhD category filters actual listings');
 await click('All Opportunities');await click('Load More');await pause(100);
 await assert(`document.querySelectorAll('main .opportunity-card').length===24`,'Load More adds twelve results');
 await click('Top Opportunities for You');await pause(150);
 await assert(`!!document.querySelector('[aria-label="Personal opportunity collection"]')&&document.body.innerText.includes('Personal research dashboard')`,'personal research collections remain available');
 await assert(`document.querySelectorAll('main .opportunity-card').length>0&&!!document.querySelector('.personal-card-facts')`,'verified personal selections show qualifications and eligibility');
 await evaluate(`(()=>{const el=document.querySelector('[aria-label="Personal opportunity collection"]');Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(el,'Fully Funded PhDs');el.dispatchEvent(new Event('change',{bubbles:true}))})()`);await pause(150);
 await assert(`document.querySelectorAll('main .opportunity-card').length>0&&[...document.querySelectorAll('main .opportunity-card')].every(x=>x.innerText.includes('Fully funded'))`,'verified fully funded doctoral collection works');
 await click('Browse public opportunities');await pause(100);
 await click('About');await pause(150);await assert(`document.querySelectorAll('.source-card').length>=17`,'operational source status is separated onto About');await click('Home');await pause(150);
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:true});await pause(200);
 await assert(`innerWidth===390&&document.documentElement.scrollWidth<=390`,'phone layout fits 390px viewport');
 await evaluate(`document.documentElement.style.fontSize='34px'`);await pause(200);
 await assert(`document.documentElement.scrollWidth<=innerWidth`,'200% text scaling on phone has no horizontal scrolling');
 await writeFile(path.join(output,'mobile-200.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 await evaluate(`document.documentElement.style.fontSize=''`);await pause(100);await writeFile(path.join(output,'mobile.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 await evaluate(`document.querySelector('[aria-label="Toggle navigation"]').click()`);await pause(100);await assert(`getComputedStyle(document.querySelector('.site-header nav')).display!=='none'`,'mobile menu opens');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});await evaluate(`document.documentElement.style.fontSize='34px'`);await pause(150);await assert(`document.documentElement.scrollWidth<=innerWidth`,'desktop 200% text scaling fits');
 if(runtimeErrors.length)throw Error('Browser runtime errors: '+JSON.stringify(runtimeErrors));console.log('PASS no browser JavaScript exceptions');console.log('Shared URL tested:',shared);console.log('Screenshots:',output);
}finally{ws?.close();browser.kill();await new Promise(resolve=>server.close(resolve))}
