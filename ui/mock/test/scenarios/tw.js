const out=[]; try {
const approve=async()=>{ let b=T.find('Hold to approve'); b.focus(); b.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); for(let i=0;i<60 && !T.has(/Approved at/);i++) await wait(100); b.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',bubbles:true})); };
const mode=location.pathname;
if (/draftfail|factcheck/.test(mode)) {
  T.click('Posts','nav button'); await wait(300); T.click('Draft'); for(let i=0;i<120 && !T.has(/Stopped at|Drafted/);i++) await wait(100);
  out.push(mode+': '+T.grab(/Stopped at[^\n]*/)+' | '+T.grab(/The fact-check couldn’t confirm[^\n]*|The fact-check couldn't confirm[^\n]*/)+' | '+T.grab(/Drafted · next in line/));
  if (T.find('Try again')) { T.click('Try again'); for(let i=0;i<120 && !T.has(/Drafted · next/);i++) await wait(100); out.push('   after retry: '+T.grab(/Drafted · next in line/)); }
  return out.join('\n');
}
if (/health/.test(mode)) { return mode+': '+T.head()+' | dot label: '+T.find('EZ, settings and health').getAttribute('aria-label'); }
T.setNow('2026-09-25T05:45:00+10:00'); await wait(300);
T.click('Preview'); await wait(300); await approve(); T.click('Start posting'); for(let i=0;i<80 && !T.has(/The final check stopped|The final checks passed/);i++) await wait(100);
if (/refused/.test(mode)) { out.push(mode+': '+T.grab(/The final check stopped[^\n]*\n[^\n]*/).replace('\n',' / ')); return out.join('\n'); }
T.click('Copy the post'); await wait(400); T.click('posted it'); for(let i=0;i<80 && !T.has(/Found it|Not on X yet/);i++) await wait(100);
if (/notfound/.test(mode)) { out.push(mode+': '+T.grab(/Not on X yet[^\n]*/)); T.click('Check again'); for(let i=0;i<80 && !T.has(/Found it/);i++) await wait(100); }
out.push(mode+': '+T.grab(/Found it[^\n]*/)+' | '+T.grab(/It isn.t the same[^\n]*|Two posts on X match[^\n]*/));
} catch(e){ out.push('ERR '+e.message); } return out.join('\n');
