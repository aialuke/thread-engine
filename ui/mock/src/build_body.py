# Generates the <x-dc> body markup for the iPhone mock (Main.dc.html).
MONO = "'IBM Plex Mono', monospace"
SERIF = "'Instrument Serif', Georgia, serif"
SANS = "'IBM Plex Sans', system-ui, sans-serif"
CARD = "background: var(--card); border: 1px solid var(--line); border-radius: 18px"
EYEBROW = f"font-family: {MONO}; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted)"
H1 = f"margin: 0; font-family: {SERIF}; font-weight: 400; font-size: 36px; line-height: 1.05"
H2 = "margin: 0; font-size: 15px; font-weight: 600"
PRIMARY = "min-height: 52px; border-radius: 12px; border: none; background: var(--btn); color: var(--on-btn); font-size: 16px; font-weight: 600; cursor: pointer"
SECONDARY = "min-height: 48px; padding: 0 16px; border-radius: 12px; border: 1px solid var(--line); background: var(--raised); font-size: 15px; font-weight: 600; cursor: pointer"
LINKBTN = "min-height: 44px; border: none; background: none; padding: 0; color: var(--blue); font-size: 14px; font-weight: 500; cursor: pointer; text-align: left"
AMBER = "font-size: 14px; color: var(--amber); background: var(--amber-soft); border-radius: 14px; padding: 12px 14px; line-height: 1.45"
NOTE = "font-size: 13.5px; color: var(--text2); background: var(--line2); border-radius: 14px; padding: 12px 14px; line-height: 1.45"
SUB = "font-size: 12.5px; color: var(--muted); line-height: 1.4"
CHIP_AMBER = "font-size: 12px; font-weight: 600; color: var(--amber); background: var(--amber-soft); padding: 4px 10px; border-radius: 999px"
CHIP_BLUE = "font-size: 12px; font-weight: 600; color: var(--blue); background: var(--blue-soft); padding: 4px 10px; border-radius: 999px"
CHIP_NEUTRAL = "font-size: 12px; font-weight: 600; color: var(--text2); background: var(--line2); padding: 4px 10px; border-radius: 999px"

AV = ('<button onClick="{{openSettings}}" aria-label="{{avatarLabel}}" style="position: relative; flex-shrink: 0; width: 44px; height: 44px; '
      f'border-radius: 50%; border: none; background: var(--btn); color: var(--on-btn); font-family: {MONO}; font-size: 12px; cursor: pointer">EZ'
      '<sc-if value="{{healthBad}}" hint-placeholder-val="{{ false }}"><span aria-hidden="true" style="position: absolute; top: 0; right: 0; width: 12px; '
      'height: 12px; border-radius: 50%; background: var(--amber-fill); box-shadow: 0 0 0 2px var(--paper)"></span></sc-if></button>')

def orb(n):
    return (f'<svg width="{n}" height="{n}" viewBox="0 0 24 24" aria-hidden="true" style="flex-shrink: 0"><circle cx="12" cy="12" r="10" fill="url(#te-orb)"></circle>'
            '<path d="M8.3 9.5l7.2-1M8.2 10.5l3.1 5.2M15.7 9.6l-3.2 5.6" stroke="#FFFFFF" stroke-width="1.3" stroke-linecap="round"></path>'
            '<circle cx="8" cy="9.7" r="1.5" fill="#FFFFFF"></circle><circle cx="15.8" cy="8.6" r="1.5" fill="#FFFFFF"></circle><circle cx="12" cy="16.1" r="1.5" fill="#FFFFFF"></circle></svg>')

ORB_DEFS = ('<svg width="0" height="0" aria-hidden="true" style="position: absolute"><defs><linearGradient id="te-orb" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#F28AD0"></stop><stop offset="0.5" stop-color="#9C8CFF"></stop><stop offset="1" stop-color="#FFB27A"></stop>'
            '</linearGradient></defs></svg>')

ASK = lambda handler, label: (f'<button onClick="{{{{{handler}}}}}" style="align-self: flex-start; display: flex; align-items: center; gap: 8px; min-height: 44px; '
                              f'padding: 0 16px 0 10px; border-radius: 999px; border: 1px solid var(--chip-line); background: var(--chip-bg); font-size: 14px; font-weight: 500; cursor: pointer">{orb(22)}{label}</button>')

CHECK = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex-shrink: 0"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg>'
LOCK = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex-shrink: 0; margin-top: 2px"><rect x="5" y="11" width="14" height="9" rx="2"></rect><path d="M8 11V8a4 4 0 0 1 8 0v3"></path></svg>'

def header(title, eyebrow=None):
    eb = f'<div style="{EYEBROW}">{eyebrow}</div>' if eyebrow else '<span></span>'
    return (f'<div style="display: flex; flex-direction: column; gap: 8px">\n'
            f'<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px">{eb}{AV}</div>\n'
            f'<h1 style="{H1}">{title}</h1>\n</div>')

def step(num, title, show_var, body):
    return (f'<section aria-disabled="{{{{{show_var}Off}}}}" style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 12px">\n'
            f'<div style="display: flex; gap: 12px; align-items: center"><span style="width: 28px; height: 28px; border-radius: 50%; background: {{{{{show_var}Badge}}}}; color: var(--on-btn); display: flex; align-items: center; justify-content: center; font-family: {MONO}; font-size: 12px">{num}</span>'
            f'<h2 style="{H2}; color: {{{{{show_var}Head}}}}">{title}</h2></div>\n{body}\n</section>')

