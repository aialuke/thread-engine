const out=[]; try {
const setv=(el,v)=>{const d=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value');d.set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};
const approve=async()=>{ let b=T.find('Hold to approve'); b.focus(); b.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); for(let i=0;i<60 && !T.has(/Approved at/);i++) await wait(100); b.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',bubbles:true})); };
const nav=(n)=>T.click(n,'nav button');
// M7: edit in a refused phrase, approve, start
T.setNow('2026-09-25T05:45:00+10:00'); await wait(300);
T.click('Preview'); await wait(300); T.click('Change something'); await wait(300);
const ta=T.root().querySelector('[role=dialog] textarea'); setv(ta, ta.value+'\nreply with your stack'); await wait(100); T.click('Save changes'); await wait(300);
await approve(); T.click('Start posting'); for(let i=0;i<80 && !T.has(/The final check stopped|The final checks passed/);i++) await wait(100);
out.push('#3 refused: '+T.grab(/The final check stopped[^\n]*\n[^\n]*/).replace(/\n/g,' / '));
T.click('Read and approve again'); await wait(300); out.push('   back to: '+T.grab(/Needs your approval|Approved at/));
// fix the card, approve, start, back options
T.click('Change something'); await wait(300); const ta2=T.root().querySelector('[role=dialog] textarea'); setv(ta2, ta2.value.replace('\nreply with your stack','')); await wait(100); T.click('Save changes'); await wait(300);
await approve(); T.click('Start posting'); for(let i=0;i<80 && !T.has(/The final checks passed/);i++) await wait(100);
out.push('#12 back options: '+!!T.find('Not now')+'/'+!!T.find('Withdraw approval'));
T.click('Withdraw approval'); await wait(300); out.push('   Withdraw → '+T.grab(/Needs your approval|Approved at[^\n]*/));
// slot missed after approval → move
await approve(); T.setNow('2026-09-25T09:00:00+10:00'); await wait(1300); T.click('Today'); await wait(300);
out.push('#11 missed after approval: '+T.head().split(' | ')[2]+' | primary: '+T.grab(/Move it to[^\n]*/));
T.click('Move it to'); await wait(1300); out.push('   after move: '+T.head().split(' | ')[2]+' | when: '+T.grab(/(Today|Tomorrow|\w{3} \d+ \w{3}), 06:00/)+' | '+T.grab(/in \d+ h \d+ m/));
T.setNow('2026-09-26T09:00:00+10:00'); await wait(1300); out.push('   26 Sep 09:00, slot was 26 Sep 06:00: '+T.head().split(' | ')[2]);
// remind toggle
T.setNow('2026-09-25T21:00:00+10:00'); await wait(1300); out.push('#8 early: '+T.head().split(' | ')[2]+' | '+T.grab(/Remind me at[^\n]*|Reminder set[^\n]*/));
T.click('Remind me at'); await wait(300); out.push('   after tap: '+T.grab(/Reminder set[^\n]*/));
T.click('EZ, settings and health'); await wait(300);
const sw=[...T.root().querySelectorAll('[role=switch]')].map(x=>x.getAttribute('aria-label')+'='+x.getAttribute('aria-checked')); out.push('   settings switches: '+sw.join(', '));
[...T.root().querySelectorAll('[role=switch]')][1].click(); await wait(200); out.push('   nudge after tap: '+[...T.root().querySelectorAll('[role=switch]')][1].getAttribute('aria-checked'));
out.push('   model row: '+T.grab(/Who answers when you ask Cortex\n[^\n]*/).replace('\n',' / ')+' | spend: '+T.grab(/about US\$[0-9.]+/));
document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})); await wait(200);
T.realNow();
// G2 chat
nav('Cortex'); await wait(300); T.click('Ask Cortex'); await wait(300);
const sg=()=>[...T.root().querySelectorAll('[role=dialog] button')].filter(e=>T.vis(e)&&e.textContent.trim().endsWith('?'));
out.push('#17 chat header: '+T.grab(/Cortex\nClaude[^\n]*/).replace('\n',' / ')); sg()[0].click(); await wait(300);
T.click('Done'); await wait(400); T.click('Ask Cortex'); await wait(300);
out.push('   reopen: chips disabled='+sg().map(e=>e.disabled).join(',')+' answer in log='+/Strangers only ever see your first post/.test(T.root().innerText)+' still asking='+T.has(/Reading your weights|Checking the X ranking|Writing an answer/));
T.click('Done'); await wait(200);
} catch(e){ out.push('ERR '+e.message+' '+(e.stack||'').split('\n')[1]); } return out.join('\n');
