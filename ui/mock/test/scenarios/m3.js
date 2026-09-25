const c=T.find('Cortex','nav button'); c.click(); await wait(300); c.focus();
c.dispatchEvent(new KeyboardEvent('keydown',{key:'k',metaKey:true,bubbles:true})); await wait(300);
return 'focus: '+document.activeElement.getAttribute('aria-label')+' dialogs='+JSON.stringify(T.dialogs());
