# UI mock: source and tests

The clickable mock of the Thread Engine UI, version 22 (25 Sep 2026). Published as a Design canvas: https://claude.ai/artifact/8zaBcxWAknJaXWkReQQPqg. This folder is the source of truth for it. The build handoff is in `reviews/ui-build-handoff/`.

## Layout

| Path | What it is |
|---|---|
| `project/` | The canvas's files, exactly as published. `canvas.json` is the board index. `Main.dc.html` (iPhone, 390×844) and `Mac.dc.html` (1440×900) are generated; `PhoneDark` and `MacDark` import them with `theme="dark"`; `Thinking.dc.html` is the working line; `WorkingStates.dc.html` is the gallery. |
| `src/main_script.js` | The one script both devices run. `DEVICE` is replaced with `phone` or `mac` at build time. Data constants first, then the `Component` class (`renderVals()` returns every template binding). |
| `src/build_body.py` | The iPhone template, as named pieces (`TODAY`, `POST`, `READY`, `POSTS`, `CAPTURE`, `REPLIES`, `RESULTS`, `CORTEX`, sheets, `NAV`). |
| `src/build_mac.py` | The Mac layout, built from the same pieces so the two can't drift. |
| `src/build.py` | Assembles `project/Main.dc.html` and `project/Mac.dc.html`, then fills `serve/` for testing. |
| `test/` | Headless Chrome checks (`run.js`, `shots.js`, `sheet.js`), the page helper (`t.js`), scenarios, and `controls.py` (every control and binding, and the inventory check). |

## Format rules that bite

`.dc.html` is the Design canvas's component format. `{{hole}}` is a dotted lookup into `renderVals()`, never an expression. `<sc-if value>` and `<sc-for list as>` are the only control flow. `<dc-import name="Thinking" cmd on-done>` embeds a component; kebab-case attributes become camelCase props. The canvas forbids global keydown handlers, so keys are handled on the `.te-root` element (`onKeyDown="{{rootKey}}"`). `inert` must be the string `'true'` or `null` (React 18 drops a boolean).

## Edit, build, test

The operator doesn't run these; an agent does.

From the repo root:

```
python3 ui/mock/src/build.py                                   # regenerate project/ and serve/
python3 ui/mock/test/controls.py --check reviews/ui-build-handoff/inventory.yaml
# The canvas runtime isn't committed (it belongs to the Design type). Fetch it once:
#   Artifact read, url above, path "artifact-type/dc-runtime.js" → save as ui/mock/serve/support.js
(cd ui/mock/serve && python3 -m http.server 8766 --bind 127.0.0.1) &
(cd ui/mock/test && npm install)                               # playwright-core only; uses the system Chrome
(cd ui/mock/test && node run.js Main.dc.html scenarios/f1.js)  # one scenario against port 8766
(cd ui/mock/test && node shots.js Main.dc.html light shots/Main-light && node sheet.js shots/Main-light sheet 7 300)
```

Scenarios: `f1` sheets, editor, counter, hold cancel; `f2` approve, checks, posting, timers; `f3` refusals, slot moves, reminders, settings, chat; `f4` capture, replies, results, review, hooks; `m2`/`m3` Mac; `tw` every canvas tweak (`serve/T-*.dc.html`); `gal` gallery; `smoke` load check. `t.js` gives scenarios `T.click`, `T.grab`, `T.setNow(iso)` (moves the clock), `T.overflow()` and more. Never read the clipboard from a script in a real Chrome tab: it raises a permission prompt that freezes the tab.

## Publishing

Publish to the same artifact URL with `root` = `ui/mock`, `file_path` = one changed `project/*.dc.html`, and the other changed files in `files` by their `project/…` paths. Send `canvas.json` only when boards move, resize or retitle.
