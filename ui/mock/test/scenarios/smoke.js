const r = T.root(); if (!r) return 'NO ROOT: ' + document.body.innerText.slice(0,300);
return [T.head(), 'main inert attr: ' + T.main().getAttribute('inert'), 'nav inert: ' + (document.querySelector('.te-root nav')||{}).getAttribute?.('inert'), JSON.stringify(T.overflow())].join('\n');
