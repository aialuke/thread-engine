// node shots.js <page> <scheme> <outdir>
const { chromium } = require('playwright-core'); const fs=require('fs');
(async()=>{ const [pg, scheme, dir]=process.argv.slice(2); fs.mkdirSync(dir,{recursive:true});
 const b=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const c=await b.newContext({viewport:{width:1500,height:1000},colorScheme:scheme,timezoneId:'Australia/Brisbane',deviceScaleFactor:1});
 const p=await c.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message));
 await p.goto('http://127.0.0.1:8766/'+pg); await p.waitForSelector('.te-root'); await p.evaluate(()=>document.fonts.ready); await p.addScriptTag({url:'/t.js'});
 const report={};
 const screens=[['Today',null],['Post','Preview'],['Posts',null],['Capture','Capture something'],['Replies',null],['Results-Growth','Growth'],['Results-Posts','Posts'],['Results-Replies','Replies'],['Cortex',null]];
 for (const [name,btn] of screens){
   await p.evaluate(([name,btn])=>{ const nav=n=>T.click(n,'nav button');
     if(name==='Post'){nav('Today'); } else if(name==='Capture'){nav('Today');} else if(name.startsWith('Results')) nav('Results'); else nav(name);
   },[name,btn]); await p.waitForTimeout(250);
   if(btn) { await p.evaluate(([name,btn])=>{ if(name.startsWith('Results')) T.click(btn,'[role=tab]'); else T.click(btn); },[name,btn]); await p.waitForTimeout(250); }
   report[name]=await p.evaluate(()=>T.overflow());
   const main=await p.$('.te-root main'); const root=await p.$('.te-root');
   const h=await main.evaluate(m=>m.scrollHeight), vh=await main.evaluate(m=>m.clientHeight);
   for(let y=0,i=0;y<h;y+=vh-60,i++){ await main.evaluate((m,y)=>m.scrollTop=y,y); await p.waitForTimeout(120); await root.screenshot({path:`${dir}/${name}-${i}.png`}); if(i>6)break; }
   await main.evaluate(m=>m.scrollTop=0);
 }
 console.log(JSON.stringify(report,null,1)); if(errs.length) console.log('ERR',errs); await b.close(); })();