TODAY = f'''<sc-if value="{{{{isToday}}}}" hint-placeholder-val="{{{{ true }}}}">
<div style="display: flex; flex-direction: column; gap: 22px">
<div style="display: flex; flex-direction: column; gap: 8px">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px"><div style="{EYEBROW}">{{{{todayLabel}}}}</div>{AV}</div>
<h1 style="{H1}">{{{{headline}}}}</h1>
<div style="display: flex; align-items: center; gap: 8px; {SUB}"><span style="width: 8px; height: 8px; border-radius: 50%; background: {{{{healthDot}}}}; flex-shrink: 0"></span>{{{{healthLine}}}}</div>
</div>
<sc-if value="{{{{healthBad}}}}" hint-placeholder-val="{{{{ false }}}}">
<div role="alert" style="{AMBER}; display: flex; flex-direction: column; gap: 8px"><span>Last night's daily check didn't run, probably because the Mac was asleep. Numbers are from the night before.</span><button onClick="{{{{fixHealth}}}}" style="{LINKBTN}; color: var(--amber); font-weight: 600">Run it now</button></div>
</sc-if>

<sc-if value="{{{{showFirstHour}}}}" hint-placeholder-val="{{{{ false }}}}">
<section aria-label="First hour" style="{CARD}; border-color: var(--blue-line); padding: 18px; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 10px"><h2 style="{H2}; font-size: 17px">First hour</h2><span style="font-family: {MONO}; font-size: 12px; color: var(--muted)">closes {{{{fhClose}}}}</span></div>
<div style="font-size: 14.5px; line-height: 1.45">Posted {{{{foundAt}}}}. The first like came 3 minutes later, so strangers can start seeing it. <span style="{CHIP_NEUTRAL}; font-size: 12px">example</span></div>
<div style="display: flex; flex-direction: column; gap: 8px; border-top: 1px solid var(--line2); padding-top: 12px">
<span style="font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted)">Answer now</span>
<div style="font-size: 14px; line-height: 1.45">@builder.two asked whether Bruno handles GraphQL. <a href="https://x.com" target="_blank" rel="noopener" style="font-weight: 600">Answer on X ↗</a></div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px; border-top: 1px solid var(--line2); padding-top: 12px">
<span style="font-size: 14px">Roughly how long did this post take you?</span>
<div role="radiogroup" aria-label="Time taken" style="display: flex; gap: 8px; flex-wrap: wrap">
<sc-for list="{{{{minuteChips}}}}" as="mc" hint-placeholder-count="4"><button role="radio" aria-checked="{{{{mc.on}}}}" onClick="{{{{mc.pick}}}}" style="min-height: 44px; padding: 0 16px; border-radius: 999px; border: 1px solid {{{{mc.border}}}}; background: {{{{mc.bg}}}}; font-size: 14px; font-weight: {{{{mc.weight}}}}; cursor: pointer">{{{{mc.label}}}}</button></sc-for>
</div>
</div>
<button onClick="{{{{closeFirstHour}}}}" style="{LINKBTN}">Close the first-hour card</button>
</section>
</sc-if>

<section aria-label="Next post" style="{CARD}; padding: 18px; display: flex; flex-direction: column; gap: 16px">
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px">
<div style="display: flex; flex-direction: column; gap: 4px"><span style="font-size: 12px; color: var(--muted)">{{{{cardEyebrow}}}}</span><span style="font-size: 18px; font-weight: 600; line-height: 1.25">PAID → FREE: developer tools</span></div>
<button onClick="{{{{goPost}}}}" style="flex-shrink: 0; min-height: 44px; padding: 0 14px; border-radius: 10px; border: 1px solid var(--line); background: var(--raised); font-size: 13.5px; font-weight: 600; cursor: pointer">Preview</button>
</div>
<div style="display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; font-family: {MONO}; font-size: 13px"><span style="font-weight: 500">{{{{whenLabel}}}}</span><span style="color: {{{{countdownColor}}}}">{{{{countdown}}}}</span></div>
<ol aria-label="Where this post is" style="list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 4px">
<sc-for list="{{{{steps}}}}" as="st" hint-placeholder-count="5">
<li aria-current="{{{{st.current}}}}" style="display: flex; flex-direction: column; align-items: center; gap: 6px">
<div style="width: 100%; height: 4px; border-radius: 2px; background: {{{{st.bar}}}}"></div>
<div style="font-size: 12px; color: {{{{st.color}}}}; font-weight: {{{{st.weight}}}}; white-space: nowrap">{{{{st.mark}}}}{{{{st.label}}}}<span class="te-sr">{{{{st.state}}}}</span></div>
</li>
</sc-for>
</ol>
<sc-if value="{{{{thinkingReady}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="border-top: 1px solid var(--line2); padding-top: 14px"><dc-import name="Thinking" cmd="ready" on-done="{{{{doneReady}}}}" hint-size="100%,110px"></dc-import></div>
</sc-if>
<sc-if value="{{{{showPrimary}}}}" hint-placeholder-val="{{{{ true }}}}">
<div style="display: flex; flex-direction: column; gap: 8px">
<button onClick="{{{{primaryAction}}}}" disabled="{{{{primaryDisabled}}}}" style="{PRIMARY}; opacity: {{{{primaryOpacity}}}}">{{{{primaryLabel}}}}</button>
<div style="{SUB}; text-align: center">{{{{primaryHint}}}}</div>
<sc-if value="{{{{showEarlyAnyway}}}}" hint-placeholder-val="{{{{ false }}}}"><button onClick="{{{{startEarly}}}}" disabled="{{{{busy}}}}" style="{LINKBTN}; align-self: center; opacity: {{{{busyOpacity}}}}">Start posting early anyway</button></sc-if>
</div>
</sc-if>
</section>

<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Progress</h2>
<div style="{CARD}; padding: 4px 16px">
<div style="display: flex; flex-direction: column; gap: 8px; padding: 12px 0; border-bottom: 1px solid var(--line2)">
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 10px"><span style="font-size: 14px">Verified followers</span><span style="font-family: {MONO}; font-size: 15px; font-weight: 500">27 <span style="color: var(--muted); font-weight: 400">of 500</span></span></div>
<div style="height: 8px; border-radius: 4px; background: var(--track-blue); overflow: hidden"><div style="width: 5.4%; height: 100%; background: var(--chart-on)"></div></div>
<span style="{SUB}">About 37 a week reaches X's rewards bar in 90 days.</span>
</div>
<div style="display: flex; flex-direction: column; gap: 8px; padding: 12px 0; border-bottom: 1px solid var(--line2)">
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 10px"><span style="font-size: 14px">Qualified impressions</span><span style="font-family: {MONO}; font-size: 15px; font-weight: 500">337 <span style="color: var(--muted); font-weight: 400">of 500,000</span></span></div>
<div style="height: 8px; border-radius: 4px; background: var(--track-blue); overflow: hidden"><div style="width: 0.07%; min-width: 2px; height: 100%; background: var(--chart-on)"></div></div>
<span style="{SUB}">Counted when a verified viewer scrolls past half of one of your original posts in their Home feed. Replies and boosted views don't count. From X's eligibility screen, last read 24 Sep.</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--line2)">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 14px">Followers</span><span style="{SUB}">First daily count 24 Sep; the trend starts from there</span></div>
<span style="font-family: {MONO}; font-size: 15px; font-weight: 500">36</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 12px 0">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 14px">Analytics export</span><span style="{SUB}">On a computer: X → Premium → Analytics → Content → Export. It's the only record of which posts brought followers.</span></div>
<span style="font-family: {MONO}; font-size: 13px; white-space: nowrap; color: var(--text2)">Thu 1 Oct</span>
</div>
</div>
</section>

<section style="display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="{H2}">Replies</h2><button onClick="{{{{goReplies}}}}" style="{LINKBTN}; font-size: 13.5px">All replies</button></div>
<div style="{CARD}; overflow: hidden">
<sc-if value="{{{{hasWaiting}}}}" hint-placeholder-val="{{{{ true }}}}">
<button onClick="{{{{goReplies}}}}" style="width: 100%; text-align: left; border: none; border-bottom: 1px solid var(--line2); background: var(--amber-soft); padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; cursor: pointer; color: var(--amber)">
<span style="font-size: 15px; font-weight: 600">{{{{waitingText}}}}</span>
<sc-for list="{{{{waitingPreview}}}}" as="wp" hint-placeholder-count="2"><span style="font-size: 13px; color: var(--text2)">{{{{wp.handle}}}} · {{{{wp.where}}}}</span></sc-for>
</button>
</sc-if>
<div style="padding: 10px 16px 4px; font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted)">Worth joining</div>
<sc-for list="{{{{replies}}}}" as="r" hint-placeholder-count="3">
<button onClick="{{{{goReplies}}}}" style="width: 100%; text-align: left; border: none; border-bottom: 1px solid var(--line2); background: var(--card); padding: 12px 16px; display: flex; flex-direction: column; gap: 4px; cursor: pointer">
<span style="font-family: {MONO}; font-size: 12px; color: var(--muted)">{{{{r.handle}}}} · found {{{{r.found}}}}</span>
<span style="font-size: 14px; line-height: 1.35">{{{{r.short}}}}</span>
</button>
</sc-for>
</div>
</section>

<section style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Capture</h2>
<span style="font-size: 14px; color: var(--text2); line-height: 1.45">A screenshot, a screen recording or a thought from today's build. Captures become build-log and tool-verdict posts.</span>
<button onClick="{{{{goCapture}}}}" style="{SECONDARY}; align-self: flex-start">Capture something</button>
</section>

<section style="display: flex; flex-direction: column; gap: 10px">
<sc-if value="{{{{showPlanButton}}}}" hint-placeholder-val="{{{{ true }}}}">
<button onClick="{{{{planNext}}}}" disabled="{{{{busy}}}}" style="min-height: 50px; border-radius: 12px; border: 1px solid var(--ink); background: transparent; font-size: 15px; font-weight: 600; cursor: pointer; opacity: {{{{busyOpacity}}}}">Plan the next post</button>
</sc-if>
<sc-if value="{{{{thinkingNext}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="{CARD}; padding: 16px 18px"><dc-import name="Thinking" cmd="next" on-done="{{{{doneNext}}}}" hint-size="100%,150px"></dc-import></div>
</sc-if>
<sc-if value="{{{{proposalShown}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="{CARD}; border-color: var(--blue-line); padding: 18px; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 12px; color: var(--blue); font-weight: 600">Proposed</span><span style="{CHIP_NEUTRAL}">example</span></div>
<div style="font-size: 17px; font-weight: 600">Build log: Claude, Codex and Grok reviewing the same plan</div>
<div style="font-family: {MONO}; font-size: 13px">Tue 29 Sep · 22:00 · no experiment</div>
<div style="font-size: 14px; color: var(--text2); line-height: 1.45">From your voice note and a reader's question. First-hand material beats another list, and 22:00 is morning on the US east coast.</div>
{ASK('askAboutProposal', 'Ask Cortex about this')}
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px">
<button onClick="{{{{acceptProposal}}}}" style="{PRIMARY}; min-height: 48px; font-size: 15px">Accept</button>
<button onClick="{{{{changeProposal}}}}" disabled="{{{{busy}}}}" style="{SECONDARY}; opacity: {{{{busyOpacity}}}}">Pick another</button>
</div>
</div>
</sc-if>
<sc-if value="{{{{proposalAccepted}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="{CARD}; padding: 16px 18px; display: flex; align-items: center; gap: 12px"><span style="color: var(--blue)">{CHECK}</span><div style="display: flex; flex-direction: column; gap: 2px"><span style="font-weight: 600; font-size: 14px">Planned: the build log</span><span style="{SUB}">Tue 29 Sep · 22:00. It's in Posts, ready to draft.</span></div></div>
</sc-if>
</section>
</div>
</sc-if>
'''

POST = f'''<sc-if value="{{{{isPost}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 18px">
<button onClick="{{{{goToday}}}}" style="{LINKBTN}; align-self: flex-start">‹ Today</button>
<div style="display: flex; flex-direction: column; gap: 8px">
<h1 style="{H1}; font-size: 34px">{{{{postTitle}}}}</h1>
<sc-if value="{{{{stageApprove}}}}" hint-placeholder-val="{{{{ true }}}}"><span style="{CHIP_AMBER}; align-self: flex-start">Needs your approval</span></sc-if>
<sc-if value="{{{{stageApprovedOnly}}}}" hint-placeholder-val="{{{{ false }}}}"><span style="{CHIP_BLUE}; align-self: flex-start">Approved at {{{{approvedAt}}}}, as shown</span></sc-if>
<sc-if value="{{{{stagePosted}}}}" hint-placeholder-val="{{{{ false }}}}"><span style="{CHIP_NEUTRAL}; align-self: flex-start">Posted {{{{foundAt}}}}</span></sc-if>
<sc-if value="{{{{editedAfter}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="{AMBER}">You changed a card after approving it, so approve again.</div></sc-if>
<sc-if value="{{{{savedNote}}}}" hint-placeholder-val="{{{{ false }}}}"><div role="status" style="{NOTE}">Saved. Your edit is recorded as a preference, so the loop can learn from it.</div></sc-if>
</div>

<article aria-label="Card 1, as it will look on X" style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; gap: 10px; align-items: center">
<div aria-hidden="true" style="width: 40px; height: 40px; border-radius: 50%; background: var(--btn); color: var(--on-btn); display: flex; align-items: center; justify-content: center; font-family: {MONO}; font-size: 13px">EZ</div>
<div style="display: flex; flex-direction: column"><span style="font-weight: 600; font-size: 15px">Exit Zero Code</span><span style="font-size: 13px; color: var(--muted)">@exitzerocode · {{{{whenCard}}}}</span></div>
</div>
<div style="display: flex; flex-direction: column; font-size: 15px; line-height: 1.4">
<sc-for list="{{{{cardLines}}}}" as="cl" hint-placeholder-count="11">
<div style="display: flex; flex-direction: column">
<sc-if value="{{{{cl.foldBefore}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; align-items: center; gap: 8px; margin: 6px 0; font-family: {MONO}; font-size: 12px; color: var(--muted)"><span style="flex-grow: 1; border-top: 1px dashed var(--dash)"></span>Strangers stop here unless they tap Show more<span style="flex-grow: 1; border-top: 1px dashed var(--dash)"></span></div>
</sc-if>
<sc-if value="{{{{cl.isBlank}}}}" hint-placeholder-val="{{{{ false }}}}"><div aria-hidden="true" style="height: 10px"></div></sc-if>
<sc-if value="{{{{cl.isText}}}}" hint-placeholder-val="{{{{ true }}}}"><div style="opacity: {{{{cl.fade}}}}; white-space: pre-wrap">{{{{cl.text}}}}</div></sc-if>
<sc-if value="{{{{cl.isSwap}}}}" hint-placeholder-val="{{{{ false }}}}"><button onClick="{{{{cl.open}}}}" style="text-align: left; opacity: {{{{cl.fade}}}}; background: {{{{cl.bg}}}}; border: none; border-radius: 6px; padding: 2px 4px; margin: 0 -4px; font-size: 15px; line-height: 1.4; cursor: pointer; text-decoration: underline; text-decoration-color: var(--dash); text-underline-offset: 3px">{{{{cl.text}}}}<span class="te-sr">, show the source</span></button></sc-if>
</div>
</sc-for>
</div>
<div style="display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-family: {MONO}; font-size: 12px; color: {{{{countColor}}}}; padding-top: 4px"><span>{{{{cardCount}}}} characters as X counts · your limit 600</span><span style="color: var(--muted)">Tap an underlined line for its source</span></div>
</article>
{ASK('askAboutPost', 'Ask Cortex about this post')}

<section style="display: flex; flex-direction: column; gap: 8px">
<div style="{SUB}">Then, 10 to 20 minutes later, as a reply. Only people who open your post see this.</div>
<div style="{CARD}; padding: 14px 16px; display: flex; flex-direction: column; gap: 8px">
<div style="font-size: 15px; line-height: 1.4"><span style="color: var(--blue)">@use_bruno</span> thanks for keeping API collections in plain files, and for shipping again this week.</div>
<div style="font-family: {MONO}; font-size: 12px; color: var(--muted)">95 characters as X counts · account checked 24 Sep</div>
</div>
</section>

<sc-if value="{{{{stageApprove}}}}" hint-placeholder-val="{{{{ true }}}}">
<section style="{CARD}; padding: 18px; display: flex; flex-direction: column; gap: 12px">
<h2 style="{H2}; font-size: 16px">Approve both cards</h2>
<div style="font-size: 14px; color: var(--text2); line-height: 1.45">Read them first. Change anything you want: edits before approving cost nothing, and they teach the loop what you prefer.</div>
<button onClick="{{{{openEditor}}}}" disabled="{{{{editDisabled}}}}" style="{SECONDARY}; opacity: {{{{editOpacity}}}}">Change something</button>
<button onPointerDown="{{{{holdStart}}}}" onPointerUp="{{{{holdEnd}}}}" onPointerLeave="{{{{holdEnd}}}}" onPointerCancel="{{{{holdEnd}}}}" onLostPointerCapture="{{{{holdEnd}}}}" onBlur="{{{{holdEnd}}}}" onKeyDown="{{{{holdKeyDown}}}}" onKeyUp="{{{{holdKeyUp}}}}" aria-describedby="te-hold-help" style="position: relative; overflow: hidden; min-height: 54px; border-radius: 12px; border: none; background: var(--btn); color: var(--on-btn); font-size: 16px; font-weight: 600; cursor: pointer; touch-action: none; user-select: none">
<span style="position: absolute; left: 0; top: 0; bottom: 0; width: {{{{holdWidth}}}}; background: var(--hold-fill)"></span>
<span style="position: relative; color: {{{{holdTextColor}}}}">{{{{holdLabel}}}}</span>
</button>
<span id="te-hold-help" style="{SUB}">Press and hold for a second. With a keyboard, hold Space. Approving locks in the cards as shown; nothing is posted.</span>
</section>
</sc-if>
<sc-if value="{{{{stageApprovedOnly}}}}" hint-placeholder-val="{{{{ false }}}}">
<section style="display: flex; flex-direction: column; gap: 10px">
<sc-if value="{{{{isEarly}}}}" hint-placeholder-val="{{{{ true }}}}">
<div style="{NOTE}">{{{{earlyNote}}}}</div>
<button onClick="{{{{startEarly}}}}" disabled="{{{{busy}}}}" style="{LINKBTN}; opacity: {{{{busyOpacity}}}}">Start posting early anyway</button>
</sc-if>
<sc-if value="{{{{showStartHere}}}}" hint-placeholder-val="{{{{ false }}}}">
<button onClick="{{{{startReady}}}}" disabled="{{{{busy}}}}" style="{PRIMARY}; opacity: {{{{busyOpacity}}}}">Start posting</button>
</sc-if>
<sc-if value="{{{{showMoveHere}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="{AMBER}">The slot has passed. Your approval stays.</div>
<button onClick="{{{{moveSlot}}}}" style="{PRIMARY}">{{{{moveLabel}}}}</button>
</sc-if>
<button onClick="{{{{openEditor}}}}" disabled="{{{{editDisabled}}}}" style="{SECONDARY}; opacity: {{{{editOpacity}}}}">Edit a card</button>
</section>
</sc-if>
</div>
</sc-if>
'''

