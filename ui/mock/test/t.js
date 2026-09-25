// Test helper for the mock review. Injected by a script tag; not part of the mock.
window.wait = ms => new Promise(r => setTimeout(r, ms));
window.T = {
  root() { return document.querySelector('.te-root'); },
  main() { return this.root().querySelector('main'); },
  vis(e) { return e.offsetParent !== null || getComputedStyle(e).position === 'fixed'; },
  find(text, sel) {
    sel = sel || 'button,a,[role=radio],[role=tab],label,input,textarea';
    const els = [...this.root().querySelectorAll(sel)].filter(e => this.vis(e));
    return els.find(e => (e.getAttribute('aria-label') || '') === text) || els.find(e => e.textContent.trim() === text)
      || els.find(e => (e.getAttribute('aria-label') || '').includes(text)) || els.find(e => e.textContent.trim().includes(text));
  },
  click(text, sel) { const e = this.find(text, sel); if (!e) return 'NOT FOUND: ' + text; e.click(); return 'clicked: ' + (e.getAttribute('aria-label') || e.textContent.trim()).slice(0, 60); },
  has(re) { return re.test(this.root().innerText); },
  grab(re) { const m = this.root().innerText.match(re); return m ? m[0] : '(none)'; },
  top() { const m = this.main(); if (m) m.scrollTop = 0; return 'top'; },
  text(n) { return this.root().innerText.replace(/\n{2,}/g, '\n').slice(0, n || 3000); },
  head() { return this.root().innerText.split('\n').filter(Boolean).slice(0, 4).join(' | '); },
  dialogs() { return [...this.root().querySelectorAll('[role=dialog]')].filter(d => this.vis(d)).map(d => d.getAttribute('aria-label') || d.textContent.slice(0, 30)); },
  // Date override: shifts Date.now and new Date() to a fixed Brisbane-relative instant, advancing in real time.
  setNow(iso) {
    const RealDate = window.__RealDate || Date; window.__RealDate = RealDate;
    const offset = RealDate.parse(iso) - RealDate.now();
    function FakeDate(...a) { return a.length ? new RealDate(...a) : new RealDate(RealDate.now() + offset); }
    FakeDate.now = () => RealDate.now() + offset; FakeDate.parse = RealDate.parse; FakeDate.UTC = RealDate.UTC; FakeDate.prototype = RealDate.prototype;
    window.Date = FakeDate; return 'now ' + new Date().toISOString();
  },
  realNow() { if (window.__RealDate) window.Date = window.__RealDate; return 'real'; },
  pe(el, type, extra) { el.dispatchEvent(new PointerEvent(type, Object.assign({ bubbles: true, pointerId: 1, pointerType: 'touch' }, extra || {}))); },
  // overflow: elements wider than the root or sticking out horizontally, ignoring screen-reader-only spans
  overflow() {
    const r = this.root().getBoundingClientRect(); const out = [];
    this.root().querySelectorAll('*').forEach(e => {
      const cs = getComputedStyle(e); if (cs.position === 'absolute' && cs.clip && cs.clip !== 'auto') return;
      if (e.getBoundingClientRect().width <= 1) return;
      const b = e.getBoundingClientRect();
      if (b.right > r.right + 1 || b.left < r.left - 1) out.push(e.tagName + ' ' + (e.textContent || '').trim().slice(0, 40));
      if (e.scrollWidth > e.clientWidth + 1 && (cs.overflowX === 'hidden' || cs.textOverflow === 'ellipsis') && e.children.length === 0) out.push('CLIPPED ' + e.tagName + ' ' + e.textContent.trim().slice(0, 50));
    });
    return [...new Set(out)].slice(0, 30);
  }
};
'T ready';
