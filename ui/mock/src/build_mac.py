# Builds the MacBook mock's <x-dc> body from the same pieces as the iPhone.
import importlib.util, re
spec = importlib.util.spec_from_file_location('bb', __file__.replace('build_mac.py', 'build_body.py'))
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
MONO, SERIF, CARD, SUB, EYEBROW, AMBER, LINKBTN = bb.MONO, bb.SERIF, bb.CARD, bb.SUB, bb.EYEBROW, bb.AMBER, bb.LINKBTN

def fix(s):
    return s.replace('{{{{', '{{').replace('}}}}', '}}')

def no_avatar(s):
    return s.replace(bb.AV, '')

# --- Today: split the phone block into the header (full width on Mac) and the rest
today = bb.TODAY
hdr_start = today.index('<div style="display: flex; flex-direction: column; gap: 8px">')
hdr_end = today.index('</div>\n</div>', today.index('{{healthLine}}')) + len('</div>\n</div>')
today_rest = today[:hdr_start] + today[hdr_end:]
today_rest = today_rest.replace('<sc-if value="{{isToday}}" hint-placeholder-val="{{ true }}">\n', '', 1)
today_rest = today_rest[:today_rest.rindex('</sc-if>')]
today_rest = re.sub(r'<button onClick="\{\{goPost\}\}" style="flex-shrink: 0; min-height: 44px;[^>]*>Preview</button>\n', '', today_rest)
# the health alert stays in the full-width header
alert_start = today_rest.index('<sc-if value="{{healthBad}}"')
alert_end = today_rest.index('</sc-if>', alert_start) + len('</sc-if>')
health_alert = today_rest[alert_start:alert_end]
today_rest = today_rest[:alert_start] + today_rest[alert_end:]

MAC_HEADER = f'''<div style="display: flex; flex-direction: column; gap: 8px">
<div style="{EYEBROW}">{{{{{{{{todayLabel}}}}}}}}</div>
<h1 style="margin: 0; font-family: {SERIF}; font-weight: 400; font-size: 44px; line-height: 1.08; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{{{{{{{{headline}}}}}}}}</h1>
<div style="display: flex; align-items: center; gap: 8px; font-size: 13.5px; color: var(--muted); line-height: 1.4"><span style="width: 8px; height: 8px; border-radius: 50%; background: {{{{{{{{healthDot}}}}}}}}; flex-shrink: 0"></span>{{{{{{{{healthLine}}}}}}}}</div>
</div>
{health_alert}'''

# --- the cards and the posting steps sit in the right column
post = bb.POST
post = post.replace('<sc-if value="{{isPost}}" hint-placeholder-val="{{ false }}">\n', '', 1)
post = post[:post.rindex('</sc-if>')]
post = re.sub(r'<button onClick="\{\{goToday\}\}"[^>]*>‹ Today</button>\n', '', post)
post = post.replace(f'<h1 style="{bb.H1}; font-size: 34px">{{{{postTitle}}}}</h1>',
                    f'<h2 data-te-cards="1" tabindex="-1" style="margin: 0; font-family: {SERIF}; font-weight: 400; font-size: 30px; scroll-margin-top: 24px">The cards · {{{{{{{{postTitle}}}}}}}}</h2>')
ready = bb.READY
ready = ready.replace('<sc-if value="{{isReady}}" hint-placeholder-val="{{ false }}">\n', '', 1)
ready = ready[:ready.rindex('</sc-if>')]
ready = re.sub(r'<button onClick="\{\{goToday\}\}"[^>]*>‹ Today</button>\n', '', ready)
ready = ready.replace(f'<h1 style="{bb.H1}; font-size: 34px">Posting</h1>', f'<h2 style="margin: 0; font-family: {SERIF}; font-weight: 400; font-size: 30px">Posting</h2>')