READY = f'''<sc-if value="{{{{isReady}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 16px">
<button onClick="{{{{goToday}}}}" style="{LINKBTN}; align-self: flex-start">‹ Today</button>
<h1 style="{H1}; font-size: 34px">Posting</h1>
<sc-if value="{{{{readyRefused}}}}" hint-placeholder-val="{{{{ false }}}}">
<div role="alert" style="{AMBER}; display: flex; flex-direction: column; gap: 10px"><span style="font-weight: 600">The final check stopped this post.</span><sc-for list="{{{{refusedReasons}}}}" as="rr" hint-placeholder-count="1"><span>{{{{rr.t}}}}</span></sc-for><span>Change the card if it needs it, then read and approve again.</span><button onClick="{{{{reapprove}}}}" style="{PRIMARY}; min-height: 48px; font-size: 15px">Read and approve again</button></div>
</sc-if>
<sc-if value="{{{{readyOk}}}}" hint-placeholder-val="{{{{ true }}}}">
<div style="font-size: 14px; color: var(--text2); line-height: 1.45">The final checks passed. You press Post on X; nothing is posted for you.</div>
<sc-if value="{{{{canBack}}}}" hint-placeholder-val="{{{{ true }}}}"><div style="display: flex; gap: 18px; flex-wrap: wrap"><button onClick="{{{{notNow}}}}" style="{LINKBTN}; font-size: 13.5px">Not now</button><button onClick="{{{{withdraw}}}}" style="{LINKBTN}; font-size: 13.5px">Withdraw approval</button></div></sc-if>
{step(1, 'Post the list', 's1', f"""<sc-if value="{{{{{{{{showCopy1}}}}}}}}" hint-placeholder-val="{{{{{{{{ true }}}}}}}}"><button onClick="{{{{{{{{copy1}}}}}}}}" style="{PRIMARY}; min-height: 50px; font-size: 15px">Copy the post</button></sc-if>
<sc-if value="{{{{{{{{copyFailed}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="alert" style="{AMBER}">Couldn't copy it. Tap Copy again. Nothing old was left for you to paste by mistake.</div></sc-if>
<sc-if value="{{{{{{{{copiedOk}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="status" style="font-size: 14px; color: var(--text2); line-height: 1.45">Copied. Check it starts “PAID → FREE / Finding free developer tools…” when you paste.</div></sc-if>
<sc-if value="{{{{{{{{showCopyAgain}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap"><button onClick="{{{{{{{{copy1}}}}}}}}" style="{SECONDARY}">Copy again</button><a href="https://x.com" target="_blank" rel="noopener" style="min-height: 44px; display: flex; align-items: center; font-size: 14px; font-weight: 600">Open X ↗</a></div></sc-if>
<sc-if value="{{{{{{{{showPosted1}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><button onClick="{{{{{{{{postedIt}}}}}}}}" style="{PRIMARY}; min-height: 50px; font-size: 15px">I've posted it</button></sc-if>
<sc-if value="{{{{{{{{finding}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><dc-import name="Thinking" cmd="find" on-done="{{{{{{{{doneFind}}}}}}}}" hint-size="100%,90px"></dc-import></sc-if>
<sc-if value="{{{{{{{{notFound}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="alert" style="{AMBER}; display: flex; flex-direction: column; gap: 8px"><span>Not on X yet. A new post can take a minute to show up.</span><div style="display: flex; gap: 10px; flex-wrap: wrap"><button onClick="{{{{{{{{postedIt}}}}}}}}" style="{SECONDARY}">Check again</button><button onClick="{{{{{{{{carryOn}}}}}}}}" style="{SECONDARY}">It's up, carry on</button></div></div></sc-if>
<sc-if value="{{{{{{{{posted1}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="status" style="font-size: 14px; color: var(--blue); font-weight: 600">{{{{{{{{foundText}}}}}}}}</div></sc-if>
<sc-if value="{{{{{{{{foundDiff}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="alert" style="{AMBER}">It isn't the same as the card you approved. Check it on X. If you changed it on purpose, the loop records the change as your edit.</div></sc-if>
<sc-if value="{{{{{{{{foundTwice}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="alert" style="{AMBER}">Two posts on X match it. Delete the later one there; the loop counts the first.</div></sc-if>""")}
{step(2, 'Wait, and answer early replies', 's2', f"""<sc-if value="{{{{{{{{posted1}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}">
<div style="display: flex; align-items: baseline; justify-content: space-between"><span style="font-family: {MONO}; font-size: 28px; font-weight: 500">{{{{{{{{waitText}}}}}}}}</span><span style="{SUB}">until the shout-out window opens</span></div>
<div style="height: 6px; border-radius: 3px; background: var(--line2); overflow: hidden"><div style="width: {{{{{{{{waitPct}}}}}}}}; height: 100%; background: var(--blue-fill)"></div></div>
<div style="font-size: 13.5px; color: var(--text2); line-height: 1.45">Post the shout-out between {{{{{{{{winStart}}}}}}}} and {{{{{{{{winEnd}}}}}}}}. No replies yet; new ones show here.</div>
<div style="display: flex; gap: 16px; flex-wrap: wrap"><button onClick="{{{{{{{{skipWait}}}}}}}}" style="{LINKBTN}; font-size: 13px">Skip the wait (mock only)</button><button onClick="{{{{{{{{skipShout}}}}}}}}" style="{LINKBTN}; font-size: 13px">Skip the shout-out</button></div>
</sc-if>""")}
{step(3, 'Thank the maker', 's3', f"""<sc-if value="{{{{{{{{waitDone}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}">
<sc-if value="{{{{{{{{nudgeSent}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="status" style="font-size: 13.5px; color: var(--text2)">Nudge sent at {{{{{{{{winStart}}}}}}}}: the window is open.</div></sc-if>
<sc-if value="{{{{{{{{windowClosed}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="alert" style="{AMBER}">The window closed at {{{{{{{{winEnd}}}}}}}}. Post it now anyway, or skip it.</div></sc-if>
<sc-if value="{{{{{{{{showCopy2}}}}}}}}" hint-placeholder-val="{{{{{{{{ true }}}}}}}}"><button onClick="{{{{{{{{copy2}}}}}}}}" style="{PRIMARY}; min-height: 50px; font-size: 15px">Copy the shout-out</button></sc-if>
<sc-if value="{{{{{{{{copy2Failed}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div role="alert" style="{AMBER}">Couldn't copy the shout-out. Tap Copy the shout-out again. Nothing is recorded until it's on X.</div><button onClick="{{{{{{{{skipShout}}}}}}}}" style="{LINKBTN}; font-size: 13px">Skip the shout-out</button></sc-if>
<sc-if value="{{{{{{{{copied2}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><div style="font-size: 14px; color: var(--text2)">Copied. Reply to your post with it.</div><a href="https://x.com/exitzerocode" target="_blank" rel="noopener" style="align-self: flex-start; min-height: 44px; display: flex; align-items: center; font-size: 14px; font-weight: 600">Open your post on X ↗</a><span style="{SUB}">In the real app this opens the post itself.</span></sc-if>
</sc-if>""")}
{step(4, 'Done', 's4', f"""<sc-if value="{{{{{{{{thinkingPosted}}}}}}}}" hint-placeholder-val="{{{{{{{{ false }}}}}}}}"><dc-import name="Thinking" cmd="{{{{{{{{recordCmd}}}}}}}}" on-done="{{{{{{{{doneRecord}}}}}}}}" hint-size="100%,110px"></dc-import>
<button onClick="{{{{{{{{doneRecord}}}}}}}}" style="{SECONDARY}; align-self: flex-start">Done</button><span style="{SUB}">It records everything once it sees your shout-out. Tap Done if it doesn't.</span></sc-if>""")}
</sc-if>
</div>
</sc-if>
'''

