const secs=[...document.querySelectorAll('section')].map(s=>s.innerText.split('\n').slice(0,3).join(' · '));
const anim=[...document.querySelectorAll('.te-shimmer,.te-spin,.te-bob,.te-holddemo')].map(e=>getComputedStyle(e).animationName).join(',');
return JSON.stringify({secs, anim});