HOME = f'''<sc-if value="{{{{isHome}}}}" hint-placeholder-val="{{{{ true }}}}">
<div style="display: flex; flex-direction: column; gap: 24px">
{MAC_HEADER}
<div style="display: grid; grid-template-columns: 440px minmax(0, 1fr); gap: 40px; align-items: start">
<div style="display: flex; flex-direction: column; gap: 22px">{today_rest}</div>
<div style="display: flex; flex-direction: column; gap: 18px">
<sc-if value="{{{{isHomeCards}}}}" hint-placeholder-val="{{{{ true }}}}">
<div style="display: flex; flex-direction: column; gap: 18px">{post}</div>
</sc-if>
<sc-if value="{{{{isHomeReady}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 16px">{ready}</div>
</sc-if>
</div>
</div>
</div>
</sc-if>'''

def narrow(block, width=820):
    # single-column pages read better at a comfortable measure
    first = block.index('>\n') + 2
    return block[:first] + f'<div style="max-width: {width}px; display: flex; flex-direction: column; gap: 20px">\n' + block[first:block.rindex('</sc-if>')] + '</div>\n</sc-if>'

POSTS = narrow(no_avatar(bb.POSTS))
CAPTURE = narrow(no_avatar(bb.CAPTURE))
REPLIES = narrow(no_avatar(bb.REPLIES), 880)
RESULTS = narrow(no_avatar(bb.RESULTS), 960).replace(
    'grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px">\n<sc-for list="{{kpis}}"',
    'grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px">\n<sc-for list="{{kpis}}"')
RESULTS = RESULTS.replace('font-size: 22px; line-height: 1.2"><span style="display: block">Every profile', 'font-size: 27px; line-height: 1.2"><span style="display: block">Every profile')

cortex = no_avatar(bb.CORTEX).replace('gap: 22px; padding-bottom: 84px', 'gap: 22px')
cortex_inner = cortex[cortex.index('>\n') + 2:cortex.rindex('</sc-if>')]
CORTEX = f'''<sc-if value="{{{{isCortex}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: grid; grid-template-columns: minmax(0, 1fr) 400px; gap: 32px; align-items: start">
<div style="display: flex; flex-direction: column; gap: 22px">{cortex_inner}</div>
<aside aria-label="Ask Cortex" style="position: sticky; top: 0; height: 820px; box-sizing: border-box; border-radius: 24px; background: linear-gradient(180deg, var(--sheet-top) 0%, var(--sheet-mid) 45%, var(--paper) 100%); border: 1px solid var(--chip-line); display: flex; flex-direction: column; overflow: hidden">
{bb.CHAT_INNER.replace(bb.HANDLE, '').replace('<button onClick="{{closeChat}}" style="' + LINKBTN + '; font-size: 15px; font-weight: 600">Done</button>', '')}
</aside>
</div>
</sc-if>'''

def nav(key, label, icon, extra=''):
    return (f'<button onClick="{{{{go{key}}}}}" aria-current="{{{{tab{key}Current}}}}" aria-label="{{{{tab{key}Label}}}}" style="position: relative; min-height: 44px; border: none; border-radius: 10px; background: {{{{nav{key}Bg}}}}; '
            f'display: flex; align-items: center; gap: 12px; padding: 0 12px; cursor: pointer; font-size: 14.5px; font-weight: {{{{tab{key}Weight}}}}; text-align: left; color: var(--ink)">'
            f'<span aria-hidden="true" style="position: absolute; left: 0; top: 10px; bottom: 10px; width: 3px; border-radius: 2px; background: {{{{nav{key}Bar}}}}"></span>{icon}{label}{extra}</button>')

ICON = lambda d: f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
BADGE = f'<sc-if value="{{{{hasWaiting}}}}" hint-placeholder-val="{{{{ true }}}}"><span aria-hidden="true" style="margin-left: auto; min-width: 22px; height: 22px; border-radius: 11px; background: var(--amber-fill); color: var(--on-amber); font-family: {MONO}; font-size: 12px; display: flex; align-items: center; justify-content: center; padding: 0 6px; box-sizing: border-box">{{{{waitingCount}}}}</span></sc-if>'