POSTS = f'''<sc-if value="{{{{isPosts}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 20px">
{header('Posts')}
<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Up next</h2>
<button onClick="{{{{goPost}}}}" style="text-align: left; {CARD}; padding: 16px; display: flex; flex-direction: column; gap: 6px; cursor: pointer">
<span style="font-size: 16px; font-weight: 600">PAID → FREE: developer tools</span>
<span style="font-family: {MONO}; font-size: 12.5px; color: var(--muted)">{{{{whenLabel}}}} · {{{{stageName}}}}</span>
</button>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="{H2}">Also drafted</h2><span style="{CHIP_NEUTRAL}">example</span></div>
<div style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 15px; font-weight: 600">Tool verdict: one fix, three reviewers</span><span style="{SUB}">From your voice note. This format opens on a hook you choose.</span></div>
<sc-if value="{{{{hookNotSaved}}}}" hint-placeholder-val="{{{{ true }}}}"><button onClick="{{{{openHook}}}}" style="{SECONDARY}; align-self: flex-start">Choose a hook</button></sc-if>
<sc-if value="{{{{hookSaved}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="display: flex; flex-direction: column; gap: 6px"><span style="font-size: 14px; line-height: 1.4">“{{{{hookChosen}}}}”</span><span style="{SUB}">Hook chosen. Your pick is recorded as a preference.</span><button onClick="{{{{openHook}}}}" style="{LINKBTN}; font-size: 13.5px">Change the hook</button></div></sc-if>
</div>
</section>
<section style="{CARD}; padding: 16px; display: flex; justify-content: space-between; align-items: center; gap: 12px">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 15px; font-weight: 600">Capture</span><span style="{SUB}">{{{{captureCount}}}} captures waiting to become posts</span></div>
<button onClick="{{{{goCapture}}}}" style="{SECONDARY}">Open</button>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Queued</h2>
<div style="{CARD}; overflow: hidden">
<sc-for list="{{{{queue}}}}" as="q" hint-placeholder-count="4">
<div style="padding: 14px 16px; border-bottom: 1px solid var(--line2); display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 15px; font-weight: 500">{{{{q.title}}}}</span><span style="{SUB}">{{{{q.meta}}}}</span></div>
<sc-if value="{{{{q.showDraft}}}}" hint-placeholder-val="{{{{ true }}}}"><button onClick="{{{{q.draft}}}}" disabled="{{{{busy}}}}" style="flex-shrink: 0; min-height: 44px; padding: 0 16px; border-radius: 10px; border: 1px solid var(--ink); background: transparent; font-size: 14px; font-weight: 600; cursor: pointer; opacity: {{{{busyOpacity}}}}">Draft</button></sc-if>
<sc-if value="{{{{q.isDrafted}}}}" hint-placeholder-val="{{{{ false }}}}"><span style="{CHIP_BLUE}; flex-shrink: 0">Drafted · next in line</span></sc-if>
</div>
<sc-if value="{{{{q.isDrafting}}}}" hint-placeholder-val="{{{{ false }}}}"><dc-import name="Thinking" cmd="draft" fail="{{{{q.fail}}}}" fail-at="1" on-retry="{{{{q.retry}}}}" on-cancel="{{{{q.cancel}}}}" on-done="{{{{q.onDone}}}}" hint-size="100%,150px"></dc-import></sc-if>
<sc-if value="{{{{q.factNote}}}}" hint-placeholder-val="{{{{ false }}}}"><div role="status" style="{AMBER}">The fact-check couldn't confirm one claim, so it's left out of the cards. Its row in CLAIMS.md says why.</div></sc-if>
</div>
</sc-for>
</div>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Posted</h2>
<div style="{CARD}; overflow: hidden">
<sc-for list="{{{{postedList}}}}" as="p" hint-placeholder-count="11">
<div style="padding: 12px 16px; border-bottom: 1px solid var(--line2); display: flex; flex-direction: column; gap: 2px">
<div style="display: flex; justify-content: space-between; gap: 12px"><span style="font-size: 14.5px; font-weight: 500">{{{{p.title}}}}</span><span style="font-family: {MONO}; font-size: 12px; color: var(--muted); white-space: nowrap">{{{{p.whenShort}}}}</span></div>
<span style="{SUB}">{{{{p.meta}}}}</span>
</div>
</sc-for>
</div>
</section>
</div>
</sc-if>
'''

CAPTURE = f'''<sc-if value="{{{{isCapture}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 18px">
<button onClick="{{{{goBackFromCapture}}}}" style="{LINKBTN}; align-self: flex-start">‹ Back</button>
<div style="display: flex; flex-direction: column; gap: 8px"><h1 style="{H1}">Capture</h1><div style="font-size: 14px; color: var(--text2); line-height: 1.45">Keep what happens while you build. Your own screenshots, recordings and verdicts are what make a post first-hand.</div></div>
<section style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 12px">
<div role="radiogroup" aria-label="Kind of capture" style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<sc-for list="{{{{capKinds}}}}" as="ck" hint-placeholder-count="4"><button role="radio" aria-checked="{{{{ck.on}}}}" onClick="{{{{ck.pick}}}}" style="min-height: 48px; border-radius: 12px; border: 1px solid {{{{ck.border}}}}; background: {{{{ck.bg}}}}; font-size: 14px; font-weight: {{{{ck.weight}}}}; cursor: pointer">{{{{ck.label}}}}</button></sc-for>
</div>
<label for="te-cap" style="font-size: 13px; color: var(--text2)">What happened, in one line</label>
<textarea id="te-cap" rows="3" value="{{{{capText}}}}" onChange="{{{{setCapText}}}}" placeholder="Codex and Claude disagreed on the fix; Grok broke the tie" style="border-radius: 12px; border: 1px solid var(--line); padding: 10px 12px; font-family: {SANS}; font-size: 15px; background: var(--raised); color: var(--ink); resize: vertical"></textarea>
<button onClick="{{{{saveCapture}}}}" style="{PRIMARY}; min-height: 48px; font-size: 15px">Save capture</button>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Captured</h2>
<sc-for list="{{{{captures}}}}" as="cp" hint-placeholder-count="2">
<div style="{CARD}; padding: 14px 16px; display: flex; flex-direction: column; gap: 8px">
<div style="display: flex; justify-content: space-between; gap: 10px; font-family: {MONO}; font-size: 12px; color: var(--muted)"><span>{{{{cp.kind}}}}</span><span>{{{{cp.when}}}}</span></div>
<div style="font-size: 15px; line-height: 1.4">{{{{cp.text}}}}</div>
<sc-if value="{{{{cp.canTurn}}}}" hint-placeholder-val="{{{{ true }}}}"><button onClick="{{{{cp.turn}}}}" style="{SECONDARY}; align-self: flex-start">Turn into a post</button></sc-if>
<sc-if value="{{{{cp.turned}}}}" hint-placeholder-val="{{{{ false }}}}"><span style="{CHIP_BLUE}; align-self: flex-start">Queued as a {{{{cp.format}}}}</span></sc-if>
</div>
</sc-for>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">From your readers</h2>
<div style="{CARD}; padding: 14px 16px; display: flex; flex-direction: column; gap: 8px">
<div style="font-size: 15px; line-height: 1.4">A reader asked how Grok compares with Codex and Claude Code on big projects and tricky debugging.</div>
<sc-if value="{{{{readerCanTurn}}}}" hint-placeholder-val="{{{{ true }}}}"><button onClick="{{{{turnReader}}}}" style="{SECONDARY}; align-self: flex-start">Turn into a tool verdict</button></sc-if>
<sc-if value="{{{{readerTurned}}}}" hint-placeholder-val="{{{{ false }}}}"><span style="{CHIP_BLUE}; align-self: flex-start">Queued as a tool verdict</span></sc-if>
</div>
</section>
</div>
</sc-if>
'''

WAITCARD = f'''<sc-for list="{{{{waiting}}}}" as="wt" hint-placeholder-count="3">
<sc-if value="{{{{wt.closed}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="{CARD}; padding: 10px 16px; display: flex; justify-content: space-between; align-items: center; gap: 10px"><span style="font-size: 13.5px; color: var(--text2)"><span style="font-family: {MONO}; font-size: 12px">{{{{wt.handle}}}}</span> · {{{{wt.status}}}}</span><button onClick="{{{{wt.undo}}}}" style="{LINKBTN}; font-size: 13.5px">Undo</button></div></sc-if>
<sc-if value="{{{{wt.open}}}}" hint-placeholder-val="{{{{ true }}}}">
<article style="{CARD}; border-color: var(--amber-line); padding: 16px; display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; gap: 10px; font-family: {MONO}; font-size: 12px; color: var(--amber)"><span>{{{{wt.handle}}}} · {{{{wt.where}}}}</span><span style="white-space: nowrap; flex-shrink: 0">{{{{wt.age}}}}</span></div>
<div style="font-size: 15px; line-height: 1.45">{{{{wt.said}}}}</div>
<div style="background: var(--paper); border-radius: 12px; padding: 12px; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em">A point you could make</span><span style="font-size: 14px; line-height: 1.45">{{{{wt.point}}}}</span></div>
<div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center">
<a href="https://x.com" target="_blank" rel="noopener" style="min-height: 44px; display: flex; align-items: center; font-size: 14px; font-weight: 600; margin-right: 6px">Answer on X ↗</a>
<button onClick="{{{{wt.answered}}}}" style="min-height: 44px; padding: 0 12px; border-radius: 10px; border: 1px solid var(--line); background: var(--raised); font-size: 13.5px; font-weight: 600; cursor: pointer">Answered</button>
<button onClick="{{{{wt.skip}}}}" style="min-height: 44px; padding: 0 12px; border-radius: 10px; border: 1px solid var(--line); background: var(--raised); font-size: 13.5px; font-weight: 600; cursor: pointer">Not answering</button>
</div>
{ASK('wt.ask', 'Ask Cortex about this reply')}
</article>
</sc-if>
</sc-for>'''

