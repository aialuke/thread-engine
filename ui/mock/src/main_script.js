const DEVICE = '__DEVICE__';
const SWAPS = [
  { paid: 'Postman Team', free: 'Bruno',
    paidFact: 'Team is US$19 a user a month, billed yearly. Postman’s free plan is one user.', paidSrc: 'postman.com/pricing',
    quote: '“Your collections are plain-text files in your repo.” “No account. No login.”', freeSrc: 'usebruno.com',
    limit: 'The Git buttons inside Bruno are paid (Pro, US$6 a user a month). The files themselves work with any Git client.' },
  { paid: 'Navicat Premium', free: 'Beekeeper Studio',
    paidFact: 'Sold as a per-user licence. Navicat Premium Lite is the free edition.', paidSrc: 'navicat.com/store',
    quote: '“100% free to use.” The community edition connects to PostgreSQL, MySQL, SQLite and more.', freeSrc: 'beekeeperstudio.io/pricing',
    limit: 'Oracle, MongoDB and Snowflake need a paid tier.' },
  { paid: 'ngrok Pay-as-you-go', free: 'Cloudflare Tunnel',
    paidFact: 'Your own domain starts at Pay-as-you-go: US$20 a month plus usage.', paidSrc: 'ngrok.com/pricing',
    quote: '“Available on all plans.” An outbound-only connection, with no open inbound ports.', freeSrc: 'developers.cloudflare.com/tunnel',
    limit: 'You need a domain added to Cloudflare first. The tunnel itself is free.' }
];
const CARD1 = 'PAID → FREE\nFinding free developer tools that actually hold up.\n\nPostman Team → Bruno\n▷ API collections as plain-text files in your repo. No account.\n\nNavicat Premium → Beekeeper Studio\n▷ One SQL editor for Postgres, MySQL and SQLite.\n\nngrok Pay-as-you-go → Cloudflare Tunnel\n▷ Localhost on your own domain. No open ports.';
const CARD2 = '@use_bruno thanks for keeping API collections in plain files, and for shipping again this week.';
// Placeholder names: dots make them impossible X handles, so no real account is shown.
const REPLIES = [
  { handle: '@builder.one', found: '05:40', kind: 'builder, verified', short: 'Day 8: agents passing the same task back and forth burned a Codex reset in 12 hours.',
    what: 'Build in public, day 8: their agents kept handing the same task to each other and burned through a Codex reset in 12 hours.',
    point: 'Ask what the loop looked like, and say how you avoid it: one agent writes, the other two only review.' },
  { handle: '@lab.notes', found: '05:40', kind: 'AI news', short: 'Released 30,000 logs from the OpenAI agent hack.',
    what: 'Released more than 30,000 logs from the OpenAI agent hack, including attempts on other targets.',
    point: 'The builder’s side of it: what you let your own agents touch, and what they can never write.' },
  { handle: '@aus.indie', found: '05:40', kind: 'builder, not yet a mutual', short: 'Found NDIS provider sites leaking personal data and reported it.',
    what: 'An Australian indie developer found NDIS provider websites leaking personal data, and reported it.',
    point: 'Ask how long it took anyone to respond, and whether there was anywhere proper to report it.' }
];
const WAITING = [
  { id: 'w1', handle: '@sec.minded', where: 'on your breach reply', age: '8 h', said: 'Says model tests alone miss the breach path: red-team what an agent can reach, what it can do, whether attempts show in the logs, and who responds.',
    point: 'Agree, and add the part people skip: who actually picks up when an alert fires at 3 am.' },
  { id: 'w2', handle: '@pixel.tools', where: 'on PAID → FREE: creator tools', age: '14 h', said: 'Suggests another browser photo editor for the Photoshop row: layers, masks, and it opens PSDs.',
    point: 'Thank them, and say it gets checked on its own site before it’s ever listed.' },
  { id: 'w3', handle: '@ship.daily', where: 'on your reply to a builder', age: '1 d', said: 'Asked what caught your eye about their project, and said they’d write up a proper explanation.',
    point: 'Answer the question after a real look at the site. One specific thing beats “looks great”.' }
];
const BUILDERS = [
  { handle: '@sec.minded', tags: 'verified · follows you · you follow · on topic', last: 'yesterday' },
  { handle: '@ship.daily', tags: 'verified · follows you · you follow · on topic', last: '2 days ago' },
  { handle: '@builder.one', tags: 'verified · you follow · not following you yet', last: '3 days ago' },
  { handle: '@aus.indie', tags: 'follows you · you don’t follow yet', last: '4 days ago' }
];
const QUEUE = [
  { id: 'local-ai', title: 'PAID → FREE: local AI', meta: 'Ollama, Cline' },
  { id: 'productivity', title: 'PAID → FREE: productivity', meta: 'Obsidian, OnlyOffice' },
  { id: 'privacy', title: 'PAID → FREE: privacy', meta: 'Bitwarden, AdGuard Home' },
  { id: 'storage', title: 'PAID → FREE: storage', meta: 'Syncthing, Nextcloud' }
];
const RPOSTS = [
  { when: 'Tue 22', title: 'Connect post (retired format)', lane: 'other', views: 856, visits: 20, follows: 13 },
  { when: 'Sun 20', title: 'Home Wi-Fi', lane: 'main', views: 285, visits: 0, follows: 1 },
  { when: 'Tue 22', title: 'MacBook battery', lane: 'main', views: 151, visits: 0, follows: 1 },
  { when: 'Wed 23', title: 'PAID → FREE: creator tools (boosted)', lane: 'other', views: 99, visits: 1, follows: 0, boosted: true },
  { when: 'Tue 22', title: 'iPhone 18 Pro vs 17 Pro', lane: 'main', views: 509, visits: 0, follows: 0 },
  { when: 'Wed 23', title: 'Quote: RLHF', lane: 'other', views: 217, visits: 0, follows: 0 },
  { when: 'Mon 21', title: 'iPhone camera', lane: 'main', views: 137, visits: 0, follows: 0 },
  { when: 'Wed 23', title: 'Prompt vs finish', lane: 'main', views: 54, visits: 0, follows: 0 },
  { when: 'Thu 24', title: 'Quote: Albanese', lane: 'other', views: 15, visits: 0, follows: 0 },
  { when: 'Thu 24', title: 'OpenAI breach take', lane: 'other', views: 4, visits: 0, follows: 0 },
  { when: 'Thu 24', title: 'Connect post 2 (retired format)', lane: 'other', views: 2, visits: 0, follows: 0 }
];
// Last 11 originals in posting order, for the on-topic share (5 on, 6 off).
const SHARE = ['main', 'main', 'main', 'other', 'main', 'other', 'main', 'other', 'other', 'other', 'other'];
const RTOPICS = [
  { t: 'Australian government breach', visits: 15, follows: 1, views: 6680 },
  { t: 'Networking and intros', visits: 10, follows: 3, views: 736 },
  { t: 'Quick answers to question posts', visits: 7, follows: 0, views: 6102 },
  { t: 'Builder conversations', visits: 1, follows: 0, views: 702 }
];
const FOLLOW_SRC = [{ t: 'Connect post', n: 13 }, { t: 'Replies', n: 4 }, { t: 'Thread cards', n: 2 }];
const KPIS = {
  growth: [
    { label: 'Verified followers', value: '27', sub: 'of the 500 X’s rewards need' },
    { label: 'New follows', value: '19', sub: 'this week, from X’s export' },
    { label: 'Followers', value: '36', sub: 'first daily count, 24 Sep' },
    { label: 'Follows per visit', value: '1 in 3', sub: '19 from 58 visits (posts 21 with the boosted one, thread cards 4, replies 33)' }
  ],
  posts: [
    { label: 'New follows', value: '15', sub: 'posts 13, their thread cards 2' },
    { label: 'Profile visits', value: '20', sub: 'boosted post left out' },
    { label: 'Views', value: '2,230', sub: 'organic, boosted post left out' },
    { label: 'Visits per 1,000 views', value: '9.0', sub: 'posts only' }
  ],
  replies: [
    { label: 'Profile visits', value: '33', sub: 'from 115 replies' },
    { label: 'New follows', value: '4', sub: 'from X’s export' },
    { label: 'Mutuals on topic', value: '2', sub: 'example' },
    { label: 'Replies', value: '115', sub: '21–24 Sep' }
  ]
};
const WEIGHTS = [
  { name: 'Opening', value: 'Settings posts: the result goes in the first sentence', src: 'Starting rule · format skills' },
  { name: 'Daily limit', value: 'At most 2 originals, hours apart', src: 'Starting rule · format skills' },
  { name: 'Series pace', value: 'PAID → FREE every other day', src: 'Starting rule · your plan, 24 Sep' },
  { name: 'Posting slots', value: '22:00–23:00 or 05:00–07:00, Tue night to Fri morning', src: 'A guess; the US-overlap test checks it', guess: true },
  { name: 'On topic means', value: 'Tech that’s useful to builders; tech broadly, for now', src: 'Yours to set, never the loop’s' }
];
const GUARDRAILS = [
  'Only you approve a post.',
  'Nothing is posted, scheduled or sent to X for you.',
  'Every figure is sourced in the same session.',
  'A fact-check that can’t confirm a claim leaves it out.',
  'The final checks keep every refusal, including the 600-character cap on the first post of settings, single-tip, build-log, tool-verdict and PAID → FREE posts.',
  'Lessons change things only when you apply them.'
];
const NEXT_EXPERIMENTS = [
  'A single post against a thread',
  'A 3-card thread against the long ones',
  'US-overlap hours against daytime Brisbane',
  'A first post under 280 characters against 500–600',
  'Five replies on a posting day against none',
  'One PAID → FREE category against another'
];
const QUESTIONS = [
  { t: 'What in the exit-zero pipeline could become posts?', why: 'A video of the pipeline with your voice-over is the likeliest breakout. Waiting until the pipeline is ready.' },
  { t: 'What makes a post worth sending to a colleague?', why: 'A copied link is X’s heaviest ranking signal (20, against 0.5 for a like, algorithm fact A9), and the loop can’t see it yet.' }
];
const PIPELINE = [{ n: '2', label: 'Open questions' }, { n: '0', label: 'Experiments' }, { n: '0', label: 'Lessons' }, { n: '5', label: 'Weights' }];
const SUGGESTIONS = [
  { q: 'Why cap the first post at 600?', a: 'Strangers only ever see your first post (algorithm facts A1 and A2), and the feed folds long posts behind “Show more”. 600 keeps a whole list in one post without burying it. The final checks hold every capped format to it, and a queued test compares under 280 with 500–600.' },
  { q: 'What should we test first?', a: 'A single post against a thread is first in the queue: it needs no new format and you already have threads to compare with. It can start around 8 Oct. You can queue it under Experiments.' },
  { q: 'Is the 22:00 slot working?', a: 'Too early to say. One post has gone out in that window, PAID → FREE #1, and it was boosted, so it doesn’t count. The queued US-overlap test checks it properly.' }
];
const SUGGESTIONS_POST = [
  { q: 'Which swap is weakest?', a: 'The ngrok row. It sits past the point where the feed folds this post, and it needs a plan name (Pay-as-you-go) to be true. If you ever cut a row, cut that one. The Bruno row is the strongest, so it leads.' },
  { q: 'Will this post count for rewards?', a: 'Only an unboosted original can count, and this is one. X also excludes posts made or posted by automated means and doesn’t define that, so your own edits and your take make it safer. The shout-out is a reply, so it never counts.' }
];
const SUGGESTIONS_RESULTS = [
  { q: 'Why did the connect post bring the follows?', a: 'It asked builders to say hi, and 13 of the week’s 19 follows came from it. The voice rules allow a connect post at most once in 15 posts, and never a “drop a hi” instruction, which X’s rewards rules treat as soliciting engagement.' },
  { q: 'What’s the one thing to change this week?', a: 'Fewer, better replies. 115 replies brought 4 follows. A handful of specific replies to verified builders is the better bet, and the queued five-replies test will check it properly.' }
];
const SUGGESTIONS_REPLY = [
  { q: 'What’s a good angle here?', a: 'Pick one specific thing from your own build that the point connects to, and ask them one real question back. I won’t write the reply: X can tell when a reply is pasted, and your own words are what build a mutual.' },
  { q: 'Is this worth answering?', a: 'Yes: they raised a real point on your post, and answering people who replied to you is how mutual follows start.' }
];
const FALLBACK = 'In the real app I’d answer from your posts, weights and the X ranking notes. This mock only knows the suggested questions.';
const CHAT_SEED = [{ role: 'bot', text: 'I’m working from your 11 posts, 115 replies and the weights you’ve set. Nothing has been learned from an experiment yet. Ask me why the engine is set the way it is, or what to test next.' }];
const SETTINGS = [
  { title: 'Health', rows: [
    { name: 'Daily check', sub: 'Runs at 20:00 on the Mac', value: 'Ran 20:00 last night', dot: 'var(--ok)' },
    { name: 'Still too new to measure', sub: 'Read once they’re 36 hours old', value: '6 posts', dot: 'var(--line)' },
    { name: 'X API', sub: 'Read-only keys in your Keychain', value: 'Last read worked', dot: 'var(--ok)' },
    { name: 'X API spend', sub: 'Estimate this month, from the run log', value: 'about US$0.42', dot: 'var(--line)' },
    { name: 'Ranking notes', sub: 'X’s published algorithm', value: 'Current · 24 Sep', dot: 'var(--ok)' }
  ] },
  { title: 'Notifications', rows: [
    { name: 'Before a post', sub: 'A reminder 10 minutes before the planned time', toggle: 'remind' },
    { name: 'Shout-out window', sub: 'A nudge when it opens, if you left the app', toggle: 'nudge' }
  ] },
  { title: 'Cortex', rows: [
    { name: 'Model', sub: 'Who answers when you ask Cortex', value: 'Claude', dot: 'var(--line)' }
  ] }
];
const HOOKS = [
  'Codex and Claude disagreed on a fix. Grok broke the tie.',
  'Three AI reviewers, one bug, two different fixes.',
  'I asked three models to review one fix. They didn’t agree.'
];
const STEP_LABELS = ['Plan', 'Draft', 'Approve', 'Post', 'Measure'];
const STAGE_NAMES = ['', 'Drafting', 'Needs your approval', 'Approved', 'Posting', 'Posted, measuring'];
const TARGET = Date.parse('2026-09-25T06:00:00+10:00');
const HOUR = 3600000, DAY = 86400000, BRIS = 10 * HOUR, WAIT_MS = 10 * 60000;
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DEFAULTS = { screen: 'today', prevScreen: 'today', stage: 2, hold: 0, source: null, thinking: null, proposal: null,
  slotMs: TARGET, remind: false, nudge: false, refused: null,
  copyState: 'none', finding: false, notFound: false, posted1: false, waitSkipped: false, copied2: false, copy2Failed: false,
  foundAt: '', foundMs: 0, foundDiff: false, foundTwice: false,
  drafting: null, drafted: {}, draftRetried: false, review: false, approvedAt: '', approvedText: '',
  chatOpen: false, chat: CHAT_SEED, asking: null, typed: '',
  queuedExp: false, context: null, settingsOpen: false, theme: null, rtab: 'growth', showTable: false,
  editorOpen: false, draftText: '', takeText: '', draftPending: false, cardBase: CARD1, cardTake: '', editedAfter: false, savedNote: false,
  firstHourClosed: false, minutes: null, dismissed: {}, capKind: 'Just a note', capText: '',
  captures: [
    { id: 'c1', kind: 'Voice note · 0:42', when: 'yesterday', text: 'Codex and Claude disagreed on the fix; Grok broke the tie.', example: true, format: 'tool verdict' },
    { id: 'c2', kind: 'Screenshot', when: '2 days ago', text: 'The Bruno collection sitting in the repo as plain files.', example: true, format: 'build log' }
  ], turned: {}, readerTurned: false, skipShout: false,
  hookOpen: false, hookPick: 0, hookTake: '', hookSaved: false };