KBD = f'<span aria-hidden="true" title="Ask Cortex from any page" style="margin-left: auto; font-family: {MONO}; font-size: 12px; color: var(--muted)">⌘K</span>'

SIDEBAR = f'''<aside style="width: 248px; flex-shrink: 0; box-sizing: border-box; border-right: 1px solid var(--line); background: var(--raised); padding: 28px 16px 18px; display: flex; flex-direction: column; gap: 26px">
<div style="display: flex; flex-direction: column; gap: 2px; padding: 0 12px"><span style="font-family: {SERIF}; font-size: 26px; line-height: 1.1">Thread Engine</span><span style="font-family: {MONO}; font-size: 12px; color: var(--muted)">@exitzerocode</span></div>
<nav aria-label="Sections" inert="{{{{navInert}}}}" style="display: flex; flex-direction: column; gap: 4px">
{nav('Today', 'Today', ICON('<circle cx="12" cy="12" r="4"></circle><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4"></path>'))}
{nav('Posts', 'Posts', ICON('<rect x="4" y="4" width="16" height="6" rx="1.5"></rect><rect x="4" y="14" width="16" height="6" rx="1.5"></rect>'))}
{nav('Replies', 'Replies', ICON('<path d="M20 12a7 7 0 0 1-10.3 6.2L5 19.5l1.3-4.2A7 7 0 1 1 20 12z"></path>'), BADGE)}
{nav('Results', 'Results', ICON('<path d="M5 20V11M12 20V5M19 20v-6"></path>'))}
{nav('Cortex', 'Cortex', ICON('<circle cx="6" cy="7" r="2.2"></circle><circle cx="18" cy="6" r="2.2"></circle><circle cx="12" cy="17.5" r="2.2"></circle><path d="M8.2 6.8l7.6-.6M7.2 9l3.7 6.5M16.9 8l-3.8 7.5"></path>'), KBD)}
</nav>
<div style="margin-top: auto; display: flex; flex-direction: column; gap: 10px; padding: 14px; border: 1px solid var(--line); border-radius: 14px; background: var(--card)">
<div style="display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--text2)"><span style="width: 8px; height: 8px; border-radius: 50%; background: {{{{healthDot}}}}"></span>{{{{sideHealth}}}}</div>
<div style="display: flex; justify-content: space-between; font-size: 13px"><span>Followers</span><span style="font-family: {MONO}">36</span></div>
<div style="display: flex; flex-direction: column; gap: 6px"><div style="display: flex; justify-content: space-between; font-size: 13px"><span>Verified followers</span><span style="font-family: {MONO}">27 of 500</span></div><div style="height: 5px; border-radius: 3px; background: var(--track-blue); overflow: hidden"><div style="width: 5.4%; height: 100%; background: var(--chart-on)"></div></div></div>
<div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px"><span>Export due</span><span style="font-family: {MONO}; font-size: 12px; color: var(--text2)">Thu 1 Oct</span></div>
</div>
<div style="display: flex; align-items: center; gap: 6px">
<button onClick="{{{{toggleSettings}}}}" aria-label="{{{{avatarLabel}}}}" aria-expanded="{{{{settingsOpen}}}}" style="flex-grow: 1; min-width: 0; display: flex; align-items: center; gap: 12px; min-height: 52px; padding: 4px 10px; border: none; border-radius: 12px; background: {{{{profileBg}}}}; cursor: pointer; text-align: left">
<span style="position: relative; width: 36px; height: 36px; border-radius: 50%; background: var(--btn); color: var(--on-btn); display: flex; align-items: center; justify-content: center; font-family: {MONO}; font-size: 12px; flex-shrink: 0">EZ<sc-if value="{{{{healthBad}}}}" hint-placeholder-val="{{{{ false }}}}"><span aria-hidden="true" style="position: absolute; top: -2px; right: -2px; width: 12px; height: 12px; border-radius: 50%; background: var(--amber-fill); box-shadow: 0 0 0 2px var(--raised)"></span></sc-if></span>
<span style="display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 600">Exit Zero Code</span><span style="font-size: 12px; color: var(--muted)">Settings and health</span></span>
</button>
{bb.THEME_TOGGLE}
</div>
</aside>'''

