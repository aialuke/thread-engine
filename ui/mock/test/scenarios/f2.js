const out=[]; try {
const setv=(el,v)=>{const d=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value');d.set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};
const approve=async()=>{ let b=T.find('Hold to approve'); b.focus(); b.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); for(let i=0;i<60 && !T.has(/Approved at/);i++) await wait(100); b.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',bubbles:true})); };
T.setNow('2026-09-25T05:45:00+10:00'); await wait(300);
T.click('Preview'); await wait(300); await approve(); await wait(200);
out.push('#46 focus after approve: '+document.activeElement.textContent.trim().slice(0,30));
// Plan running blocks Start posting (G3)
T.click('Today'); await wait(200); T.click('Plan the next post'); await wait(300);
const sp=T.find('Start posting'); out.push('#16 Start posting disabled while Plan runs: '+sp.disabled); sp.click(); await wait(300);
out.push('   plan still running: '+T.has(/Running the daily snapshot|Reading the loop status|Searching X|Checking the queue|Picking the time/));
for(let i=0;i<100 && !T.find('Accept');i++) await wait(100);
out.push('   proposal arrives: '+!!T.find('Accept'));
// B1: start posting, edit is locked during checks
T.click('Start posting'); await wait(200); T.click('Preview'); await wait(200);
const eb=T.find('Edit a card'); out.push('#1 Edit disabled during checks: '+(eb&&eb.disabled)); if(eb) eb.click(); await wait(200); out.push('   editor opened: '+(T.dialogs().length>0));
for(let i=0;i<80 && !T.has(/The final checks passed/);i++) await wait(100);
out.push('   checks: '+T.grab(/The final checks passed[^\n]*|The final check stopped[^\n]*/));
// M3 way back
out.push('#12 back options: '+!!T.find('Not now')+'/'+!!T.find('Withdraw approval'));
T.click('Not now'); await wait(300); out.push('   Not now → '+T.grab(/Approved at[^\n]*|Needs your approval/));
T.click('Today'); await wait(200); T.click('Start posting'); for(let i=0;i<80 && !T.has(/The final checks passed/);i++) await wait(100);
// copy (clipboard granted) and m7
out.push('#39 posted-it before copy: '+!!T.find("I’ve posted it")+'/'+!!T.find("I've posted it"));
T.click('Copy the post'); await wait(400); out.push('   copy: '+T.grab(/Copied[^\n]*|Couldn.t copy[^\n]*/)+' | focus: '+document.activeElement.textContent.trim().slice(0,20));
T.click('posted it'); for(let i=0;i<80 && !T.has(/Found it/);i++) await wait(100);
out.push('   '+T.grab(/Found it[^\n]*/)+' | timer '+T.grab(/\b\d+:\d\d\b/)+' | window '+T.grab(/between \d\d:\d\d and \d\d:\d\d/));
T.setNow('2026-09-25T05:57:00+10:00'); await wait(1300); out.push('#14 timer after 12 real-min jump (from post time): '+T.grab(/\b\d+:\d\d\b(?=\n)/)+' shoutout step: '+!!T.find('Copy the shout-out'));
T.setNow('2026-09-25T06:10:00+10:00'); await wait(1300); out.push('   window closed note: '+T.grab(/The window closed[^\n]*/));
T.click('Copy the shout-out'); for(let i=0;i<80 && !T.has(/Stay close for the first hour/);i++) await wait(100);
out.push('   after shout-out: '+T.head().split(' | ')[2]+' | hint: '+T.grab(/The first full read[^\n]*/)+' | when: '+T.grab(/Posted \d\d:\d\d/));
out.push('#13 first hour open: '+T.has(/First hour/)); T.setNow('2026-09-25T07:05:00+10:00'); await wait(1300); out.push('   after close time: '+T.has(/First hour/));
} catch(e){ out.push('ERR '+e.message+' '+(e.stack||'').split('\n')[1]); } return out.join('\n');