REPLIES = f'''<sc-if value="{{{{isReplies}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 18px">
{header('Replies')}
<div style="font-size: 14px; color: var(--text2); line-height: 1.45">You write every reply. Nothing here is meant to be pasted. Names in this mock are placeholders.</div>
<section style="display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="{H2}; font-size: 17px">Waiting for you</h2><span style="{SUB}">replies to your posts</span></div>
{WAITCARD}
<sc-if value="{{{{noWaiting}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="{NOTE}">Nobody's waiting. You're all caught up.</div></sc-if>
<div style="border: 1px dashed var(--dash); border-radius: 14px; padding: 12px 14px; font-size: 13.5px; color: var(--text2); line-height: 1.45">Plus 37 greetings and connect requests this week. A like is enough; answering each one looks like spam to X. <span style="{CHIP_NEUTRAL}">example</span></div>
</section>
<section style="display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="{H2}; font-size: 17px">Builders</h2><span style="{SUB}">people you've had a real exchange with</span></div>
<div style="{CARD}; padding: 14px 16px; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 26px; font-weight: 600">2</span><span style="font-size: 13.5px; color: var(--text2); line-height: 1.45">mutuals on topic. When you and a builder follow each other, X ranks your posts higher for them: it weighs their chance of replying at 20 instead of 5 (A10).</span><span style="{CHIP_NEUTRAL}; align-self: flex-start">example</span></div>
<div style="{CARD}; overflow: hidden">
<sc-for list="{{{{builders}}}}" as="b" hint-placeholder-count="4">
<div style="padding: 12px 16px; border-bottom: 1px solid var(--line2); display: flex; flex-direction: column; gap: 4px">
<div style="display: flex; justify-content: space-between; gap: 10px"><span style="font-family: {MONO}; font-size: 13px; font-weight: 500">{{{{b.handle}}}}</span><span style="{SUB}">{{{{b.last}}}}</span></div>
<span style="{SUB}">{{{{b.tags}}}}</span>
</div>
</sc-for>
</div>
</section>
<section style="display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="{H2}; font-size: 17px">Worth joining</h2><span style="{SUB}">verified builders first</span></div>
<sc-for list="{{{{replies}}}}" as="r" hint-placeholder-count="3">
<article style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; gap: 10px; font-family: {MONO}; font-size: 12px; color: var(--muted)"><span>{{{{r.handle}}}}</span><span>found {{{{r.found}}}} · {{{{r.kind}}}}</span></div>
<div style="font-size: 15px; line-height: 1.4">{{{{r.what}}}}</div>
<div style="background: var(--paper); border-radius: 12px; padding: 12px; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em">A point you could make</span><span style="font-size: 14px; line-height: 1.45">{{{{r.point}}}}</span></div>
<a href="https://x.com" target="_blank" rel="noopener" style="align-self: flex-start; min-height: 44px; display: flex; align-items: center; font-size: 14px; font-weight: 500">Open on X ↗</a>
</article>
</sc-for>
</section>
<div style="{NOTE}">Your busiest 24 hours (Wed to Thu) had 68 replies, and on 22 Sep one line went out 12 times. X's reply scorer sees how many you sent in 24 hours (A12), and repeated lines can be flagged as spam (A13). Keep it to what you'd write by hand.</div>
</div>
</sc-if>
'''

def table(cols, lst, cells):
    th = ''.join(f'<th scope="col" style="padding: 6px 4px; font-weight: 500; text-align: {a}">{c}</th>' for c, a in cols)
    td = ''.join(f'<td style="padding: 6px 4px; text-align: {a}; font-variant-numeric: tabular-nums">{{{{{c}}}}}</td>' for c, a in cells)
    return (f'<table style="width: 100%; border-collapse: collapse; font-size: 13px"><thead><tr style="color: var(--muted)">{th}</tr></thead>'
            f'<tbody><sc-for list="{{{{{lst}}}}}" as="row" hint-placeholder-count="3"><tr style="border-top: 1px solid var(--line2)">{td}</tr></sc-for></tbody></table>')

def barlist(title, sub, lst, table_html):
    return f'''<section style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 10px"><h2 style="{H2}">{title}</h2><span style="{SUB}">{sub}</span></div>
<sc-if value="{{{{showChart}}}}" hint-placeholder-val="{{{{ true }}}}">
<sc-for list="{{{{{lst}}}}}" as="b" hint-placeholder-count="4">
<div style="display: grid; grid-template-columns: 112px minmax(0, 1fr); gap: 8px; align-items: center; min-height: 40px">
<span style="font-size: 13px; line-height: 1.3">{{{{b.t}}}}</span>
<span style="display: flex; align-items: center; gap: 6px; min-width: 0; border-left: 1px solid var(--axis); padding: 4px 0"><span style="height: 12px; width: {{{{b.pct}}}}; min-width: 2px; border-radius: 0 4px 4px 0; background: var(--chart-on); flex-shrink: 0"></span><span style="font-size: 12.5px; white-space: nowrap">{{{{b.label}}}}</span></span>
</div>
</sc-for>
</sc-if>
<sc-if value="{{{{showTable}}}}" hint-placeholder-val="{{{{ false }}}}">{table_html}</sc-if>
</section>'''