// X's weighted length, as scripts/post_thread.py counts it: these code points 1, every other 2, a link 23.
const URL_RE = /https?:\/\/\S+/gi;
function xLength(text) {
  const links = (text.match(URL_RE) || []).length;
  let n = 0;
  for (const ch of text.replace(URL_RE, '')) {
    const c = ch.codePointAt(0);
    n += (c <= 0x10FF || (c >= 0x2000 && c <= 0x200D) || (c >= 0x2010 && c <= 0x201F) || (c >= 0x2032 && c <= 0x2037)) ? 1 : 2;
  }
  return n + 23 * links;
}
// The gate's refusals for a PAID → FREE root (scripts/post_thread.py card_refusals and swap_root_refusals).
const SWAP_WORDS = ['creator', 'productivity', 'developer', 'privacy', 'system', 'storage', 'diagram', 'finance', 'local AI', 'self-hosting', 'support'];
const SWAP_STEM = new RegExp('^Finding free (?:' + SWAP_WORDS.join('|') + ') tools that actually hold up\\.$');
const SOLICIT_RE = /\bdrop (?:a|an) (?:hi|hello|comment|reply|link|👋)|\bdrop (?:it|them|yours|your \w+) (?:below|here|in the comments)|\bfollow (?:me )?for (?:more|part)|\blike (?:and|&|\+) (?:repost|retweet|share|follow|comment)|\b(?:repost|retweet|bookmark) this\b|\bsave this (?:post|thread|tweet|for later|before)|\bcomment below\b|\breply with\b|\btag (?:a friend|someone|your)/i;
const BANNED_RE = /game changer|most people don['’]?t know|wait for it|🚨|🔥|👇|juggernaut|neural graph|zero server dependenc(?:y|ies)|hollywood[- ]grade|drop-in replacement|let['’]?s grow together/i;
const PART_RE = /^\s*(\d{1,2})\/(\d{1,2})\b|\b(\d{1,2})\/(\d{1,2})\s*$/m;
function gateRefusals(text) {
  if (!text.trim()) return ['Card 1 is empty.'];
  const r = [];
  const lines = text.split('\n');
  const n = xLength(text);
  if (n > 600) r.push('Card 1 is ' + n + ' characters as X counts. PAID → FREE caps the first post at 600.');
  if (!(lines.length >= 2 && lines[0].trim() === 'PAID → FREE' && SWAP_STEM.test(lines[1].trim()))) r.push('Card 1 has to open with the PAID → FREE header and its “Finding free … tools that actually hold up.” line.');
  const h = text.match(/(^|[^\w@])(@\w{1,15})/);
  if (h) r.push(h[2] + ' is in card 1. Handles go in the shout-out only.');
  const tag = text.match(/(^|[^\w&#])(#[A-Za-z]\w*)/);
  if (tag) r.push('Hashtag ' + tag[2] + ' in card 1.');
  const part = text.match(PART_RE);
  if (part) { const a = +(part[1] || part[3]), b = +(part[2] || part[4]); if (a >= 1 && a <= b && b > 1) r.push('Thread counter ' + part[0].trim() + ' in card 1.'); }
  if (/\bVERIFY\b/.test(text)) r.push('Card 1 still has a VERIFY mark.');
  if (text.includes('💬')) r.push('💬 in card 1.');
  if (/your thoughts/i.test(text)) r.push('Card 1 asks for “your thoughts”. Ask a real question instead.');
  const so = text.match(SOLICIT_RE);
  if (so) r.push('Card 1 asks for engagement (“' + so[0] + '”). Ask a real question instead.');
  const b = text.match(BANNED_RE);
  if (b) r.push('Banned phrase in card 1: “' + b[0] + '”.');
  return r;
}
function fmtN(n) { return n.toLocaleString('en-AU'); }
function pad(n) { return (n < 10 ? '0' : '') + n; }
// Brisbane is UTC+10 all year, so times are worked out directly.
function hhmm(ms) { const d = new Date(ms + BRIS); return pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()); }
function brisShort(ms) { const d = new Date(ms + BRIS); return WEEKDAYS[d.getUTCDay()] + ' ' + d.getUTCDate() + ' ' + MONTHS[d.getUTCMonth()]; }
function brisDay(ms) {
  try { return new Date(ms).toLocaleDateString('en-AU', { weekday: 'long', day: 'numeric', month: 'short', timeZone: 'Australia/Brisbane' }); }
  catch (e) { return ''; }
}
function brisMidnight(ms) { return Math.floor((ms + BRIS) / DAY) * DAY - BRIS; }
function sameBrisDay(a, b) { return brisMidnight(a) === brisMidnight(b); }
// The next 06:00 at least 30 minutes away.
function nextSlot(now) { let t = brisMidnight(now) + 6 * HOUR; while (t <= now + 30 * 60000) t += DAY; return t; }
// The first 20:00 daily check once the post is 36 hours old (scripts/snapshot.py, ops/launchd).
function firstRead(posted) { const t = posted + 36 * HOUR; let r = brisMidnight(t) + 20 * HOUR; if (r < t) r += DAY; return r; }
function dayOf(when) { return parseInt(when.split(' ')[1], 10) || 0; }
function copyText(text, done) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => done(true), () => done(false));
      return;
    }
  } catch (e) {}
  done(false);
}

