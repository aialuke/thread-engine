Verdict: the plan is directionally right, but the live run is evidence about one rendered, native-tool surface—not the planned Grok Build CLI—and its provenance is too weak to settle tool behaviour. The decisive finding is that semantic results can be stale or malformed unless timestamp- and ID-verified; the run makes stronger capture and eligibility controls necessary, not a semantic-search verdict.

## High changes

- **Treat raw-tool capture as a pilot capability test, not an assumed CLI feature.** The plan promises every full response and CLI envelope, but xAI docs research says server-side outputs are not exposed to API callers; the live folder only preserves “returned messages,” not wire-level payloads.  
  Evidence: [plan.md:58](/Users/lukemckenzie/src/thread-engine/research/discovery-test/plan.md:58), [plan.md:68](/Users/lukemckenzie/src/thread-engine/research/discovery-test/plan.md:68), [docs-grok.md:35](/Users/lukemckenzie/src/thread-engine/research/discovery-test/docs-grok.md:35), [live README:3](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/README.md:3).  
  Edit: P7 must first record immutable original CLI stdout, stderr, streaming/envelope data, requested and observed tool arguments, model, cwd, timestamps, byte count, and hash. Explicitly answer whether CLI exposes rendered per-tool text, rather than assuming it does.

- **Replace “20 posts” with audited units: returned slots → numeric-ID posts → X-verified posts → eligible-in-window posts.** A purported result slot can have no ID or text, while the manifest still calls it one of ten posts; this run also skipped X ID checks.  
  Evidence: [S1 raw:14](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/S1.raw.txt:14), [overlap.md:5](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/overlap.md:5), [live README:7](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/README.md:7).  
  Edit: add those four denominators to `grok.jsonl`/`posts.csv`; quarantine malformed slots, preserve their count, and never score or count them as posts. Verify every extractable Grok ID before scoring.

- **Make the shared-window claim an eligibility rule, not a claim of equivalent retrieval.** The plan says each source uses the same UTC window, but default semantic retrieval returned results from well outside the active period; date-filtered semantic retrieval is only calendar-day granular.  
  Evidence: [plan.md:29](/Users/lukemckenzie/src/thread-engine/research/discovery-test/plan.md:29), [S1 raw:8](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/S1.raw.txt:8), [S1 raw:45](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/S1.raw.txt:45), [S9 raw:15](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/S9.raw.txt:15).  
  Edit: compare only ID-verified posts whose normalized timestamp is inside the exact UTC window. Report all returned-but-ineligible semantic posts separately as retrieval waste; do not silently discard them.

## Medium changes

- **Add replicated semantic probes before selecting a prompt arm.** The one dated sample fits its requested dates, but does not test `to_date` inclusivity, timezone, or midnight boundaries; the keyword-like six-hour syntax did not constrain semantic results in this sample.  
  Evidence: [S4 arguments:7](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/S4.args.json:7), [overlap.md:49](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/overlap.md:49), [S9 arguments:7](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/S9.args.json:7).  
  Edit: add P7 subtests for UTC-midnight boundaries, each date endpoint, and semantic queries with/without keyword operators. Record these as repeatable observations, never schema facts.

- **Keep every Grok run outside the repo and remove the stale contrary instruction.** The plan both requires an empty external cwd and asks for an in-repo comparison; the later section says that comparison is dropped. The live artifacts do not record cwd, so they cannot establish a clean baseline.  
  Evidence: [plan.md:92](/Users/lukemckenzie/src/thread-engine/research/discovery-test/plan.md:92), [plan.md:104](/Users/lukemckenzie/src/thread-engine/research/discovery-test/plan.md:104), [manifest.jsonl:1](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/manifest.jsonl:1).  
  Edit: delete the in-repo comparison sentence and require recorded cwd evidence for every arm.

- **Add a frozen spam/control query and report query saturation.** One broad latest keyword query filled all ten positions with promotional selling material; semantic paraphrase results had no overlap with the brand-word query and visibly include off-target material.  
  Evidence: [K1 arguments:7](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/K1.args.json:7), [report C237](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/x-search-tools-report.md:576), [overlap.md:45](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/overlap.md:45).  
  Edit: pre-freeze one promotional-negative variant per tool-research cell and report spam share per query, not only per source aggregate.

## Low change

- **Redact the blind-scoring input from raw transcripts.** Rendered output includes profile and media metadata beyond the post text.  
  Evidence: [S1 raw:3](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/S1.raw.txt:3), [plan.md:52](/Users/lukemckenzie/src/thread-engine/research/discovery-test/plan.md:52).  
  Edit: retain original hashed raw privately, but generate a separate text-and-opaque-ID scoring corpus.

## Report claims the raw files do not support

- **C229 is unsupported as an observed threshold test.** S2’s artifact was explicitly saved from S1 with one edited view count, so it cannot establish that threshold `0` returned the same posts. [live README:5](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/README.md:5), [report C229](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/x-search-tools-report.md:568).

- **C227’s “default threshold” is an inference, not a raw observation.** The raw supports only that S1 omitted the argument; its effective default comes from the reported schema. [S1 arguments:7](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/calls/S1.args.json:7), [report C227](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/x-search-tools-report.md:566).

- **C239 should be labelled inference.** Different `ID` and `Conversation ID` supports membership in another conversation, but the raw does not define that as a reply field or distinguish all relationship types. [report C239](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/x-search-tools-report.md:578).

What is sound: the plan’s ID-check requirement is essential and should remain; the run confirms that a rendered surface can expose IDs, text, GMT timestamps, engagement, and media, while exposing neither score nor language. [plan.md:16](/Users/lukemckenzie/src/thread-engine/research/discovery-test/plan.md:16), [field-inventory.md:5](/Users/lukemckenzie/src/thread-engine/research/discovery-test/private/grok-insights/runs/semantic-live-2026-09-26/field-inventory.md:5). C230–C238 are useful as narrowly labelled one-run observations once the provenance caveat is attached.

Codex session ID: 01a0dcb8-620f-7200-af3b-1b4b4c7d8b5b
Resume in Codex: codex resume 01a0dcb8-620f-7200-af3b-1b4b4c7d8b5b
