# Assembles project/Main.dc.html and project/Mac.dc.html from src/main_script.js, src/build_body.py and src/build_mac.py,
# then copies the project to serve/ (generated, not committed) for local testing. Run: python3 ui/mock/src/build.py
import importlib.util, re, shutil, os, glob
SRC = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(SRC))
os.makedirs('serve', exist_ok=True)
js = open(os.path.join(SRC, 'main_script.js')).read()
def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SRC, name + '.py')); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
bb = load('build_body'); bm = load('build_mac')
helmet_src = open('project/Main.dc.html').read()
helmet = helmet_src[helmet_src.index('<helmet>') + 8:helmet_src.index('</helmet>')]
for fname, body, dev, w, h in (('Main', bb.BODY.replace('{{{{', '{{').replace('}}}}', '}}'), 'phone', 390, 844), ('Mac', bm.BODY, 'mac', 1440, 900)):
    cur = open(f'project/{fname}.dc.html').read()
    head = cur[:cur.index('<x-dc>')]
    props = '{"theme":{"editor":"enum","options":["system","light","dark"],"default":"system"},"health":{"editor":"enum","options":["ok","failed"],"default":"ok"},"find":{"editor":"enum","options":["found","notfound","differs","twice"],"default":"found"},"gate":{"editor":"enum","options":["ok","refused"],"default":"ok"},"draft":{"editor":"enum","options":["ok","factcheck","error"],"default":"ok"},"$preview":{"width":%d,"height":%d}}' % (w, h)
    if os.environ.get('ORIGPROPS'):
        props = '{"theme":{"editor":"enum","options":["system","light","dark"],"default":"system"},"health":{"editor":"enum","options":["ok","failed"],"default":"ok"},"find":{"editor":"enum","options":["found","notfound"],"default":"found"},"gate":{"editor":"enum","options":["ok","refused"],"default":"ok"},"$preview":{"width":%d,"height":%d}}' % (w, h)
    xb = body.replace('__HELMET__', helmet)
    hs, he = xb.index('<helmet>'), xb.index('</helmet>')
    # curly apostrophes in visible text only (text nodes, never the helmet CSS or attributes)
    xb = xb[:he] + re.sub(r'>([^<]*)<', lambda m: '>' + re.sub(r"(?<=[A-Za-z])'(?=[A-Za-z])", '’', m.group(1)) + '<', xb[he:])
    out = head + xb + '\n' + f"<script type=\"text/x-dc\" data-dc-script data-props='{props}'>\n" + js.replace('__DEVICE__', dev) + "</script>\n</body>\n</html>\n"
    open(f'project/{fname}.dc.html', 'w').write(out)
    holes = len(re.findall(r'(?<!\{)\{[a-zA-Z]\w*\}(?!\})', out[out.index('<x-dc>'):out.index('</x-dc>')]))
    print(fname, len(out), 'quad', out.count('{{{{'), 'single-brace holes', holes)
for f in glob.glob('project/*.dc.html'):
    shutil.copy(f, 'serve/')
# Test support: the helper the scenarios inject, and one light page per canvas tweak (failure states).
shutil.copy('test/t.js', 'serve/t.js')
dark = open('project/PhoneDark.dc.html').read()
for name, attr in (('notfound', 'find="notfound"'), ('differs', 'find="differs"'), ('twice', 'find="twice"'),
                   ('refused', 'gate="refused"'), ('factcheck', 'draft="factcheck"'), ('draftfail', 'draft="error"'),
                   ('health', 'health="failed"')):
    page = dark.replace('<dc-import name="Main" theme="dark" hint-size', f'<dc-import name="Main" theme="light" {attr} hint-size').replace('#15140F', '#F3F1EA')
    open(f'serve/T-{name}.dc.html', 'w').write(page)