class Component extends DCLogic {
  componentDidMount() {
    this.tick = setInterval(() => this.forceUpdate(), 1000);
    this.onVis = () => { if (document.hidden) this.cancelHold(); };
    document.addEventListener('visibilitychange', this.onVis);
  }
  componentWillUnmount() {
    clearInterval(this.tick); clearInterval(this.holdTimer);
    document.removeEventListener('visibilitychange', this.onVis);
  }
  st() { return Object.assign({}, DEFAULTS, this.state || {}); }
  later(fn) { setTimeout(fn, 60); }
  cancelHold() { if (!this.holdTimer) return; clearInterval(this.holdTimer); this.holdTimer = null; this.setState({ hold: 0 }); }
  shown(sel) { return [...document.querySelectorAll(sel)].filter((e) => e.offsetParent !== null || getComputedStyle(e).position === 'fixed'); }
  // Sheets: focus moves in on open and back to what opened them on close.
  openSheet(patch, label, first) {
    this.returnFocus = document.activeElement;
    this.setState(patch);
    this.later(() => {
      const d = this.shown('.te-root [role=dialog][aria-label="' + label + '"]')[0];
      if (!d) return;
      const f = (first && d.querySelector(first)) || d.querySelector('textarea, input:not([type=hidden])') || d.querySelector('button:not([disabled]), a[href]');
      if (f) f.focus();
    });
  }
  restoreFocus() { const el = this.returnFocus; this.returnFocus = null; this.later(() => { if (el && el.isConnected) el.focus(); }); }
  focusButton(texts) {
    this.later(() => {
      const bs = this.shown('.te-root main button, .te-root main a');
      for (const t of texts) { const b = bs.find((x) => x.textContent.trim().startsWith(t)); if (b) { b.focus(); return; } }
    });
  }
  finishAsk(cur) { const a = cur.asking || {}; return { asking: null, chat: cur.chat.concat([{ role: 'bot', text: a.a || FALLBACK }]) }; }
  askCortex(context) {
    this.returnFocus = document.activeElement;
    // On the Mac's Cortex page the chat is already docked, so only the question's subject changes.
    if (DEVICE === 'mac' && this.st().screen === 'cortex') this.setState({ context: context });
    else this.setState({ chatOpen: true, context: context });
    this.later(() => { const ins = this.shown('.te-root input[aria-label="Ask Cortex"]'); const i = ins[ins.length - 1]; if (i) i.focus(); });
  }
  closeEditorKeep() {
    const s = this.st();
    this.setState({ editorOpen: false, draftPending: s.draftText !== s.cardBase || s.takeText !== s.cardTake });
    this.restoreFocus();
  }
  closeTop() {
    const s = this.st();
    if (s.hookOpen) { this.setState({ hookOpen: false }); this.restoreFocus(); return true; }
    if (s.editorOpen) { this.closeEditorKeep(); return true; }
    if (s.source !== null) { this.setState({ source: null }); this.restoreFocus(); return true; }
    if (s.chatOpen && !(DEVICE === 'mac' && s.screen === 'cortex')) { this.setState(Object.assign({ chatOpen: false }, s.asking ? this.finishAsk(s) : {})); this.restoreFocus(); return true; }
    if (s.settingsOpen) { this.setState({ settingsOpen: false }); this.restoreFocus(); return true; }
    return false;
  }
  globalKey(e) {
    if (e.key === 'Escape') { if (this.closeTop()) e.preventDefault(); return; }
    if (DEVICE === 'mac' && (e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); this.askCortex(null); }
  }