RESULTS = f'''<sc-if value="{{{{isResults}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 20px">
<div style="display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px"><div style="{EYEBROW}">Results · week of 18–24 Sep</div>{AV}</div>
<h1 style="margin: 0; font-family: {SERIF}; font-weight: 400; font-size: 22px; line-height: 1.2"><span style="display: block">Every profile visit from an unboosted post came from one networking post.</span><span style="display: block; margin-top: 6px; font-family: {SANS}; font-size: 15px; line-height: 1.4; color: var(--text2)">115 replies brought 14,220 views and 4 follows.</span></h1>
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
<div role="tablist" aria-label="Results" onKeyDown="{{{{rtKey}}}}" style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); background: var(--seg); border-radius: 12px; padding: 3px; gap: 3px">
<button role="tab" aria-selected="{{{{rtGrowth}}}}" aria-controls="te-rt-panel" tabindex="{{{{rtGrowthTi}}}}" onClick="{{{{rtGoGrowth}}}}" style="min-height: 44px; border: {{{{rtGrowthBorder}}}}; border-radius: 9px; background: {{{{rtGrowthBg}}}}; font-size: 14px; font-weight: {{{{rtGrowthWeight}}}}; cursor: pointer">Growth</button>
<button role="tab" aria-selected="{{{{rtPosts}}}}" aria-controls="te-rt-panel" tabindex="{{{{rtPostsTi}}}}" onClick="{{{{rtGoPosts}}}}" style="min-height: 44px; border: {{{{rtPostsBorder}}}}; border-radius: 9px; background: {{{{rtPostsBg}}}}; font-size: 14px; font-weight: {{{{rtPostsWeight}}}}; cursor: pointer">Posts</button>
<button role="tab" aria-selected="{{{{rtReplies}}}}" aria-controls="te-rt-panel" tabindex="{{{{rtRepliesTi}}}}" onClick="{{{{rtGoReplies}}}}" style="min-height: 44px; border: {{{{rtRepliesBorder}}}}; border-radius: 9px; background: {{{{rtRepliesBg}}}}; font-size: 14px; font-weight: {{{{rtRepliesWeight}}}}; cursor: pointer">Replies</button>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; gap: 10px">
<div role="radiogroup" aria-label="Date range" style="display: flex; gap: 6px">
<button role="radio" aria-checked="true" style="min-height: 44px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--ink); background: var(--btn); color: var(--on-btn); font-size: 13px; font-weight: 600; cursor: pointer">7 days</button>
<button role="radio" aria-checked="false" disabled="{{{{ true }}}}" title="Data starts 20 Sep" style="min-height: 44px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--line); background: transparent; color: var(--faint); font-size: 13px">30 days</button>
<button role="radio" aria-checked="false" disabled="{{{{ true }}}}" title="Data starts 20 Sep" style="min-height: 44px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--line); background: transparent; color: var(--faint); font-size: 13px">90 days</button>
</div>
<button onClick="{{{{toggleTable}}}}" style="min-height: 44px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--line); background: var(--card); font-size: 13px; font-weight: 600; cursor: pointer">{{{{tableLabel}}}}</button>
</div>
<div style="{SUB}">Data starts 20 Sep, so 30 and 90 days open up later.</div>
</div>
<div role="tabpanel" id="te-rt-panel" aria-label="{{{{rtPanelLabel}}}}" style="display: flex; flex-direction: column; gap: 20px">
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px">
<sc-for list="{{{{kpis}}}}" as="k" hint-placeholder-count="4">
<div style="{CARD}; border-radius: 14px; padding: 12px 14px; display: flex; flex-direction: column; gap: 2px"><span style="font-size: 12px; color: var(--muted)">{{{{k.label}}}}</span><span style="font-size: 24px; font-weight: 600; line-height: 1.15">{{{{k.value}}}}</span><span style="font-size: 12px; color: var(--muted); line-height: 1.35">{{{{k.sub}}}}</span></div>
</sc-for>
</div>

<sc-if value="{{{{rtGrowth}}}}" hint-placeholder-val="{{{{ true }}}}">
<div style="display: flex; flex-direction: column; gap: 16px">
{barlist('Where this week’s 19 follows came from', 'from X’s export', 'followSrc', table([('Source','left'),('Follows','right')], 'followSrc', [('row.t','left'),('row.n','right')]))}
<section style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="{H2}">Followers over time</h2><span style="{SUB}">daily count</span></div>
<sc-if value="{{{{showChart}}}}" hint-placeholder-val="{{{{ true }}}}">
<div style="display: flex; align-items: flex-end; gap: 10px; height: 110px; border-bottom: 1px solid var(--axis); padding-left: 8px"><div style="display: flex; flex-direction: column; align-items: center; gap: 4px"><span style="font-size: 12px; font-weight: 600">36</span><div style="width: 22px; height: 80px; background: var(--chart-on); border-radius: 4px 4px 0 0"></div></div><span style="{SUB}; padding-bottom: 8px">One daily count so far. A column is added each day from today.</span></div>
<div style="font-family: {MONO}; font-size: 12px; color: var(--muted)">Thu 24 Sep</div>
</sc-if>
<sc-if value="{{{{showTable}}}}" hint-placeholder-val="{{{{ false }}}}">{table([('Day','left'),('Followers','right')], 'followerDays', [('row.d','left'),('row.n','right')])}</sc-if>
</section>
</div>
</sc-if>

<sc-if value="{{{{rtPosts}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 16px">
<section style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 10px"><h2 style="{H2}">On topic, last 15 posts</h2><span style="{SUB}">target 12</span></div>
<sc-if value="{{{{showTable}}}}" hint-placeholder-val="{{{{ false }}}}">{table([('Post','left'),('On topic','left')], 'shareRows', [('row.n','left'),('row.v','left')])}</sc-if>
<sc-if value="{{{{showChart}}}}" hint-placeholder-val="{{{{ true }}}}">
<div aria-label="{{{{shareLabel}}}}" role="img" style="display: grid; grid-template-columns: repeat(15, minmax(0, 1fr)); gap: 4px">
<sc-for list="{{{{shareSlots}}}}" as="sl" hint-placeholder-count="15"><div style="height: 22px; border-radius: 4px; background: {{{{sl.bg}}}}; border: {{{{sl.border}}}}; box-sizing: border-box"></div></sc-for>
</div>
<div style="display: flex; gap: 14px; flex-wrap: wrap; font-size: 12.5px; color: var(--text2)"><span style="display: flex; align-items: center; gap: 6px"><span style="width: 12px; height: 12px; border-radius: 3px; background: var(--chart-on)"></span>On topic (5)</span><span style="display: flex; align-items: center; gap: 6px"><span style="width: 12px; height: 12px; border-radius: 3px; border: 1.5px solid var(--axis); box-sizing: border-box"></span>Off topic (6)</span><span style="display: flex; align-items: center; gap: 6px"><span style="width: 12px; height: 12px; border-radius: 3px; border: 1.5px dashed var(--dash); box-sizing: border-box"></span>Still to post (4)</span></div>
</sc-if>
<div style="font-size: 13px; color: var(--text2); line-height: 1.45">On topic: posts that fit your account's promise, tech that's useful to builders. The target is yours: X's code tracks topic share over your last 15 posts (A8), and a penalty isn't proven.</div>
</section>
<section style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 6px">
<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 10px"><h2 style="{H2}">Posts, by what they brought</h2><span style="{SUB}">follows · visits · views</span></div>
<sc-if value="{{{{showTable}}}}" hint-placeholder-val="{{{{ false }}}}">{table([('Post','left'),('Follows','right'),('Visits','right'),('Views','right'),('On topic','left')], 'postRows', [('row.t','left'),('row.f','right'),('row.v','right'),('row.w','right'),('row.topic','left')])}</sc-if>
<sc-if value="{{{{showChart}}}}" hint-placeholder-val="{{{{ true }}}}">
<sc-for list="{{{{rposts}}}}" as="rp" hint-placeholder-count="11">
<div style="display: flex; flex-direction: column; padding: 8px 0; border-top: 1px solid var(--line2)">
<div style="display: flex; justify-content: space-between; gap: 10px"><span style="font-size: 14px; font-weight: 500; line-height: 1.3">{{{{rp.title}}}}</span><span style="font-family: {MONO}; font-size: 12px; color: var(--muted); white-space: nowrap">{{{{rp.when}}}}</span></div>
<span style="font-size: 13px; color: var(--text2)">{{{{rp.label}}}}</span>
</div>
</sc-for>
</sc-if>
<div style="{SUB}; padding-top: 6px">Charts come once there's a month of data. The boosted post never counts as a win.</div>
</section>
</div>
</sc-if>

<sc-if value="{{{{rtReplies}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 16px">
{barlist('Replies that led somewhere', 'profile visits · follows', 'rtopics', table([('Topic','left'),('Visits','right'),('Follows','right'),('Views','right')], 'rtopics', [('row.t','left'),('row.visits','right'),('row.follows','right'),('row.views','right')]))}
<div style="{NOTE}">Reply views (14,220) don't count toward X's rewards; only your own posts do. Replies earn their keep through visits, follows and mutuals.</div>
</div>
</sc-if>
</div>
{ASK('askAboutResults', 'Ask Cortex about these results')}
<sc-if value="{{{{showReviewButton}}}}" hint-placeholder-val="{{{{ true }}}}"><button onClick="{{{{writeReview}}}}" disabled="{{{{busy}}}}" style="min-height: 50px; border-radius: 12px; border: 1px solid var(--ink); background: transparent; font-size: 15px; font-weight: 600; cursor: pointer; opacity: {{{{busyOpacity}}}}">Write this week's review</button></sc-if>
<sc-if value="{{{{thinkingResults}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="{CARD}; padding: 16px 18px"><dc-import name="Thinking" cmd="results" ask="{{{{reviewAsk}}}}" ans-a="Use 24 Sep’s: 27 and 337" ans-b="Leave them out this week" on-done="{{{{doneReview}}}}" hint-size="100%,140px"></dc-import></div></sc-if>
<sc-if value="{{{{reviewWritten}}}}" hint-placeholder-val="{{{{ false }}}}"><div role="status" style="{CARD}; padding: 14px 18px; display: flex; flex-direction: column; gap: 4px"><span style="font-weight: 600; font-size: 14px">Review written</span><span style="{SUB}">The next one is due Thu 1 Oct, after your analytics export.</span></div></sc-if>
</div>
</sc-if>
'''

CORTEX = f'''<sc-if value="{{{{isCortex}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="display: flex; flex-direction: column; gap: 22px; padding-bottom: 84px">
<div style="display: flex; flex-direction: column; gap: 8px">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px"><div style="{EYEBROW}">What your engine knows</div>{AV}</div>
<h1 style="{H1}; font-size: 40px">Cortex</h1>
<div style="font-size: 14px; color: var(--text2); line-height: 1.45">Set by you for now. Once experiments finish, it proposes changes and you decide.</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px">
<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px">
<sc-for list="{{{{pipeline}}}}" as="pp" hint-placeholder-count="4"><div style="{CARD}; border-radius: 12px; padding: 10px 4px; display: flex; flex-direction: column; gap: 2px; align-items: center"><span style="font-family: {MONO}; font-size: 20px; font-weight: 500">{{{{pp.n}}}}</span><span style="font-size: 12px; color: var(--muted); text-align: center">{{{{pp.label}}}}</span></div></sc-for>
</div>
<div style="{SUB}; text-align: center">Questions become experiments. Experiments become lessons. You apply a lesson to change a weight.</div>
</div>
<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Lessons</h2>
<div style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 15px; font-weight: 600">No lessons yet.</span><span style="font-size: 13.5px; color: var(--text2); line-height: 1.45">The first experiment can start around 8 Oct, once two weeks of organic numbers are in.</span></div>
<div style="border: 1.5px dashed var(--dash); border-radius: 18px; padding: 16px; display: flex; flex-direction: column; gap: 12px; background: var(--raised)">
<span style="font-family: {MONO}; font-size: 12px; letter-spacing: 0.08em; color: var(--muted)">EXAMPLE OF A LESSON · NOT REAL DATA</span>
<span style="font-size: 16px; font-weight: 600; line-height: 1.35">Three-card threads bring more people to your profile than long ones.</span>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px">
<div style="display: flex; flex-direction: column; gap: 4px"><span style="font-family: {MONO}; font-size: 30px; font-weight: 500">24</span><div style="height: 6px; border-radius: 3px; background: var(--chart-on); width: 100%"></div><span style="font-size: 12.5px; color: var(--text2)">visits per 1,000 views, 3-card threads</span></div>
<div style="display: flex; flex-direction: column; gap: 4px"><span style="font-family: {MONO}; font-size: 30px; font-weight: 500">11</span><div style="height: 6px; border-radius: 3px; background: var(--axis); width: 46%"></div><span style="font-size: 12.5px; color: var(--text2)">visits per 1,000 views, 7-card threads</span></div>
</div>
<div style="font-family: {MONO}; font-size: 12px; color: var(--text2); line-height: 1.6">6 posts each · 20 Sep – 12 Oct<br>Bar set before the test: 1.5×. Result: 2.2×.<br>Proven 14 Oct</div>
<div style="display: flex; gap: 10px; flex-wrap: wrap"><button disabled="{{{{ true }}}}" style="{SECONDARY}; opacity: 0.6">Apply to Post length</button><button disabled="{{{{ true }}}}" style="{SECONDARY}; opacity: 0.6">Undo</button></div>
</div>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="{H2}">Weights</h2><span style="{SUB}">the ones that matter most</span></div>
<div style="{CARD}; padding: 2px 16px">
<sc-for list="{{{{weights}}}}" as="w" hint-placeholder-count="5">
<div style="padding: 12px 0; border-bottom: 1px solid var(--line2); display: flex; flex-direction: column; gap: 3px">
<div style="display: flex; justify-content: space-between; gap: 12px"><span style="font-size: 12.5px; color: var(--muted)">{{{{w.name}}}}</span><span style="font-family: {MONO}; font-size: 12px; color: var(--muted); font-style: {{{{w.style}}}}; text-align: right">{{{{w.src}}}}</span></div>
<span style="font-size: 14.5px; font-weight: 500; line-height: 1.35">{{{{w.value}}}}</span>
</div>
</sc-for>
</div>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<div style="display: flex; justify-content: space-between; align-items: baseline"><h2 style="{H2}">Guardrails</h2><span style="{SUB}">never changed by Cortex or the loop</span></div>
<div style="{CARD}; padding: 14px 16px; display: flex; flex-direction: column; gap: 10px">
<sc-for list="{{{{guardrails}}}}" as="g" hint-placeholder-count="6"><div style="display: flex; gap: 10px; align-items: flex-start; font-size: 14px; line-height: 1.4">{LOCK}<span>{{{{g.text}}}}</span></div></sc-for>
</div>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Experiments</h2>
<div style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 12px">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px"><span style="font-size: 15px; font-weight: 600">None running</span><span style="{CHIP_NEUTRAL}">Paused until about 8 Oct</span></div>
<span style="font-size: 13.5px; color: var(--text2); line-height: 1.45">Experiments need two weeks of organic numbers first. The daily read started on 24 Sep.</span>
<div style="border-top: 1px solid var(--line2); padding-top: 12px; display: flex; flex-direction: column; gap: 10px">
<span style="{SUB}">Up next, in order</span>
<sc-for list="{{{{nextExperiments}}}}" as="x" hint-placeholder-count="6">
<div style="display: flex; flex-direction: column; gap: 6px">
<div style="display: flex; gap: 10px; font-size: 14px; line-height: 1.4"><span style="font-family: {MONO}; font-size: 12px; color: var(--muted); width: 14px; flex-shrink: 0; padding-top: 2px">{{{{x.n}}}}</span><span>{{{{x.text}}}}</span></div>
<sc-if value="{{{{x.first}}}}" hint-placeholder-val="{{{{ false }}}}"><button onClick="{{{{queueFirst}}}}" disabled="{{{{queuedExp}}}}" style="{SECONDARY}; align-self: flex-start; margin-left: 24px; min-height: 44px; font-size: 14px">{{{{queueLabel}}}}</button></sc-if>
</div>
</sc-for>
</div>
</div>
</section>
<section style="display: flex; flex-direction: column; gap: 10px">
<h2 style="{H2}">Open questions</h2>
<sc-for list="{{{{questions}}}}" as="oq" hint-placeholder-count="2"><div style="{CARD}; padding: 16px; display: flex; flex-direction: column; gap: 6px"><span style="font-size: 15px; font-weight: 600; line-height: 1.35">{{{{oq.t}}}}</span><span style="font-size: 13.5px; color: var(--text2); line-height: 1.45">{{{{oq.why}}}}</span></div></sc-for>
</section>
</div>
</sc-if>
'''