def modal(show, close, label, inner, width):
    return f'''<sc-if value="{{{{{show}}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="position: absolute; left: 0; top: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center">
<div onClick="{{{{{close}}}}}" aria-hidden="true" style="position: absolute; left: 0; top: 0; right: 0; bottom: 0; background: var(--scrim); cursor: pointer"></div>
<div role="dialog" aria-modal="true" aria-label="{label}" onKeyDown="{{{{sheetKey}}}}" class="te-sheet-in" style="position: relative; width: {width}px; max-height: 820px; overflow-y: auto; border-radius: 22px; background: var(--raised); display: flex; flex-direction: column; box-shadow: 0 24px 60px rgba(23, 22, 15, 0.25)">
{inner.replace(bb.HANDLE, '')}
</div>
</div>
</sc-if>'''

DRAWER = f'''<sc-if value="{{{{showDrawer}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="position: absolute; left: 0; top: 0; right: 0; bottom: 0; display: flex; justify-content: flex-end">
<div onClick="{{{{closeChat}}}}" aria-hidden="true" style="position: absolute; left: 0; top: 0; right: 0; bottom: 0; background: var(--scrim); cursor: pointer"></div>
<div role="dialog" aria-modal="true" aria-label="Ask Cortex" onKeyDown="{{{{sheetKey}}}}" class="te-sheet-in" style="position: relative; width: 440px; height: 100%; background: linear-gradient(180deg, var(--sheet-top) 0%, var(--sheet-mid) 45%, var(--paper) 100%); display: flex; flex-direction: column; box-shadow: -12px 0 40px rgba(120, 60, 160, 0.16)">
{bb.CHAT_INNER.replace(bb.HANDLE, '')}
</div>
</div>
</sc-if>'''

POPOVER = f'''<sc-if value="{{{{settingsOpen}}}}" hint-placeholder-val="{{{{ false }}}}">
<div onClick="{{{{closeSettings}}}}" aria-hidden="true" style="position: absolute; left: 0; top: 0; right: 0; bottom: 0"></div>
<div role="dialog" aria-modal="true" aria-label="Settings and health" onKeyDown="{{{{sheetKey}}}}" class="te-sheet-in" style="position: absolute; left: 16px; bottom: 80px; width: 400px; max-height: 780px; overflow-y: auto; box-sizing: border-box; background: var(--raised); border: 1px solid var(--line); border-radius: 20px; display: flex; flex-direction: column; box-shadow: 0 18px 50px rgba(23, 22, 15, 0.18)">
{bb.SETTINGS_INNER.replace(bb.HANDLE, '').replace(bb.THEME_TOGGLE, '').replace('Match iPhone', 'Match Mac')}
</div>
</sc-if>'''

BODY = f'''<x-dc>
<helmet>__HELMET__</helmet>
<div class="te-root" onKeyDown="{{{{rootKey}}}}" data-theme="{{{{themeAttr}}}}" style="width: 1440px; height: 900px; box-sizing: border-box; display: flex; background: var(--paper); color: var(--ink); overflow: hidden; position: relative">
{bb.ORB_DEFS}
{SIDEBAR}
<main inert="{{{{mainInert}}}}" style="flex-grow: 1; overflow-y: auto; padding: 36px 44px 44px; box-sizing: border-box">
{HOME}
{POSTS}
{CAPTURE}
{REPLIES}
{RESULTS}
{CORTEX}
</main>
{modal('hasSource', 'closeSource', 'Source', bb.SOURCE_INNER, 540)}
{modal('editorOpen', 'closeEditor', 'Change something', bb.EDITOR_INNER, 640)}
{modal('hookOpen', 'closeHook', 'Choose a hook', bb.HOOK_INNER, 560)}
{DRAWER}
{POPOVER}
</div>
</x-dc>'''
BODY = fix(fix(BODY))