  renderVals() {
    const s = this.st();
    const now = Date.now();
    const go = (screen) => () => this.setState({ screen: screen, prevScreen: s.screen, source: null, chatOpen: false });
    const busy = !!(s.thinking || s.drafting);
    const cardText = s.cardBase + (s.cardTake ? '\n\n' + s.cardTake : '');

    // --- time, relative to now and this post's slot
    const slot = s.slotMs, slotEnd = slot + HOUR, slotHM = hhmm(slot);
    const toGo = slot - now, late = now > slot, missed = now > slotEnd;
    const dayWord = sameBrisDay(now, slot) ? 'Today' : (sameBrisDay(now + DAY, slot) ? 'Tomorrow' : brisShort(slot));
    const whenShort = dayWord + ', ' + slotHM;
    const next = nextSlot(now);
    const nextLabel = (sameBrisDay(now, next) ? 'today' : sameBrisDay(now + DAY, next) ? 'tomorrow' : brisShort(next)) + ', ' + hhmm(next);
    let countdown, countdownColor = 'var(--blue)';
    if (!late) {
      const h = Math.floor(toGo / HOUR), m = Math.floor((toGo % HOUR) / 60000);
      countdown = h > 0 ? 'in ' + h + ' h ' + m + ' m' : 'in ' + m + ' min';
    } else if (!missed) {
      countdown = Math.floor((now - slot) / 60000) + ' min late, still inside the ' + hhmm(slot - HOUR) + '–' + hhmm(slotEnd) + ' slot';
      countdownColor = 'var(--amber)';
    } else {
      countdown = 'missed the slot';
      countdownColor = 'var(--amber)';
    }
    const isEarly = toGo > 30 * 60000;
    const remindAt = hhmm(slot - 10 * 60000);
    const moveSlot = () => this.setState({ slotMs: next });

    const at = s.stage <= 3 ? s.stage : s.stage - 1;
    const steps = STEP_LABELS.map((label, i) => {
      const done = i < at, cur = i === at;
      return { label: label, mark: done ? '✓ ' : '', state: done ? ', done' : cur ? ', current step' : ', to do',
        current: cur ? 'step' : 'false', bar: done ? 'var(--ink)' : cur ? 'var(--blue)' : 'var(--line)',
        color: done ? 'var(--ink)' : cur ? 'var(--blue)' : 'var(--muted)', weight: cur ? '600' : '400' };
    });

    // On the Mac the cards sit beside Today, so reading them means bringing them into view.
    const focusCards = () => {
      this.setState({ screen: 'today', prevScreen: s.screen, source: null });
      this.later(() => { const el = document.querySelector('.te-root [data-te-cards]'); if (el) { el.scrollIntoView({ block: 'start', behavior: 'smooth' }); el.focus({ preventScroll: true }); } });
    };
    const readCards = DEVICE === 'mac' ? focusCards : go('post');
    const startReady = () => { if (this.st().thinking || this.st().drafting) return; this.setState({ screen: 'today', thinking: 'ready', refused: null }); };

    let headline, primaryLabel, primaryHint, primaryAction, showEarlyAnyway = false, primaryDisabled = false;
    if (s.stage === 2 && missed) {
      headline = 'The ' + slotHM + ' slot has passed.';
      primaryLabel = 'Read and approve'; primaryHint = 'Approving posts nothing. Then move it to ' + nextLabel + '.'; primaryAction = readCards;
    } else if (s.stage === 2) {
      headline = dayWord === 'Today' ? 'Today’s post needs your read.' : dayWord === 'Tomorrow' ? 'Tomorrow’s post needs your read.' : 'Your next post needs your read.';
      primaryLabel = 'Read and approve'; primaryHint = 'Change anything first. Edits teach the loop what you prefer.'; primaryAction = readCards;
    } else if (s.stage === 3 && missed) {
      headline = 'The ' + slotHM + ' slot has passed.';
      primaryLabel = 'Move it to ' + nextLabel; primaryHint = 'Your approval stays. Nothing is posted for you.'; primaryAction = moveSlot;
    } else if (s.stage === 3 && isEarly) {
      headline = 'Approved, and ready for ' + slotHM + ' ' + (dayWord === 'Today' ? 'today' : dayWord === 'Tomorrow' ? 'tomorrow' : 'on ' + dayWord) + '.';
      primaryLabel = s.remind ? 'Reminder set for ' + remindAt : 'Remind me at ' + remindAt;
      primaryHint = s.remind ? 'Tap to turn it off. Nothing is posted for you.' : 'A nudge 10 minutes before. Nothing is posted for you.';
      primaryAction = () => this.setState({ remind: !s.remind });
      showEarlyAnyway = true;
    } else if (s.stage === 3) {
      headline = late ? 'Time to post.' : 'Almost time to post.';
      primaryLabel = 'Start posting'; primaryHint = 'Final checks first. You press Post on X.'; primaryAction = startReady; primaryDisabled = busy;
    } else if (s.stage === 4) {
      headline = 'You’re in the middle of posting.'; primaryLabel = 'Back to posting'; primaryHint = 'The shout-out is still to come.'; primaryAction = go('ready');
    } else {
      headline = 'Posted. Stay close for the first hour.'; primaryLabel = 'See results';
      primaryHint = 'The first full read comes with the daily check on ' + brisShort(firstRead(s.foundMs || now)) + ' at 20:00.'; primaryAction = go('results');
    }

    // --- hold to approve (pointer and keyboard); any interruption cancels it
    const approveNow = () => {
      const cur = this.st();
      this.setState({ hold: 0, stage: 3, approvedAt: hhmm(Date.now()), approvedText: cur.cardBase + (cur.cardTake ? '\n\n' + cur.cardTake : ''), editedAfter: false, savedNote: false });
      this.focusButton(['Start posting', 'Move it to', 'Edit a card']);
    };
    const holdStart = () => {
      if (this.holdTimer) return;
      this.holdTimer = setInterval(() => {
        const h = ((this.state && this.state.hold) || 0) + 4;
        if (h >= 100) { clearInterval(this.holdTimer); this.holdTimer = null; approveNow(); }
        else this.setState({ hold: h });
      }, 40);
    };
    const holdEnd = () => this.cancelHold();

    // --- card preview from the actual card text, with the fold computed
    const lines = cardText.split('\n');
    let run = 0, foldAt = -1;
    lines.forEach((ln, i) => { run += xLength(ln) + (i ? 1 : 0); if (foldAt < 0 && run > 280) foldAt = i; });
    const cardLines = lines.map((ln, i) => {
      const swapIdx = SWAPS.findIndex((w) => ln.startsWith(w.paid + ' →'));
      const after = foldAt >= 0 && i >= foldAt;
      return { text: ln, isBlank: ln.trim() === '', isText: ln.trim() !== '' && swapIdx < 0, isSwap: swapIdx >= 0,
        foldBefore: i === foldAt, fade: after ? '0.6' : '1', bg: s.source === swapIdx ? 'var(--blue-soft)' : 'transparent',
        open: () => this.openSheet({ source: swapIdx }, 'Source') };
    });
    const cardCount = xLength(cardText);
    const takeTrim = s.takeText.trim();
    const draftCount = xLength(s.draftText + (takeTrim ? '\n\n' + takeTrim : ''));

    // --- posting
    const waitLeft = s.posted1 ? (s.waitSkipped ? 0 : Math.max(0, Math.ceil((s.foundMs + WAIT_MS - now) / 1000))) : WAIT_MS / 1000;
    const s1Active = s.stage >= 4, s2Active = s.posted1, s3Active = s.posted1 && waitLeft === 0, s4Active = s.copied2 || s.skipShout;
    const stepVals = (k, on) => { const o = {}; o[k + 'Off'] = on ? 'false' : 'true'; o[k + 'Badge'] = on ? 'var(--btn)' : 'var(--faint)'; o[k + 'Head'] = on ? 'var(--ink)' : 'var(--muted)'; return o; };
    const mm = Math.floor(waitLeft / 60), ss = waitLeft % 60;
    const base = s.foundMs || now;
    const winStartMs = base + WAIT_MS, winEndMs = base + 2 * WAIT_MS, fhCloseMs = base + HOUR;
    const backTo = (stage) => () => this.setState({ stage: stage, screen: DEVICE === 'mac' ? 'today' : 'post', copyState: 'none', finding: false, notFound: false,
      approvedAt: stage === 2 ? '' : s.approvedAt, approvedText: stage === 2 ? '' : s.approvedText });

    // --- replies
    const waitingLeft = WAITING.filter((w) => !s.dismissed[w.id]);
    const mark = (id, how) => () => { const cur = this.st(); const d = Object.assign({}, cur.dismissed); if (how) d[id] = how; else delete d[id]; this.setState({ dismissed: d }); };
    const nWait = waitingLeft.length;

    // --- chat
    const askQ = (sg) => {
      const cur = this.st();
      if (cur.asking) return;
      this.setState({ chat: cur.chat.concat([{ role: 'user', text: sg.q }]), asking: sg, typed: '' });
    };
    const ALL_Q = SUGGESTIONS.concat(SUGGESTIONS_POST, SUGGESTIONS_RESULTS, SUGGESTIONS_REPLY);
    const sendText = (text) => { const q = (text || '').trim(); if (!q) return; askQ(ALL_Q.find((sg) => sg.q.toLowerCase() === q.toLowerCase()) || { q: q, a: FALLBACK }); };
    const ctxSet = { post: SUGGESTIONS_POST, results: SUGGESTIONS_RESULTS, reply: SUGGESTIONS_REPLY, proposal: SUGGESTIONS };
    const ctxLabel = { post: 'the next post', results: 'this week’s results', reply: 'a reply waiting for you', proposal: 'the proposed build log' };

    // --- theme
    const th = s.theme || this.props.theme || 'system';
    let sysDark = false;
    try { sysDark = !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches); } catch (e) {}
    const resolved = th === 'system' ? (sysDark ? 'dark' : 'light') : th;
    const segOn = (on) => ({ bg: on ? 'var(--card)' : 'transparent', border: on ? '1px solid var(--seg-sel)' : '1px solid transparent', weight: on ? '600' : '500' });
    const seg = (prefix, on, handler) => { const v = segOn(on); const o = {}; o[prefix] = on; o[prefix + 'Bg'] = v.bg; o[prefix + 'Border'] = v.border; o[prefix + 'Weight'] = v.weight; o[prefix + 'Ti'] = on ? '0' : '-1'; if (handler) o[prefix + 'Go'] = handler; return o; };
    const healthBad = this.props.health === 'failed' && !s.healthFixed;