def tab(key, label, icon, extra=''):
    return (f'<button onClick="{{{{go{key}}}}}" aria-current="{{{{tab{key}Current}}}}" aria-label="{{{{tab{key}Label}}}}" style="border: none; background: none; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; cursor: pointer; color: {{{{tab{key}}}}}">'
            f'<span style="position: relative; display: flex">{icon}{extra}</span><span style="font-size: 12px; font-weight: {{{{tab{key}Weight}}}}">{label}</span></button>')

ICON = lambda d: f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
BADGE = f'<sc-if value="{{{{hasWaiting}}}}" hint-placeholder-val="{{{{ true }}}}"><span aria-hidden="true" style="position: absolute; top: -5px; right: -10px; min-width: 18px; height: 18px; border-radius: 9px; background: var(--amber-fill); color: var(--on-amber); font-family: {MONO}; font-size: 12px; display: flex; align-items: center; justify-content: center; padding: 0 4px; box-sizing: border-box">{{{{waitingCount}}}}</span></sc-if>'

NAV = ('<nav aria-label="Sections" inert="{{navInert}}" style="height: 80px; flex-shrink: 0; border-top: 1px solid var(--line); background: var(--raised); display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); padding-bottom: 14px; box-sizing: border-box">\n'
       + tab('Today', 'Today', ICON('<circle cx="12" cy="12" r="4"></circle><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4"></path>')) + '\n'
       + tab('Posts', 'Posts', ICON('<rect x="4" y="4" width="16" height="6" rx="1.5"></rect><rect x="4" y="14" width="16" height="6" rx="1.5"></rect>')) + '\n'
       + tab('Replies', 'Replies', ICON('<path d="M20 12a7 7 0 0 1-10.3 6.2L5 19.5l1.3-4.2A7 7 0 1 1 20 12z"></path>'), BADGE) + '\n'
       + tab('Results', 'Results', ICON('<path d="M5 20V11M12 20V5M19 20v-6"></path>')) + '\n'
       + tab('Cortex', 'Cortex', ICON('<circle cx="6" cy="7" r="2.2"></circle><circle cx="18" cy="6" r="2.2"></circle><circle cx="12" cy="17.5" r="2.2"></circle><path d="M8.2 6.8l7.6-.6M7.2 9l3.7 6.5M16.9 8l-3.8 7.5"></path>')) + '\n</nav>')

def sheet(show, close, label, inner, height='max-height: 90%', bg='background: var(--raised)', extra_style=''):
    return f'''<sc-if value="{{{{{show}}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="position: absolute; left: 0; top: 0; right: 0; bottom: 0; display: flex; flex-direction: column; justify-content: flex-end">
<div onClick="{{{{{close}}}}}" aria-hidden="true" style="position: absolute; left: 0; top: 0; right: 0; bottom: 0; background: var(--scrim); cursor: pointer"></div>
<div role="dialog" aria-modal="true" aria-label="{label}" onKeyDown="{{{{sheetKey}}}}" class="te-sheet-in" style="position: relative; {height}; overflow-y: auto; border-radius: 26px 26px 0 0; {bg}; display: flex; flex-direction: column; {extra_style}">
{inner}
</div>
</div>
</sc-if>'''

HANDLE = '<div aria-hidden="true" style="align-self: center; width: 40px; height: 4px; border-radius: 2px; background: var(--line)"></div>'

SOURCE_INNER = f'''<div style="padding: 12px 22px 30px; display: flex; flex-direction: column; gap: 14px; font-family: {MONO}; font-size: 13px; line-height: 1.5">
{HANDLE}
<div style="display: flex; justify-content: space-between; font-size: 12px; letter-spacing: 0.08em; color: var(--muted)"><span>SOURCE · SWAP {{{{src.n}}}} OF 3</span><span>CHECKED 24 SEP</span></div>
<h2 style="margin: 0; font-family: {SANS}; font-size: 18px; font-weight: 600">{{{{src.paid}}}} → {{{{src.free}}}}</h2>
<div style="border-top: 1px dashed var(--dash)"></div>
<div style="display: flex; flex-direction: column; gap: 4px"><span style="font-size: 12px; letter-spacing: 0.08em; color: var(--muted)">PAID SIDE</span><span>{{{{src.paidFact}}}}</span><span style="color: var(--blue)">{{{{src.paidSrc}}}}</span></div>
<div style="border-top: 1px dashed var(--dash)"></div>
<div style="display: flex; flex-direction: column; gap: 4px"><span style="font-size: 12px; letter-spacing: 0.08em; color: var(--muted)">FREE SIDE · THE VENDOR'S OWN WORDS</span><span>{{{{src.quote}}}}</span><span style="color: var(--blue)">{{{{src.freeSrc}}}}</span></div>
<div style="border-top: 1px dashed var(--dash)"></div>
<div style="display: flex; flex-direction: column; gap: 4px"><span style="font-size: 12px; letter-spacing: 0.08em; color: var(--muted)">IF SOMEONE PUSHES BACK</span><span>{{{{src.limit}}}}</span></div>
<button onClick="{{{{closeSource}}}}" style="{SECONDARY}; font-family: {SANS}">Done</button>
</div>'''
SOURCE_SHEET = sheet('hasSource', 'closeSource', 'Source', SOURCE_INNER)

EDITOR_INNER = f'''<div style="padding: 12px 20px 28px; display: flex; flex-direction: column; gap: 14px">
{HANDLE}
<div style="display: flex; justify-content: space-between; align-items: center"><h2 style="{H2}; font-size: 17px">Change something</h2><button onClick="{{{{cancelEdit}}}}" style="{LINKBTN}">Cancel</button></div>
<sc-if value="{{{{draftPending}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="{NOTE}; display: flex; justify-content: space-between; align-items: center; gap: 10px"><span>Your unsaved changes are still here.</span><button onClick="{{{{discardDraft}}}}" style="{LINKBTN}; font-size: 13.5px">Discard them</button></div></sc-if>
<sc-if value="{{{{editClearsApproval}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="{AMBER}">Saving clears the approval. You'll read and approve again.</div></sc-if>
<label for="te-card" style="font-size: 13px; color: var(--text2)">Card 1</label>
<textarea id="te-card" rows="12" value="{{{{draftText}}}}" onChange="{{{{setDraftText}}}}" style="border-radius: 12px; border: 1px solid var(--line); padding: 10px 12px; font-family: {SANS}; font-size: 15px; line-height: 1.4; background: var(--card); color: var(--ink); resize: vertical"></textarea>
<div style="font-family: {MONO}; font-size: 12px; color: {{{{draftCountColor}}}}">{{{{draftCount}}}} characters as X counts · your limit 600</div>
<div style="{NOTE}">This format has a fixed header, so there's no hook to choose. Other formats offer two or three hooks here.</div>
<label for="te-take" style="font-size: 13px; color: var(--text2)">Your take, in one line (optional, added under the list)</label>
<input id="te-take" value="{{{{takeText}}}}" onChange="{{{{setTakeText}}}}" placeholder="I moved my own collections to Bruno last month" style="min-height: 46px; border-radius: 12px; border: 1px solid var(--line); padding: 0 12px; font-family: {SANS}; font-size: 15px; background: var(--card); color: var(--ink)">
<div style="{SUB}">Every claim still goes through the fact-check, and the final check still applies.</div>
<button onClick="{{{{saveEdit}}}}" style="{PRIMARY}">Save changes</button>
</div>'''
EDITOR_SHEET = sheet('editorOpen', 'closeEditor', 'Change something', EDITOR_INNER)

