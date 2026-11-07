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
const url=`http://127.0.0.1:${server.address().port}/`;
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
 const assert=async(expression,message)=>{if(!await evaluate(expression))throw Error(message);console.log('PASS',message)};
 const click=async text=>evaluate(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()===${JSON.stringify(text)}||b.querySelector('span')?.textContent===${JSON.stringify(text)})?.click()`);
 await call('Runtime.enable');await call('Page.enable');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url});
 for(let i=0;i<100;i++){if(await evaluate(`document.querySelectorAll('.opportunity-card').length>0`))break;await pause(100)}
 await assert(`document.querySelectorAll('.opportunity-card').length>0`,'production feed renders cards');
 await assert(`document.documentElement.scrollWidth<=innerWidth`,'desktop has no horizontal overflow');
 await writeFile(path.join(output,'desktop.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 await evaluate(`document.querySelector('.save-button').click()`);await pause(150);await click('Saved');await pause(150);
 await assert(`document.querySelectorAll('.opportunity-card').length===1`,'bookmark appears in Saved');
 await click('View details');await pause(100);
 await assert(`document.querySelector('textarea')!==null`,'application tracker expands');
 await evaluate(`(()=>{const input=document.querySelector('textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(input,'QA private note');input.dispatchEvent(new Event('input',{bubbles:true}))})()`);await pause(150);
 await assert(`Object.values(JSON.parse(localStorage.getItem('opportunityradar-tracker-v1'))).some(t=>t.notes==='QA private note')`,'notes persist in browser storage');
 await call('Page.reload');await pause(800);
 await click('Saved');await pause(150);await assert(`document.querySelectorAll('.opportunity-card').length===1`,'bookmark survives reload');
 await click('All Opportunities');await pause(150);
 await evaluate(`(()=>{const input=document.querySelector('input[aria-label="Search opportunities"]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,'NO_MATCH_8e60adc');input.dispatchEvent(new Event('input',{bubbles:true}))})()`);await pause(150);
 await assert(`document.querySelectorAll('.opportunity-card').length===0&&document.body.innerText.includes('No opportunities match')`,'empty search displays useful state');
 await click('Reset filters');await pause(150);await click('Sources');await pause(150);
 await assert(`document.querySelectorAll('.source-card').length>=6`,'source health directory renders');
 await click('Overview');await pause(150);
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:true});await pause(300);
 await assert(`innerWidth===390&&document.documentElement.scrollWidth<=390`,'phone layout fits a 390px viewport');
 await writeFile(path.join(output,'mobile.png'),Buffer.from((await call('Page.captureScreenshot',{format:'png'})).data,'base64'));
 if(runtimeErrors.length)throw Error('Browser runtime errors: '+JSON.stringify(runtimeErrors));console.log('PASS no browser JavaScript exceptions');
 console.log('Screenshots:',output);
}finally{ws?.close();browser.kill();await new Promise(resolve=>server.close(resolve))}