    const rt = s.rtab;
    const RT_ORDER = ['growth', 'posts', 'replies'];
    const tabOn = (on) => (on ? 'var(--ink)' : 'var(--faint)');
    const inToday = ['today', 'post', 'ready'].includes(s.screen);
    const tabs = {};
    [['Today', inToday], ['Posts', s.screen === 'posts' || s.screen === 'capture'], ['Replies', s.screen === 'replies'], ['Results', s.screen === 'results'], ['Cortex', s.screen === 'cortex']].forEach(([k, on]) => {
      tabs['tab' + k] = tabOn(on); tabs['tab' + k + 'Weight'] = on ? '600' : '500'; tabs['tab' + k + 'Current'] = on ? 'page' : 'false';
      tabs['tab' + k + 'Label'] = k === 'Replies' && nWait ? 'Replies, ' + nWait + ' waiting' : k;
      tabs['nav' + k + 'Bg'] = on ? 'var(--line2)' : 'transparent'; tabs['nav' + k + 'Bar'] = on ? 'var(--ink)' : 'transparent';
    });

    const draftFail = this.props.draft === 'error' && !s.draftRetried ? 'Couldn’t reach postman.com/pricing. Nothing was written; try again in a minute.' : '';
    const queue = QUEUE.map((q) => {
      const isDrafting = s.drafting === q.id, isDrafted = !!s.drafted[q.id];
      return Object.assign({}, q, { isDrafting: isDrafting, isDrafted: isDrafted, showDraft: !isDrafting && !isDrafted,
        factNote: isDrafted && this.props.draft === 'factcheck',
        fail: draftFail, retry: () => this.setState({ draftRetried: true }),
        cancel: () => this.setState({ drafting: null }),
        draft: () => { if (!this.st().thinking && !this.st().drafting) this.setState({ drafting: q.id }); },
        onDone: () => { const cur = this.st(); const d = Object.assign({}, cur.drafted); d[q.id] = true; this.setState({ drafting: null, drafted: d }); } });
    });