CHAT_INNER = f'''<div style="padding: 10px 18px 8px; display: flex; flex-direction: column; gap: 10px">
{HANDLE}
<div style="display: flex; align-items: center; gap: 10px">{orb(28)}<div style="display: flex; flex-direction: column; flex-grow: 1"><h2 style="{H2}; font-size: 16px">Cortex</h2><span style="font-family: {MONO}; font-size: 12px; color: var(--muted)">Claude</span></div><button onClick="{{{{closeChat}}}}" style="{LINKBTN}; font-size: 15px; font-weight: 600">Done</button></div>
</div>
<div style="flex-grow: 1; overflow-y: auto; display: flex; flex-direction: column-reverse; padding: 4px 18px 8px">
<div role="log" aria-live="polite" aria-label="Conversation" style="display: flex; flex-direction: column; gap: 14px; --shimmer-hi: var(--shimmer-hi-sheet)">
<sc-for list="{{{{chat}}}}" as="m" hint-placeholder-count="1">
<div style="display: flex; flex-direction: column; gap: 8px">
<sc-if value="{{{{m.isUser}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="align-self: flex-end; max-width: 82%; background: var(--btn); color: var(--on-btn); border-radius: 18px 18px 4px 18px; padding: 10px 14px; font-size: 15px; line-height: 1.4">{{{{m.text}}}}</div></sc-if>
<sc-if value="{{{{m.isBot}}}}" hint-placeholder-val="{{{{ true }}}}"><div style="display: flex; gap: 10px; align-items: flex-start">{orb(20)}<div style="font-size: 15px; line-height: 1.5">{{{{m.text}}}}</div></div></sc-if>
</div>
</sc-for>
<sc-if value="{{{{asking}}}}" hint-placeholder-val="{{{{ false }}}}"><dc-import name="Thinking" cmd="ask" on-done="{{{{doneAsk}}}}" hint-size="100%,110px"></dc-import></sc-if>
</div>
</div>
<div style="padding: 8px 18px 26px; display: flex; flex-direction: column; gap: 10px">
<sc-if value="{{{{hasContext}}}}" hint-placeholder-val="{{{{ false }}}}"><div style="align-self: flex-start; display: flex; align-items: center; gap: 4px; background: var(--card); border: 1px solid var(--chip-line); border-radius: 999px; padding: 0 0 0 12px; font-size: 13px; color: var(--text2)"><span>About: {{{{contextLabel}}}}</span><button onClick="{{{{clearContext}}}}" aria-label="Stop asking about this" style="width: 44px; height: 44px; border: none; background: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--muted)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg></button></div></sc-if>
<div style="display: flex; gap: 8px; flex-wrap: wrap; padding-bottom: 2px">
<sc-for list="{{{{suggestions}}}}" as="sg" hint-placeholder-count="3"><button onClick="{{{{sg.ask}}}}" disabled="{{{{asking}}}}" style="flex-shrink: 0; min-height: 44px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--chip-line); background: var(--chip-glass); font-size: 13.5px; cursor: pointer; text-align: left">{{{{sg.q}}}}</button></sc-for>
</div>
<div class="te-glow" style="border-radius: 999px"><div class="te-glass" style="min-height: 52px; border-radius: 999px; display: flex; align-items: center; gap: 10px; padding: 0 4px 0 16px">{orb(22)}<input aria-label="Ask Cortex" enterkeyhint="send" value="{{{{typed}}}}" onChange="{{{{setTyped}}}}" onKeyDown="{{{{typedKey}}}}" placeholder="Ask Cortex…" style="flex-grow: 1; min-width: 0; height: 44px; border: none; background: transparent; font-family: {SANS}; font-size: 16px; color: var(--ink)"><button onClick="{{{{sendTyped}}}}" aria-label="Send" style="flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; border: none; background: var(--btn); color: var(--on-btn); display: flex; align-items: center; justify-content: center; cursor: pointer"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"></path></svg></button></div></div>
<div style="{SUB}; text-align: center">Cortex answers and suggests. Every change is a button you press yourself.</div>
</div>'''
CHAT_SHEET = sheet('chatOpen', 'closeChat', 'Ask Cortex', CHAT_INNER, height='height: 88%', bg='background: linear-gradient(180deg, var(--sheet-top) 0%, var(--sheet-mid) 45%, var(--paper) 100%)', extra_style='overflow: hidden; box-shadow: 0 -10px 40px rgba(120, 60, 160, 0.18)')

THEME_TOGGLE = '''<button onClick="{{flipTheme}}" aria-label="{{flipLabel}}" title="{{flipLabel}}" style="flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--line); background: var(--card); color: var(--ink); display: flex; align-items: center; justify-content: center; cursor: pointer">
<sc-if value="{{showMoon}}" hint-placeholder-val="{{ true }}"><svg class="te-swap" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"></path></svg></sc-if>
<sc-if value="{{showSun}}" hint-placeholder-val="{{ false }}"><svg class="te-swap" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"></path></svg></sc-if>
</button>'''

def seg_radio(v, label):
    return f'<button role="radio" aria-checked="{{{{{v}}}}}" onClick="{{{{{v}Go}}}}" style="min-height: 44px; border: {{{{{v}Border}}}}; border-radius: 9px; background: {{{{{v}Bg}}}}; font-size: 13.5px; font-weight: {{{{{v}Weight}}}}; cursor: pointer">{label}</button>'

SETTINGS_INNER = f'''<div style="padding: 12px 20px 28px; display: flex; flex-direction: column; gap: 18px">
{HANDLE}
<div style="display: flex; align-items: center; gap: 12px">
<div aria-hidden="true" style="width: 52px; height: 52px; border-radius: 50%; background: var(--btn); color: var(--on-btn); display: flex; align-items: center; justify-content: center; font-family: {MONO}; font-size: 15px">EZ</div>
<div style="display: flex; flex-direction: column; flex-grow: 1"><h2 style="{H2}; font-size: 17px">Exit Zero Code</h2><span style="font-family: {MONO}; font-size: 12.5px; color: var(--muted)">@exitzerocode · 36 followers</span></div>
{THEME_TOGGLE}
<button onClick="{{{{closeSettings}}}}" style="{LINKBTN}; font-size: 15px; font-weight: 600; padding: 0 4px">Done</button>
</div>
<sc-for list="{{{{settingsGroups}}}}" as="sgp" hint-placeholder-count="3">
<section style="display: flex; flex-direction: column; gap: 8px">
<h3 style="margin: 0; font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted)">{{{{sgp.title}}}}</h3>
<div style="{CARD}; border-radius: 16px; padding: 0 14px">
<sc-for list="{{{{sgp.rows}}}}" as="row" hint-placeholder-count="3">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--line2)">
<div style="display: flex; align-items: center; gap: 10px"><span style="width: 8px; height: 8px; border-radius: 50%; background: {{{{row.dot}}}}; flex-shrink: 0"></span><div style="display: flex; flex-direction: column; gap: 1px"><span style="font-size: 14.5px">{{{{row.name}}}}</span><span style="{SUB}">{{{{row.sub}}}}</span></div></div>
<sc-if value="{{{{row.notToggle}}}}" hint-placeholder-val="{{{{ true }}}}"><span style="font-family: {MONO}; font-size: 12.5px; text-align: right">{{{{row.value}}}}</span></sc-if>
<sc-if value="{{{{row.isToggle}}}}" hint-placeholder-val="{{{{ false }}}}"><button role="switch" aria-checked="{{{{row.on}}}}" aria-label="{{{{row.name}}}}" onClick="{{{{row.flip}}}}" style="flex-shrink: 0; position: relative; width: 48px; height: 30px; border-radius: 15px; border: none; background: {{{{row.track}}}}; cursor: pointer; padding: 0"><span aria-hidden="true" style="position: absolute; top: 2px; left: {{{{row.knob}}}}; width: 26px; height: 26px; border-radius: 50%; background: #FFFFFF; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25)"></span></button></sc-if>
</div>
</sc-for>
</div>
</section>
</sc-for>
<section style="display: flex; flex-direction: column; gap: 8px">
<h3 style="margin: 0; font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted)">Appearance</h3>
<div role="radiogroup" aria-label="Appearance" style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); background: var(--seg); border-radius: 12px; padding: 3px; gap: 3px">
{seg_radio('thIsLight','Light')}
{seg_radio('thIsDark','Dark')}
{seg_radio('thIsSystem','Match iPhone')}
</div>
</section>
<sc-if value="{{{{healthBad}}}}" hint-placeholder-val="{{{{ false }}}}"><button onClick="{{{{fixHealth}}}}" style="{SECONDARY}">Run the daily check now</button></sc-if>
</div>'''
SETTINGS_SHEET = sheet('settingsOpen', 'closeSettings', 'Settings and health', SETTINGS_INNER)

HOOK_INNER = f'''<div style="padding: 12px 20px 28px; display: flex; flex-direction: column; gap: 14px">
{HANDLE}
<div style="display: flex; justify-content: space-between; align-items: center"><h2 style="{H2}; font-size: 17px">Choose a hook</h2><button onClick="{{{{closeHook}}}}" style="{LINKBTN}">Cancel</button></div>
<div style="font-size: 14px; color: var(--text2); line-height: 1.45">Strangers see the opening first. Pick the one that sounds like you; the rest of the card stays as drafted. <span style="{CHIP_NEUTRAL}">example</span></div>
<div role="radiogroup" aria-label="Hooks" style="display: flex; flex-direction: column; gap: 8px">
<sc-for list="{{{{hooks}}}}" as="hk" hint-placeholder-count="3"><button role="radio" aria-checked="{{{{hk.on}}}}" onClick="{{{{hk.pick}}}}" style="text-align: left; min-height: 56px; padding: 10px 14px; border-radius: 12px; border: 1.5px solid {{{{hk.border}}}}; background: {{{{hk.bg}}}}; cursor: pointer; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 15px; line-height: 1.4">{{{{hk.text}}}}</span><span style="font-family: {MONO}; font-size: 12px; color: var(--muted)">{{{{hk.count}}}} characters as X counts</span></button></sc-for>
</div>
<label for="te-hook-take" style="font-size: 13px; color: var(--text2)">Your take, in one line (optional)</label>
<input id="te-hook-take" value="{{{{hookTake}}}}" onChange="{{{{setHookTake}}}}" placeholder="Two reviewers beat one, when they disagree for a reason" style="min-height: 46px; border-radius: 12px; border: 1px solid var(--line); padding: 0 12px; font-family: {SANS}; font-size: 15px; background: var(--card); color: var(--ink)">
<div style="{SUB}">Your pick is recorded as a preference, so the loop can learn which openings you choose.</div>
<button onClick="{{{{saveHook}}}}" style="{PRIMARY}">Use this hook</button>
</div>'''
HOOK_SHEET = sheet('hookOpen', 'closeHook', 'Choose a hook', HOOK_INNER)

PILL = f'''<sc-if value="{{{{showPill}}}}" hint-placeholder-val="{{{{ false }}}}">
<div class="te-glow" style="position: absolute; left: 20px; right: 20px; bottom: 94px; border-radius: 999px">
<button onClick="{{{{openChat}}}}" class="te-glass" style="width: 100%; min-height: 52px; border: none; border-radius: 999px; display: flex; align-items: center; gap: 12px; padding: 0 16px; cursor: pointer; color: var(--text2); font-size: 16px; text-align: left">{orb(22)}<span>Ask Cortex…</span></button>
</div>
</sc-if>'''

BODY = f'''<x-dc>
<helmet>__HELMET__</helmet>
<div class="te-root" onKeyDown="{{{{rootKey}}}}" data-theme="{{{{themeAttr}}}}" style="width: 390px; height: 844px; box-sizing: border-box; display: flex; flex-direction: column; background: var(--paper); color: var(--ink); position: relative; overflow: hidden">
{ORB_DEFS}
<main inert="{{{{mainInert}}}}" style="flex-grow: 1; overflow-y: auto; padding: 28px 20px 28px; display: flex; flex-direction: column; gap: 22px">
{TODAY}
{POST}
{READY}
{POSTS}
{CAPTURE}
{REPLIES}
{RESULTS}
{CORTEX}
</main>
{NAV}
{PILL}
{SOURCE_SHEET}
{EDITOR_SHEET}
{CHAT_SHEET}
{SETTINGS_SHEET}
{HOOK_SHEET}
</div>
</x-dc>'''

if __name__ == '__main__':
    import sys
    open(sys.argv[1], 'w').write(BODY)
