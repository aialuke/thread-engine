"""List every interactive control and every template binding in the mock, and check the handoff inventory covers them.

    python3 ui/mock/test/controls.py                 # print controls as JSON
    python3 ui/mock/test/controls.py --check FILE    # exit 1 if FILE (inventory.yaml) misses a handler binding

A control is a <button>, <a>, <input>, <textarea> or an element with a role of radio, tab or switch.
Its screen is the innermost screen <sc-if> around it (isToday, isPost, ... or a sheet's show flag).
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'project'
SCREEN_FLAGS = {'isToday', 'isPost', 'isReady', 'isPosts', 'isCapture', 'isReplies', 'isResults', 'isCortex',
                'isHome', 'isHomeCards', 'isHomeReady', 'hasSource', 'editorOpen', 'chatOpen', 'settingsOpen',
                'hookOpen', 'showDrawer', 'showPill', 'rtGrowth', 'rtPosts', 'rtReplies'}
CONTROL_TAGS = {'button', 'a', 'input', 'textarea'}
CONTROL_ROLES = {'radio', 'tab', 'switch'}
HOLE = re.compile(r'\{\{\s*([\w.]+)\s*\}\}')


class Walker(HTMLParser):
    def __init__(self, file):
        super().__init__(convert_charrefs=True)
        self.file, self.stack, self.controls, self.open = file, [], [], []

    def handle_starttag(self, tag, attrs):
        a = {k: v or '' for k, v in attrs}
        if tag == 'sc-if':
            m = HOLE.search(a.get('value', ''))
            self.stack.append(('if', m.group(1) if m else '?'))
        elif tag == 'sc-for':
            m = HOLE.search(a.get('list', ''))
            self.stack.append(('for', (m.group(1) if m else '?') + ' as ' + a.get('as', '?')))
        if tag in CONTROL_TAGS or a.get('role') in CONTROL_ROLES:
            handlers = {k: m.group(1) for k, v in a.items() if k.startswith('on') for m in [HOLE.search(v)] if m}
            screens = [v for kind, v in self.stack if kind == 'if' and v in SCREEN_FLAGS]
            conds = [v for kind, v in self.stack if kind == 'if' and v not in SCREEN_FLAGS]
            loops = [v for kind, v in self.stack if kind == 'for']
            c = {'file': self.file, 'line': self.getpos()[0], 'tag': tag, 'role': a.get('role') or None,
                 'aria_label': a.get('aria-label') or None, 'href': a.get('href') or None, 'handlers': handlers,
                 'disabled': a.get('disabled') or None, 'screen': screens[-1] if screens else None,
                 'shown_if': conds, 'in_list': loops, 'text': ''}
            self.controls.append(c)
            if tag not in ('input',):
                self.open.append([tag, c, 0])

    def handle_endtag(self, tag):
        if tag in ('sc-if', 'sc-for') and self.stack:
            self.stack.pop()
        if self.open and self.open[-1][0] == tag:
            if self.open[-1][2] == 0:
                self.open.pop()
            else:
                self.open[-1][2] -= 1

    def handle_data(self, data):
        for o in self.open:
            o[1]['text'] = (o[1]['text'] + ' ' + data.strip()).strip()


def controls():
    out = []
    for f in ('Main.dc.html', 'Mac.dc.html', 'Thinking.dc.html', 'WorkingStates.dc.html'):
        text = (ROOT / f).read_text()
        body = text[text.index('<x-dc>'):text.index('</x-dc>')]
        w = Walker(f)
        w.feed(body)
        for c in w.controls:
            c['text'] = re.sub(r'\s+', ' ', c['text'])[:80]
        out.extend(w.controls)
    return out


def bindings(f):
    text = (ROOT / f).read_text()
    body = text[text.index('<x-dc>'):text.index('</x-dc>')]
    return sorted(set(HOLE.findall(body)))


if __name__ == '__main__':
    cs = controls()
    if len(sys.argv) == 3 and sys.argv[1] == '--check':
        inv = Path(sys.argv[2]).read_text()
        names = sorted({h for c in cs for h in c['handlers'].values()})
        missing = [n for n in names if n.split('.')[-1] not in inv]
        print(f'{len(names)} handler bindings, {len(missing)} missing from {sys.argv[2]}')
        for n in missing:
            print('  missing:', n)
        sys.exit(1 if missing else 0)
    print(json.dumps({'controls': cs, 'bindings': {f: bindings(f) for f in ('Main.dc.html', 'Mac.dc.html', 'Thinking.dc.html', 'WorkingStates.dc.html')}}, indent=1))