    const src = SWAPS[s.source === null || s.source < 0 ? 0 : s.source];
    const maxVisits = 15;
    const rpostsSorted = RPOSTS.slice().sort((a, b) => b.follows - a.follows || b.visits - a.visits || b.views - a.views);
    const plural = (n, one, many) => n + ' ' + (n === 1 ? one : many);
    const inertOn = !!((DEVICE === 'mac' ? (s.chatOpen && s.screen !== 'cortex') : s.chatOpen) || s.settingsOpen || s.editorOpen || s.source !== null || s.hookOpen);

    return Object.assign({
      isHome: ['today', 'post', 'ready'].includes(s.screen), isHomeCards: ['today', 'post'].includes(s.screen), isHomeReady: s.screen === 'ready',
      showDrawer: DEVICE === 'mac' && s.chatOpen && s.screen !== 'cortex',
      toggleSettings: () => { if (s.settingsOpen) { this.setState({ settingsOpen: false }); this.restoreFocus(); } else this.openSheet({ settingsOpen: true }, 'Settings and health'); },
      profileBg: s.settingsOpen ? 'var(--line2)' : 'transparent',
      sideHealth: healthBad ? 'Daily check missed last night' : 'Daily check ran 20:00',
      rootKey: (e) => this.globalKey(e),
      themeAttr: th, mainInert: inertOn ? 'true' : null, navInert: inertOn ? 'true' : null,
      showMoon: resolved === 'light', showSun: resolved === 'dark',
      flipLabel: resolved === 'light' ? 'Switch to dark mode' : 'Switch to light mode',
      flipTheme: () => this.setState({ theme: resolved === 'dark' ? 'light' : 'dark' }),

      isToday: s.screen === 'today', isPost: s.screen === 'post', isReady: s.screen === 'ready', isPosts: s.screen === 'posts',
      isCapture: s.screen === 'capture', isReplies: s.screen === 'replies', isResults: s.screen === 'results', isCortex: s.screen === 'cortex',
      goToday: go('today'), goPost: readCards, goPosts: go('posts'), goReplies: go('replies'), goResults: go('results'), goCortex: () => this.setState({ screen: 'cortex', context: null }),
      goCapture: go('capture'), goBackFromCapture: go(s.prevScreen === 'capture' ? 'today' : s.prevScreen),

      avatarLabel: healthBad ? 'EZ, settings and health, something needs you' : 'EZ, settings and health',
      healthBad: healthBad, healthDot: healthBad ? 'var(--amber-fill)' : 'var(--ok)',
      healthLine: healthBad ? 'Last daily check: Wed 20:00' : 'Daily check ran 20:00 last night. 6 posts are still too new to measure.',
      fixHealth: () => this.setState({ healthFixed: true, settingsOpen: false }),
      todayLabel: brisDay(now) + ' · Brisbane',

      headline: headline, cardEyebrow: s.stage >= 5 ? 'Just posted' : 'Next post',
      whenLabel: s.stage >= 5 ? 'Posted ' + s.foundAt : whenShort, whenShort: whenShort, whenCard: s.stage >= 5 ? 'Posted ' + s.foundAt : whenShort,
      countdown: s.stage >= 5 ? '' : countdown, countdownColor: countdownColor, steps: steps,
      stageName: STAGE_NAMES[s.stage] || '', primaryLabel: primaryLabel, primaryHint: primaryHint, primaryAction: primaryAction,
      primaryDisabled: primaryDisabled, primaryOpacity: primaryDisabled ? '0.45' : '1',
      showEarlyAnyway: showEarlyAnyway, startEarly: startReady,
      thinkingReady: s.thinking === 'ready', showPrimary: s.thinking !== 'ready',
      // Posting goes ahead only if the post is still approved and the cards are the ones approved.
      doneReady: () => {
        const cur = this.st();
        const text = cur.cardBase + (cur.cardTake ? '\n\n' + cur.cardTake : '');
        if (cur.stage !== 3 || text !== cur.approvedText) { this.setState({ thinking: null }); return; }
        const reasons = gateRefusals(text);
        if (this.props.gate === 'refused') reasons.unshift('Card 1 changed after you approved it.');
        this.setState({ thinking: null, screen: 'ready', stage: reasons.length ? 3 : 4, refused: reasons.length ? reasons : null });
      },
      busy: busy, busyOpacity: busy ? '0.45' : '1',

      showFirstHour: s.stage >= 5 && !s.firstHourClosed && now < fhCloseMs, fhClose: hhmm(fhCloseMs), closeFirstHour: () => this.setState({ firstHourClosed: true }),
      minuteChips: ['15 min', '30 min', '1 hour', 'Longer'].map((m) => ({ label: m, on: s.minutes === m, bg: s.minutes === m ? 'var(--blue-soft)' : 'var(--raised)',
        border: s.minutes === m ? 'var(--blue)' : 'var(--line)', weight: s.minutes === m ? '600' : '500', pick: () => this.setState({ minutes: m }) })),

      replies: REPLIES,
      waiting: WAITING.map((w) => Object.assign({}, w, { open: !s.dismissed[w.id], closed: !!s.dismissed[w.id],
        status: s.dismissed[w.id] === 'answered' ? 'Answered' : 'Not answering',
        answered: mark(w.id, 'answered'), skip: mark(w.id, 'skipped'), undo: mark(w.id, null),
        ask: () => this.askCortex('reply') })),
      waitingPreview: waitingLeft.slice(0, 2), waitingCount: nWait, hasWaiting: nWait > 0, noWaiting: nWait === 0,
      waitingText: nWait === 1 ? '1 person is waiting for your answer' : nWait + ' people are waiting for your answer',
      builders: BUILDERS,

      showPlanButton: s.thinking !== 'next' && !s.proposal, thinkingNext: s.thinking === 'next',
      planNext: () => { if (!busy) this.setState({ thinking: 'next', proposal: null }); },
      doneNext: () => this.setState({ thinking: null, proposal: 'shown' }),
      proposalShown: s.proposal === 'shown', proposalAccepted: s.proposal === 'accepted',
      acceptProposal: () => this.setState({ proposal: 'accepted' }),
      changeProposal: () => { if (!this.st().thinking && !this.st().drafting) this.setState({ proposal: null, thinking: 'next' }); },
      askAboutProposal: () => this.askCortex('proposal'),

      postTitle: s.stage >= 5 ? 'Posted' : whenShort,
      stageApprove: s.stage === 2, stageApprovedOnly: s.stage === 3, stagePosted: s.stage >= 5,
      approvedAt: s.approvedAt, editedAfter: s.editedAfter && s.stage === 2, savedNote: s.savedNote,
      isEarly: isEarly && !missed, showStartHere: !isEarly && !missed, showMoveHere: missed, moveSlot: moveSlot, moveLabel: 'Move it to ' + nextLabel,
      earlyNote: 'Approved. It’s planned for ' + whenShort + '. Come back about 10 minutes before.' + (s.remind ? ' A reminder is set for ' + remindAt + '.' : ''),
      startReady: startReady,
      holdStart: holdStart, holdEnd: holdEnd,
      holdKeyDown: (e) => { if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) { e.preventDefault(); holdStart(); } },
      holdKeyUp: (e) => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); holdEnd(); } },
      holdWidth: s.hold + '%', holdLabel: s.hold > 0 ? 'Keep holding…' : 'Hold to approve', holdTextColor: 'var(--on-btn)',
      cardLines: cardLines, cardCount: cardCount, countColor: cardCount > 600 ? 'var(--amber)' : 'var(--muted)',
      askAboutPost: () => this.askCortex('post'),

      editorOpen: s.editorOpen, editClearsApproval: s.stage === 3, editDisabled: s.thinking === 'ready', editOpacity: s.thinking === 'ready' ? '0.45' : '1',
      openEditor: () => {
        if (this.st().thinking === 'ready') return;
        const patch = s.draftPending ? { editorOpen: true, source: null } : { editorOpen: true, source: null, draftText: s.cardBase, takeText: s.cardTake };
        this.openSheet(patch, 'Change something');
      },
      closeEditor: () => this.closeEditorKeep(),
      cancelEdit: () => { this.setState({ editorOpen: false, draftPending: false }); this.restoreFocus(); },
      draftPending: s.draftPending && s.editorOpen,
      discardDraft: () => this.setState({ draftText: s.cardBase, takeText: s.cardTake, draftPending: false }),
      draftText: s.draftText, setDraftText: (e) => this.setState({ draftText: e.target.value }),
      takeText: s.takeText, setTakeText: (e) => this.setState({ takeText: e.target.value }),
      draftCount: draftCount, draftCountColor: draftCount > 600 ? 'var(--amber)' : 'var(--muted)',
      saveEdit: () => {
        const cur = this.st();
        const take = cur.takeText.trim();
        const text = cur.draftText + (take ? '\n\n' + take : '');
        const changed = text !== cardText;
        this.setState({ editorOpen: false, draftPending: false, cardBase: cur.draftText, cardTake: take,
          stage: changed && cur.stage === 3 ? 2 : cur.stage, editedAfter: changed && cur.stage === 3, savedNote: changed,
          approvedAt: changed && cur.stage === 3 ? '' : cur.approvedAt, approvedText: changed && cur.stage === 3 ? '' : cur.approvedText });
        this.restoreFocus();
      },

      hasSource: s.source !== null && s.source >= 0, src: Object.assign({ n: (s.source || 0) + 1 }, src),
      closeSource: () => { this.setState({ source: null }); this.restoreFocus(); },
      sheetKey: (e) => { if (e.key === 'Escape') { e.stopPropagation(); e.preventDefault(); this.closeTop(); } },

      readyRefused: !!s.refused, readyOk: !s.refused, refusedReasons: (s.refused || []).map((t) => ({ t: t })),
      reapprove: () => { this.setState({ stage: 2, refused: null, approvedAt: '', approvedText: '' }); readCards(); },
      canBack: s.stage === 4 && !s.posted1 && !s.finding, notNow: backTo(3), withdraw: backTo(2),
      showCopy1: s.copyState === 'none',
      copy1: () => copyText(cardText, (ok) => { this.setState({ copyState: ok ? 'ok' : 'failed' }); this.focusButton(ok ? ['I’ve posted it', "I've posted it"] : ['Copy again']); }),
      copyFailed: s.copyState === 'failed' && !s.posted1, copiedOk: s.copyState === 'ok' && !s.posted1,
      showCopyAgain: s.copyState !== 'none' && !s.posted1,
      showPosted1: s.copyState === 'ok' && !s.posted1 && !s.finding && !s.notFound,
      postedIt: () => this.setState({ finding: true, notFound: false }),
      finding: s.finding, notFound: s.notFound,
      doneFind: () => {
        const cur = this.st();
        if (this.props.find === 'notfound' && !cur.foundOnce) { this.setState({ finding: false, notFound: true, foundOnce: true }); return; }
        const t = Date.now();
        this.setState({ finding: false, notFound: false, posted1: true, foundMs: t, foundAt: hhmm(t), foundDiff: this.props.find === 'differs', foundTwice: this.props.find === 'twice' });
      },
      carryOn: () => { const t = Date.now(); this.setState({ notFound: false, posted1: true, foundMs: t, foundAt: hhmm(t) }); },
      foundAt: s.foundAt || hhmm(now),
      posted1: s.posted1, foundText: 'Found it: posted ' + s.foundAt + '.' + (s.foundDiff ? '' : ' Matches your approved card.'),
      foundDiff: s.posted1 && s.foundDiff, foundTwice: s.posted1 && s.foundTwice,
      waitText: mm + ':' + (ss < 10 ? '0' : '') + ss, waitPct: ((WAIT_MS / 1000 - waitLeft) / (WAIT_MS / 1000) * 100).toFixed(1) + '%',
      winStart: hhmm(winStartMs), winEnd: hhmm(winEndMs),
      windowClosed: s3Active && now > winEndMs && !s.copied2 && !s.skipShout,
      nudgeSent: s3Active && s.nudge && !s.copied2 && !s.skipShout,
      skipWait: () => this.setState({ waitSkipped: true }),
      skipShout: () => this.setState({ skipShout: true, thinking: 'posted' }),
      waitDone: s3Active && !s.skipShout,
      copy2: () => copyText(CARD2, (ok) => this.setState(ok ? { copied2: true, copy2Failed: false, thinking: 'posted' } : { copy2Failed: true })),
      copied2: s.copied2, copy2Failed: s.copy2Failed && !s.copied2, showCopy2: !s.copied2,
      thinkingPosted: s.thinking === 'posted', recordCmd: s.skipShout ? 'record' : 'posted',
      doneRecord: () => this.setState({ thinking: null, stage: 5, screen: 'today' }),

      queue: queue, captureCount: s.captures.filter((c) => !s.turned[c.id]).length,
      postedList: RPOSTS.slice().sort((a, b) => dayOf(b.when) - dayOf(a.when)).map((p) => ({ title: p.title, whenShort: p.when,
        meta: plural(p.follows, 'follow', 'follows') + ' · ' + plural(p.visits, 'visit', 'visits') + ' · ' + fmtN(p.views) + ' views' + (p.boosted ? ' · not counted' : '') })),

      openHook: () => this.openSheet({ hookOpen: true }, 'Choose a hook', '[role=radio][aria-checked="true"]'),
      closeHook: () => { this.setState({ hookOpen: false }); this.restoreFocus(); },
      hookOpen: s.hookOpen, hookSaved: s.hookSaved, hookNotSaved: !s.hookSaved, hookChosen: HOOKS[s.hookPick],
      hooks: HOOKS.map((h, i) => ({ text: h, n: i + 1, count: xLength(h), on: s.hookPick === i ? 'true' : 'false',
        border: s.hookPick === i ? 'var(--blue)' : 'var(--line)', bg: s.hookPick === i ? 'var(--blue-soft)' : 'var(--card)', pick: () => this.setState({ hookPick: i }) })),
      hookTake: s.hookTake, setHookTake: (e) => this.setState({ hookTake: e.target.value }),
      saveHook: () => { this.setState({ hookOpen: false, hookSaved: true }); this.restoreFocus(); },

      capKinds: ['Screenshot', 'Screen recording', 'Voice note', 'Just a note'].map((k) => Object.assign({ label: k }, (() => { const v = segOn(s.capKind === k); return { on: s.capKind === k, bg: v.bg === 'transparent' ? 'var(--raised)' : 'var(--blue-soft)', border: s.capKind === k ? 'var(--blue)' : 'var(--line)', weight: v.weight }; })(), { pick: () => this.setState({ capKind: k }) })),
      capText: s.capText, setCapText: (e) => this.setState({ capText: e.target.value }),
      saveCapture: () => { if (!s.capText.trim()) return; this.setState({ captures: [{ id: 'c' + (s.captures.length + 1) + '-' + Date.now(), kind: s.capKind, when: 'just now', text: s.capText.trim(), format: 'build log' }].concat(s.captures), capText: '' }); },
      captures: s.captures.map((c) => ({ kind: c.kind + (c.example ? ' · example' : ''), when: c.when, text: c.text,
        canTurn: !s.turned[c.id], turned: !!s.turned[c.id], format: c.format,
        turn: () => { const t = Object.assign({}, this.st().turned); t[c.id] = true; this.setState({ turned: t }); } })),
      readerCanTurn: !s.readerTurned, readerTurned: s.readerTurned, turnReader: () => this.setState({ readerTurned: true }),

      rtGoGrowth: () => this.setState({ rtab: 'growth' }), rtGoPosts: () => this.setState({ rtab: 'posts' }), rtGoReplies: () => this.setState({ rtab: 'replies' }),
      rtKey: (e) => {
        const i = RT_ORDER.indexOf(rt);
        const j = e.key === 'ArrowRight' ? (i + 1) % 3 : e.key === 'ArrowLeft' ? (i + 2) % 3 : e.key === 'Home' ? 0 : e.key === 'End' ? 2 : null;
        if (j === null) return;
        e.preventDefault(); this.setState({ rtab: RT_ORDER[j] });
        this.later(() => { const t = this.shown('.te-root [role=tab]')[j]; if (t) t.focus(); });
      },
      rtPanelLabel: { growth: 'Growth', posts: 'Posts', replies: 'Replies' }[rt],
      showTable: s.showTable, showChart: !s.showTable, tableLabel: s.showTable ? 'Show charts' : 'Show as table',
      toggleTable: () => this.setState({ showTable: !s.showTable }), kpis: KPIS[rt],
      followSrc: FOLLOW_SRC.map((f) => ({ t: f.t, n: f.n, pct: (f.n / 13 * 70).toFixed(1) + '%', label: String(f.n) })),
      followerDays: [{ d: 'Thu 24 Sep', n: '36' }],
      rposts: rpostsSorted.map((p) => ({ title: p.title, when: p.when, label: plural(p.follows, 'follow', 'follows') + ' · ' + plural(p.visits, 'visit', 'visits') + ' · ' + fmtN(p.views) + ' views' + (p.boosted ? ' · not counted' : '') })),
      postRows: rpostsSorted.map((p) => ({ t: p.title, f: p.follows, v: p.visits, w: fmtN(p.views), topic: (p.lane === 'main' ? 'On' : 'Off') + (p.boosted ? ', boosted' : '') })),
      shareSlots: Array.from({ length: 15 }, (_, i) => { const v = SHARE[i]; return { bg: v === 'main' ? 'var(--chart-on)' : 'transparent', border: v === 'main' ? 'none' : v === 'other' ? '1.5px solid var(--axis)' : '1.5px dashed var(--dash)' }; }),
      shareRows: Array.from({ length: 15 }, (_, i) => ({ n: i + 1, v: SHARE[i] === 'main' ? 'On topic' : SHARE[i] === 'other' ? 'Off topic' : 'Still to post' })),
      shareLabel: 'On topic: 5 of your last 11 posts, 4 still to post. Target 12 of 15.',
      rtopics: RTOPICS.map((t) => ({ t: t.t, visits: t.visits, follows: t.follows, views: fmtN(t.views), pct: (t.visits / maxVisits * 48).toFixed(1) + '%',
        label: plural(t.visits, 'visit', 'visits') + ' · ' + plural(t.follows, 'follow', 'follows') })),
      askAboutResults: () => this.askCortex('results'),
      showReviewButton: s.thinking !== 'results' && !s.review, thinkingResults: s.thinking === 'results',
      writeReview: () => { if (!busy) this.setState({ thinking: 'results' }); }, doneReview: () => this.setState({ thinking: null, review: true }), reviewWritten: s.review,
      reviewAsk: 'The review needs this week’s numbers from X’s eligibility screen.',

      pipeline: PIPELINE, weights: WEIGHTS.map((w) => Object.assign({}, w, { style: w.guess ? 'italic' : 'normal' })),
      guardrails: GUARDRAILS.map((g) => ({ text: g })), questions: QUESTIONS,
      nextExperiments: NEXT_EXPERIMENTS.map((x, i) => ({ n: i + 1, text: x, first: i === 0 })),
      queuedExp: s.queuedExp, queueFirst: () => this.setState({ queuedExp: true }), queueLabel: s.queuedExp ? 'Queued for about 8 Oct' : 'Queue for about 8 Oct',

      showPill: DEVICE === 'phone' && s.screen === 'cortex' && !s.chatOpen, chatOpen: s.chatOpen,
      openChat: () => this.askCortex(null),
      closeChat: () => { const cur = this.st(); this.setState(Object.assign({ chatOpen: false }, cur.asking ? this.finishAsk(cur) : {})); this.restoreFocus(); },
      chat: s.chat.map((m) => ({ text: m.text, isUser: m.role === 'user', isBot: m.role === 'bot' })),
      asking: !!s.asking,
      doneAsk: () => this.setState(this.finishAsk(this.st())),
      suggestions: (ctxSet[s.context] || SUGGESTIONS).map((sg) => ({ q: sg.q, ask: () => askQ(sg) })),
      hasContext: !!s.context, contextLabel: ctxLabel[s.context] || '', clearContext: () => this.setState({ context: null }),
      typed: s.typed, setTyped: (e) => this.setState({ typed: e.target.value }), sendTyped: () => sendText(s.typed),
      typedKey: (e) => { if (e.key !== 'Enter' || e.shiftKey || e.isComposing) return; e.preventDefault(); sendText(e.target.value); },

      settingsOpen: s.settingsOpen, openSettings: () => this.openSheet({ settingsOpen: true }, 'Settings and health'),
      closeSettings: () => { this.setState({ settingsOpen: false }); this.restoreFocus(); },
      settingsGroups: SETTINGS.map((g) => ({ title: g.title, rows: g.rows.map((r) => {
        const t = r.toggle, on = t ? !!s[t] : false;
        return Object.assign({}, r, { isToggle: !!t, notToggle: !t, on: on ? 'true' : 'false', value: t ? (on ? 'On' : 'Off') : r.value,
          dot: t ? (on ? 'var(--ok)' : 'var(--line)') : r.dot, flip: () => { if (t) this.setState({ [t]: !this.st()[t] }); },
          knob: on ? '20px' : '2px', track: on ? 'var(--blue-fill)' : 'var(--line)' });
      }) }))
    }, tabs, stepVals('s1', s1Active), stepVals('s2', s2Active), stepVals('s3', s3Active), stepVals('s4', s4Active),
      seg('rtGrowth', rt === 'growth'), seg('rtPosts', rt === 'posts'), seg('rtReplies', rt === 'replies'),
      seg('thIsLight', th === 'light', () => this.setState({ theme: 'light' })), seg('thIsDark', th === 'dark', () => this.setState({ theme: 'dark' })),
      seg('thIsSystem', th === 'system', () => this.setState({ theme: 'system' })));
  }
}
