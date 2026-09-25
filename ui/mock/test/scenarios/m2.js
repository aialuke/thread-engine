const out=[]; try {
const setv=(el,v)=>{const d=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value');d.set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};
const m=T.main(); m.scrollTop=0;
T.click('Read and approve'); await wait(900);
out.push('#15 Read and approve: focus='+(document.activeElement.textContent||'').trim().slice(0,30)+' scrolled='+m.scrollTop);
(document.activeElement||T.root()).dispatchEvent(new KeyboardEvent('keydown',{key:'k',metaKey:true,bubbles:true})); await wait(300);
out.push('#22 cmdK: dialogs='+JSON.stringify(T.dialogs())+' focus='+document.activeElement.getAttribute('aria-label')+' sidebar inert='+document.querySelector('.te-root nav').getAttribute('inert'));
document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})); await wait(300); out.push('   Esc: '+JSON.stringify(T.dialogs()));
out.push('#34 sidebar: '+T.grab(/27 (of|\/) 500/)+' | kbd hint: '+T.has(/⌘K/));
T.click('Cortex','nav button'); await wait(300); out.push('#42 cortex overflow: '+JSON.stringify(T.overflow()));
(document.activeElement||T.root()).dispatchEvent(new KeyboardEvent('keydown',{key:'k',metaKey:true,bubbles:true})); await wait(300); out.push('   cmdK on Cortex focuses docked input: '+document.activeElement.getAttribute('aria-label')+' dialogs='+JSON.stringify(T.dialogs()));
T.click('Posts','nav button'); await wait(300); T.click('Choose a hook'); await wait(300); out.push('E4 hook modal: '+JSON.stringify(T.dialogs())+' focus='+document.activeElement.getAttribute('role')); document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true})); await wait(200);
// B1 on Mac
T.click('Today','nav button'); await wait(300); T.setNow('2026-09-25T05:45:00+10:00'); await wait(1200);
let b=T.find('Hold to approve'); b.focus(); b.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); for(let i=0;i<60 && !T.has(/Approved at/);i++) await wait(100); b.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',bubbles:true}));
T.click('Start posting'); await wait(300); const eb=T.find('Edit a card'); out.push('#1 Mac edit during checks: '+(eb?('disabled='+eb.disabled):'not shown'));
for(let i=0;i<80 && !T.has(/The final checks passed|The final check stopped/);i++) await wait(100); out.push('   '+T.grab(/The final checks passed[^\n]*/)+' | back: '+!!T.find('Not now'));
} catch(e){ out.push('ERR '+e.message); } return out.join('\n');
