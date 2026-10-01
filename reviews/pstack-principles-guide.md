# pstack principles and guide: which change decisions in a checkable way

Source: local pstack at commit 2eb7ed4, under `/private/tmp/claude-501/-Users-lukemckenzie-src-thread-engine/a7aa1f30-0e8d-4a69-95e6-c4ac2e475eb0/scratchpad/plugins/pstack/` (`$P` below). Local files only.

Read in full: `$P/README.md`; all 23 `$P/skills/principle-*/SKILL.md` (each dir holds only SKILL.md, no references); `$P/docs/guide/README.md` and `01` to `10`.
Not read: `skills/poteto-mode/SKILL.md` (holds the "inline principles index", so how a principle is triggered at runtime is unknown), all playbooks, all other skills.

Grade for everything: vendor (the author's own docs), no experiments, "no numbers given" throughout. Nothing shows any principle changes agent behaviour; evidence is the rule text only.

Shared facts:
- Every principle file has `disable-model-invocation: true`. Guide `08`: "`/poteto-mode` reads their index at the start of every multi-step task, applies the ones the task triggers, and names each applied principle in its reply along with the decision it changed." README: "the standalone files are there so other skills can reference a principle by name". So the files are reference text unless poteto-mode (not read) loads them.
- None of the 23 files names a Cursor-only feature. Soft references: `show-me-your-work`, `typescript-best-practices`, "brain note", subagents. Portability high.
- Overlap key: R1 commit before risky ops; R2 don't weaken failing tests/silence linters; R3 clean scratch; R4 blind-review with second model; R5 Assumed/Overlooked lists; R6 delegate wide reads.

## 1. Findings (paths `$P/skills/principle-<name>/SKILL.md`)

Verdict C = checkable trigger/test that changes a decision; P = partly; S = slogan.

| # | Principle | V |
|---|---|---|
| 1 | laziness-protocol | P |
| 2 | foundational-thinking | S |
| 3 | redesign-from-first-principles | S |
| 4 | attack-the-premise | C |
| 5 | subtract-before-you-add | S |
| 6 | minimize-reader-load | C |
| 7 | outcome-oriented-execution | S |
| 8 | experience-first | S |
| 9 | exhaust-the-design-space | P |
| 10 | build-the-lever | C |
| 11 | model-the-domain | P |
| 12 | boundary-discipline | C |
| 13 | type-system-discipline | C |
| 14 | make-operations-idempotent | C |
| 15 | migrate-callers-then-delete-legacy-apis | P |
| 16 | separate-before-serializing-shared-state | C |
| 17 | prove-it-works | C |
| 18 | fix-root-causes | P |
| 19 | sequence-verifiable-units | C |
| 20 | test-behavior-not-implementation | C (strongest) |
| 21 | guard-the-context-window | S |
| 22 | never-block-on-the-human | P (conflicts) |
| 23 | encode-lessons-in-structure | C |

Per principle: (1) rule, (2) trigger/test, (3) decision changed, (4) portability, (5) overlap.

1. laziness-protocol. (1) "Aim for the most result with the least code and complexity." (2) "If answering a question requires tracing through more than 3 files or layers, flatten it." plus "**The test:** If a human developer would find the code exhausting to maintain, it is a bad solution." (second is a feeling). (3) "If a task asks you to pass a new signal through types, schemas, pipelines, or similar layers, stop and look for a more direct path." (4) Full. (5) None; repo has no diff-size rule.
2. foundational-thinking. (1) "Get the data shape right before writing logic." (2) Situations only: "choosing core types and data structures, sequencing scaffold-vs-feature work, asking what concurrent actors share"; one question: "does every subsequent phase benefit from this existing?" (3) "Sequence for option value: setup before features, tests before fixes." (4) Full. (5) Concurrency corollary duplicates #16; "Subtraction comes before scaffolding" duplicates #5.
3. redesign-from-first-principles. (1) "don't bolt it onto the existing design. Redesign as if the requirement had been there from the start." (2) "Apply when integrating a new requirement into an existing design"; no size threshold. (3) "Propagate the change through every reference: types, docs, examples, rationale sections." (4) Full. (5) None; tension with #1, text does not reconcile.
4. attack-the-premise. (1) "When two or more fixes that share one premise have failed the same gate, suspect the premise, not the fixes." (2) "Do not start the next fix before the premise is written down and the census exists." and "If the census is even across actors, the premise is not the cause." (3) After the second failed fix: write the one-sentence premise, run a census script, "Remove the asymmetry instead of compensating for it". (4) Full; needs "gate" and "actors", fits concurrent code more than content work. (5) Loosely R2; otherwise new.
5. subtract-before-you-add. (1) "When evolving a system, remove complexity first, then build." (2) "Apply when sequencing an addition, refactor, or rewrite"; no threshold for "dead". (3) "When a reference has no novel content, delete it rather than leaving a stub." (4) Full. (5) Near-duplicate of #1 and #15; not R3 (that is scratch files).
6. minimize-reader-load. (1) Track "Layers to trace" and "State to hold". (2) "Can a new reader answer 'where does X come from?' and 'what can change X?' in under 30 seconds? If not, cut layers or cut state." (3) Inline "wrappers with one caller, adapters with no second implementation"; "locals over fields, fields over module state, and module state over globals." (4) Full; test is a judgment but reviewable. (5) None; dupes #1's flat-hierarchy bullet.
7. outcome-oriented-execution. (1) "Prioritize end-state integrity over transitional stability." (2) "Use this for planned rewrites and migrations with explicit phase boundaries"; "Declare where temporary breakage is acceptable." Procedure, no test. (3) Skip compat shims between phases; "Require full static and runtime verification at plan completion". (4) Full. (5) Tension with R2/R1 if misread; "Intermediate breakage is acceptable when it is planned, scoped, and reversible" (reversible ties to R1). Near-dupe of #15.
8. experience-first. (1) "When implementation convenience conflicts with user delight, choose delight." (2) "Apply when product, UX, or feature-scope tradeoffs come up." No test. (3) "Ship less, ship better (polished experience with three features beats rough one with ten)". (4) Full, UI/product oriented; "user" widened to the next maintainer, which blurs into #6. (5) None of R1-R6.
9. exhaust-the-design-space. (1) "build 2-3 competing prototypes or sketches. Compare them side by side. Only then commit." (2) Has apply and skip lists: "Novel UI interactions (no prior art in the codebase)" vs "Bug fixes or refactors with a clear target state"; "A second flavor of the first shape does not count." (3) For a novel interaction, build three throwaways before implementing. (4) Rule portable; README implements it via `/arena` (multi-model panel, costly). (5) Near R4 (second opinion) but generates options rather than reviews a recommendation.
10. build-the-lever. (1) "When the work isn't trivial, build the tool that does it instead of doing it by hand." (2) "Applying this principle produces a file. If you cited it and there is no codemod, script, generator, or delegate skill in the diff, you didn't apply it." Skip for "a couple of obvious edits you can see at a glance." (3) "Do the first unit by hand to learn the recipe, then build the tool. Prove it by rerunning it on that unit and diffing against your hand-done version." and "Don't fan out delegates to hand-apply what a script can do." (4) Full. (5) Refines R6 (script beats fan-out). Tension with R3: "Commit the lever when the work outlives the session" vs clean scratch scripts; reconcile with "outlives the session".
11. model-the-domain. (1) "Encode the real domain in a data structure instead of scattering it across conditionals." (2) "The sign that you skipped this is a new feature that grows an existing if/else chain by one more branch, or a second boolean that must stay in sync with the first." Limit: "Prefer boring code if the current shape is already clear, local, and unlikely to grow." (3) Replace a synced second boolean with a state machine or union. (4) Full. (5) Overlaps #13; none of R1-R6.
12. boundary-discipline. (1) Validate at boundaries, trust internal types, logic in pure functions. (2) "'Is this data crossing a system boundary right now?' If not, validation is redundant." and "'Can this be a pure function that the shell just calls?' If yes, extract it." (3) Delete "redundant nil checks deep in call chains if the boundary already validated". (4) Full; fits `x_api.py`/`x_read.py` parsing. (5) None; consistent with the repo's fail-closed boundary checks.
13. type-system-discipline. (1) Make illegal states unrepresentable, brand primitives, parse external data, exhaust variants. (2) "'Can I write a comment explaining when this combination of fields is valid?' If yes, the type is too loose." and "'Where did this `any`, this `as`, this `assertNotNull` come from?'" (3) Replace `{ completed: boolean; completedAt?: Date }` with `{ kind: 'open' } | { kind: 'done'; at: Date }`. (4) Any typed language; the repo is Python scripts, so only with strict typing. `typescript-best-practices` not read. (5) Echo of R2 ("Don't lie to the type system").
14. make-operations-idempotent. (1) "converge to the correct state regardless of how many times they run or where they start from." (2) "1. What happens if this runs twice in a row? 2. What happens if the previous run crashed at every possible point? 3. Does re-execution converge to the same end state?" and "If any answer is 'it depends on what state was left behind,' the operation needs a reconciliation step." (3) Add stale-state cleanup or "PID-based stale lock detection". (4) Full; fits `loop.py`, `snapshot.py`, `/posted`. (5) None.
15. migrate-callers-then-delete-legacy-apis. (1) "migrate callers and remove the old API in the same refactor wave instead of preserving compatibility layers." (2) "No external users depend on backward compatibility; The project can absorb coordinated breaking changes". (3) "Inventory callers, migrate them, and delete the old API immediately"; also "delete tests that only protect pre-refactor implementation details". (4) Full. (5) R2 tension: deleting tests is fine only for removed code.
16. separate-before-serializing-shared-state. (1) "first ask whether they need the same mutable object. If not, eliminate the sharing." (2) "Two workers writing their own `lastX` field into one `state.json` is still shared mutation. `indexer-state.json` + `metrics-state.json` is not." and "Instructions and conventions are not concurrency control." (3) Give each parallel agent its own file/branch/worktree, no locks. (4) Full. (5) None; the repo's `loop.py`-as-sole-writer is the "serialize structurally" branch.
17. prove-it-works. (1) "Verify every task output by checking the real thing directly." (2) "Do not infer from proxies, self-reports, or 'it compiles.'"; "When verification fails, suspect the observation method before suspecting the system."; best form "a deterministic script that re-runs the same comparison". (3) After the build passes, run the real command and read the written value. (4) Full. (5) Complements R5 (do the check vs disclose unrun checks); overlaps the repo's "Every path and claim is sourced".
18. fix-root-causes. (1) "do not fix symptoms. Trace every problem to its root cause and fix it there." (2) "Do not add guards (adding a nil check to silence a crash is a symptom fix)"; "If a workaround needs a paragraph-long comment to justify it, the code is wrong"; "Reproduce first". (3) Refuse the nil-check patch; "grep for the same pattern, fix all instances"; for restart bugs "suspect stale persistent state first". (4) Full. (5) Same instinct as R2; adds "reproduce first" and "grep for the pattern", which R2 lacks.
19. sequence-verifiable-units. (1) "Order work as a sequence of small units, each ending in a state you can check, and don't advance until the current one is green." (2) "Each unit is a before/after bracket: known-good state, one change, run the check, then proceed." Delivery: "The canonical shape is the failing test first, then the fix on top." (3) In a sweep, check after each file, not after the batch. (4) Full. (5) R1 (commit per unit gives the restore point); complements R2.
20. test-behavior-not-implementation. (1) "A test calls the code the way its users do and asserts the result they observe against a literal expected value." (2) "before you keep a test, ask whether it would still pass if every function it imports returned `undefined`. If yes, it observes no behavior and cannot fail for a defect. Rewrite the assertion or delete the test." Five named shapes (weak assertion, mock-only, self-referential, constant pin, fixture asserts fixture). (3) Replace `expect(LIMITS.maxTools).toBe(8)` with a call on one input and a literal output, or delete. (4) Language-neutral test; examples are Jest-style; repo uses `unittest`, shapes translate. (5) R2 conflict: R2 forbids weakening a failing test, this says delete tests that cannot fail; compatible only for tests that never fail. Add that sentence.
21. guard-the-context-window. (1) "Route verbose outputs, screenshots, and large documents to subagents. The main context gets summaries, not raw data." (2) "Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning." No size threshold; "Limit files per phase, set turn budgets" gives no numbers. (3) Send a large read to a subagent, keep the summary. (4) Full. (5) R6 almost verbatim.
22. never-block-on-the-human. (1) "Proceed, then present. Do the work, show the result. Don't ask 'should I do X?' Do X, explain why." (2) "Irreversible actions (force-push, delete production data, send external messages) still require confirmation." "Product direction comes from the human." (3) Skip "may I?" on reversible edits. (4) In Claude Code the permission system gates tools regardless; this changes wording only. (5) Conflicts with repo, see section 2.
23. encode-lessons-in-structure. (1) "Encode recurring fixes in mechanisms (tools, code, metadata, automation) instead of textual instructions." (2) "When you catch yourself writing the same instruction a second time: 1. Ask: can this be a lint rule, a metadata flag, a runtime check, or a script? 2. If yes, encode it. Delete the instruction". Strength order: "an unrepresentable state that cannot compile, then a lint or banned API that fails CI, then a canonical helper, then a runtime check". (3) On the second repeated correction, write a hook or script rather than another AGENTS.md line. (4) Full. (5) Duplicates RULES.md ("convert it to a hook"); only the strength order and anti-patterns ("'I'll keep that in mind' does not persist") are new.

## 2. Contradicts the plan

- never-block-on-the-human vs the repo: "Don't ask 'should I do X?' Do X, explain why." AGENTS.md says "Start non-trivial work in Plan mode"; RULES.md says "If unsure which applies, ask." and write-capable delegation "need my go-ahead". The carve-out ("irreversible actions ... still require confirmation") covers only some of it.
- test-behavior-not-implementation and migrate-callers both direct deleting tests; R2 says do not weaken a failing test. Add "never delete a currently failing test".
- build-the-lever "Commit the lever when the work outlives the session" vs R3 clean scratch scripts. Compatible only through that test.
- laziness-protocol (smallest diff) vs redesign-from-first-principles (redesign as if from day one): no arbitration in the text. README says "the goal is not to maximize loc, in fact it's the opposite".
- The README's "twenty-three playbooks" is a different 23 from the 23 principles; do not conflate.
- The guide demands principles change decisions ("A principle citation with no decision behind it is the tell that it name-dropped instead of applying.") but the files contain no mechanism for that, and I found no evidence any principle was evaluated.

## 3. Searched, found nothing

- Numbers (success rates, effect sizes, token counts): none in README, principle files or guide.
- Per-principle references: none exist.
- Cursor dependencies inside the 23 principle files: none.
- How poteto-mode triggers each principle: not read.

## 4. Guide docs (all read)

Setup (`01`): "`/add-plugin pstack`" (Cursor); `/setup-pstack` "writes `~/.cursor/rules/pstack-models.mdc`, a small rule every pstack skill reads." Cursor-specific; Claude Code has no equivalent command or `.mdc` rules. "For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size." Default panel "opus 5.5 / sol / grok" (README); the repo is dropping Grok (D88). Verification offer writes `.cursor/skills/verify-<app>/`. "`/poteto-mode` is sticky."

Prompting (`README`, `02`, `05`, `08`, `10`): "Give the agent a goal and a way to check it". "new task" re-matches: "Without those two phrases, a mode mid-Feature tends to treat your question as the next feature step." Pitfall: "don't enumerate skills in your prompt ... a hand-written sequence usually reorders or drops steps the playbook would have kept." Build prompts pin behaviour ("text output stays byte-identical"; "record the current output first and prove it's unchanged after"; perf "states the measurement, not a vibe"). Steering: "use subtract before you add. delete the obsolete adapters first, then design what's left."

Verification (`06`): "State the finish condition up front"; "a confident reply without evidence" is "a red flag"; a reply should say "inconclusive" when a check could not run (overlaps R5). Check by type: CLI runs the real command; UI walks the flow; parser replays saved input; perf compares profiles; storage reads back the value. Shipping: "the agent that judges a change is never the one that wrote it" (R4-like). Babysit "never merges, even with everything green, because merging is a different decision."

Overnight (`07`): contract = goal, finish condition, permissions, escape hatch. Example: "done means zero old callers, all parser fixtures pass, old api deleted. keep a decision log. don't ask me before committing. /loop until done. if you're truly stuck after a few hours, stop and write up why." Loop: "One change, one check, one log row, every iteration ... the finish condition never quietly relaxes to declare victory." Pitfall: "a duration is not a finish condition." `/show-me-your-work` TSV (time, phase, decision, reason, evidence pointer, result); a reviewer on a different model family reads the trail first. "`/loop` is Cursor's built-in wake mechanism, not a pstack skill"; Claude Code equivalent not read.

Skill testing (`09`): Eval playbook: "candidate agents get an organic-looking task in sanitized directories, never the words 'eval' or 'candidate'"; "One judge scores all outputs under neutral labels". Extends R4 with candidates not knowing they are tested; relevant to the Jev tests. "don't edit a skill mid-task because it's misbehaving. Fix it in its own PR."

Pitfalls (`10`): enumerating skills; vague finish condition; "Parallel agents in one worktree"; `/arena` for coverage (use `/swarm`); "Accepting every review comment"; treating `auto` as a model slug; "Reporting success off a green build"; writing a SKILL.md freehand.

What costs many subagents or tokens (no token counts given anywhere):
- `/arena`: "N subagents attempt the same design or code brief in parallel" plus a judge; example "5 candidates" (`04`). `/architect` "runs `/arena`" by default (`04`).
- `/interrogate`: "several reviewers on different model families" (`04`).
- `/swarm`: "one worker per package" (`04`, `10`).
- `/how`: "fans out two to four read-only explorers"; `/why` queries all evidence categories "in parallel" (`03`).
- Shipping: "One fresh agent per PR proves the behavior live" (`06`).
- Autopilot-full: "A swarm of fresh verifiers starts a round at the owner's code-ready head and again at every later push that changes the patch" (`07`).
- Orchestrate: "It's deliberately heavy machinery." (`07`).
- `/maintain-verification-skill`: "one read-only source reader per feature in parallel, then one live pass" (`06`).
- `/reflect`: "three parallel reviewers, then a synthesizer" (`09`).
- `/show-me-your-work`: extra reviewer on another model (`07`).
- Overnight `/loop`: hours of iterations.

## 5. Ranked list

Most worth adopting:
1. test-behavior-not-implementation: the `undefined` check is pass/fail and usable in `tests/`; add "never delete a currently failing test".
2. prove-it-works: real artifact not proxy; pairs with R5 and the repo's VERIFY rule.
3. build-the-lever: "no file in the diff means you did not apply it" is auditable; fits a no-code operator.
4. attack-the-premise: after two failed fixes under one premise, write the premise and a census script.
5. sequence-verifiable-units: check each unit before the next; pairs with R1.
6. make-operations-idempotent: three questions for `loop.py`, `snapshot.py`, `/posted` reruns.
7. separate-before-serializing-shared-state: one owner per file when agents run in parallel.
8. boundary-discipline: delete redundant inner validation; keep parse checks at the X edge.
9. fix-root-causes: adds "reproduce first" and "grep for the same pattern".

Duplicate what the reader has: encode-lessons-in-structure (RULES.md "convert it to a hook"); guard-the-context-window (R6); fix-root-causes and prove-it-works in part (R2, R5).

Skip: foundational-thinking, redesign-from-first-principles, subtract-before-you-add, outcome-oriented-execution, experience-first (no tests, first two pull against laziness); type-system-discipline (repo is Python); migrate-callers (few internal APIs, edges R2); exhaust-the-design-space and model-the-domain (loose triggers, subagent cost); never-block-on-the-human (contradicts Plan mode); laziness-protocol and minimize-reader-load (style; take only the "3 files" and "30 seconds" tests if needed).

## 6. Hand-offs

- Read `skills/poteto-mode/SKILL.md` index and the Eval playbook; both were out of scope.
- Cursor-specific: `/add-plugin`, `~/.cursor/rules/*.mdc`, `.cursor/skills/`, `/loop`, `cursor-team-kit`, `/deslop`, `create-skill`.
- Default model panel includes Grok.

## 7. Citation trail

README principles table to the 23 files; guide README to `01`-`10`. Cross-links to unread skills not followed.

Assumed: the glob for `skills/principle-*/**` is complete; `disable-model-invocation` works as in Claude Code docs (not verified).
Overlooked: poteto-mode index and playbooks; no behavioural test of any principle; repo code not audited against the principles.
