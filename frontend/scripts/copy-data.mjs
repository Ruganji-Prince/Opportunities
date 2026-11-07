import { mkdir,copyFile } from 'node:fs/promises';
const target=new URL('../public/data/',import.meta.url);
await mkdir(target,{recursive:true});
for(const name of ['opportunities','archived_opportunities','refresh_status']) await copyFile(new URL(`../../data/${name}.json`,import.meta.url),new URL(`${name}.json`,target));
