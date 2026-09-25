const out=[]; try {
const setv=(el,v)=>{const d=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value');d.set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};
const nav=(n)=>T.click(n,'nav button');
// capture
T.click('Capture something'); await wait(300);
out.push('#25 default kind: '+[...T.main().querySelectorAll('[role=radio]')].filter(e=>e.getAttribute('aria-checked')==='true').map(e=>e.textContent.trim()).join(','));
const caps=()=>T.main().innerText.split(/\n+/).filter(l=>/· example|^Just a note$|^Voice note$|Turn into|Queued/.test(l)).join(' / ');
[...T.main().querySelectorAll('button')].filter(e=>/^Turn into a post/.test(e.textContent.trim()))[0].click(); await wait(200);
setv(T.main().querySelector('textarea'),'Typed a quick note'); await wait(100); T.click('Save capture'); await wait(300);
out.push('   after turn + add: '+caps());
// replies
nav('Replies'); await wait(300); T.click('Answered'); await wait(200); T.click('Not answering'); await wait(200);
out.push('#38 closed rows: '+T.main().innerText.split('\n').filter(l=>/· (Answered|Not answering)$/.test(l)).join(' | ')+' | badge label: '+T.find('Replies','nav button').getAttribute('aria-label'));
T.click('Undo'); await wait(200); out.push('   after undo: '+T.find('Replies','nav button').getAttribute('aria-label'));
out.push('#4 builders: '+T.grab(/mutuals on topic[^\n]*/)+'\n#6 footer: '+T.grab(/Your busiest 24 hours[^\n]*/)+'\n#7: '+T.grab(/Plus 37[^\n]*/));
// results
nav('Results'); await wait(300);
out.push('E3 D18: '+T.grab(/Every profile visit[^\n]*/)+' | #29 '+T.grab(/2[12]–24 Sep/));
const tabs=[...T.root().querySelectorAll('[role=tab]')]; tabs[0].focus(); tabs[0].dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true})); await wait(300);
out.push('#45 arrow key: selected='+[...T.root().querySelectorAll('[role=tab]')].map(t=>t.textContent+':'+t.getAttribute('aria-selected')+':'+t.getAttribute('tabindex')).join(' ')+' focus='+document.activeElement.textContent+' panel='+(T.root().querySelector('[role=tabpanel]')||{}).getAttribute?.('aria-label'));
out.push('#5 A8: '+T.grab(/The target is yours[^\n]*/));
out.push('#16 posts order: '+T.main().innerText.split('\n').filter(l=>/follows? · \d+ visits? ·/.test(l)).slice(0,5).join(' | '));
T.click('Show as table'); await wait(300);
out.push('#21 tables: posts tab '+T.main().querySelectorAll('table').length);
T.click('Growth','[role=tab]'); await wait(200); out.push('   growth tab '+T.main().querySelectorAll('table').length);
T.click('Replies','[role=tab]'); await wait(200); out.push('   replies tab '+T.main().querySelectorAll('table').length); T.click('Show charts'); await wait(200);
out.push('#40 replies chart: '+T.main().innerText.split('\n').filter(l=>/visits? ·/.test(l)).join(' | ')+' | overflow: '+JSON.stringify(T.overflow()));
// review needs-you
T.click("Write this week’s review")||T.click("Write this week's review"); for(let i=0;i<120 && !T.has(/Needs you\./);i++) await wait(100);
out.push('#18 needs you: '+T.grab(/Needs you\.[^\n]*/)); T.click('Use 24 Sep'); await wait(400); out.push('   answered → '+T.grab(/Review written/));
// posted list + hook
nav('Posts'); await wait(300);
const pl=T.main().innerText.split('Posted\n')[1]||''; out.push('#37 posted order: '+(pl.match(/(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d+/g)||[]).join(', '));
T.click('Choose a hook'); await wait(300); out.push('E4 hook sheet: '+JSON.stringify(T.dialogs())+' focus='+document.activeElement.tagName);
[...T.root().querySelectorAll('[role=dialog] [role=radio]')][2].click(); await wait(150); T.click('Use this hook'); await wait(300);
out.push('   chosen: '+T.grab(/“I asked three[^\n]*/)+' | '+T.grab(/Hook chosen[^\n]*/));
out.push('#36 queue: '+T.grab(/Ollama[^\n]*/));
} catch(e){ out.push('ERR '+e.message+' '+(e.stack||'').split('\n')[1]); } return out.join('\n');
