const { chromium } = require('playwright-core'); const fs=require('fs'), path=require('path');
(async()=>{ const [dir,out,cols,w]=process.argv.slice(2); const files=fs.readdirSync(dir).filter(f=>f.endsWith('.png')).sort();
 const html=`<body style="margin:0;background:#888;display:grid;grid-template-columns:repeat(${cols},${w}px);gap:6px;padding:6px">`+files.map(f=>`<div style="font:11px sans-serif;color:#fff">${f}<br><img src="file://${path.resolve(dir,f)}" style="width:${w}px"></div>`).join('')+'</body>';
 fs.writeFileSync(out+'.html',html);
 const b=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--allow-file-access-from-files']});
 const p=await (await b.newContext({viewport:{width:cols*(+w+6)+12,height:800}})).newPage(); await p.goto('file://'+path.resolve(out+'.html')); await p.waitForTimeout(500); await p.screenshot({path:out+'.png',fullPage:true}); await b.close(); })();
