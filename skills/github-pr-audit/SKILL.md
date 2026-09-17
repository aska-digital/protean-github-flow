---
name: github-pr-audit
description: "Use when auditing a GitHub PR or issue before merge."
version: 1.13.0
author: the Protean publication
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Code-Review, Pull-Requests, QA, Audit]
    related_skills: [github-code-review, github-auth, adversarial-review]
---

# GitHub PR / Issue Audit (pre-merge QA)

A focused workflow for the QA pass on a GitHub contribution — PR or feature
issue — before it lands on a high-visibility open-source repo. This is the
VERIFICATION DISCIPLINE that prevents publishing a wrong or sloppy review, plus
the GitHub permission realities that shape how you sign off. For the raw
diff/comment mechanics (gh vs REST, inline comments), load `github-code-review`
alongside this — that skill covers commands; this one covers gates.

## When to use
- "Review this PR", "audit this contribution", "make sure we don't look stupid
  on this merge".
- Any PR/issue on a watched repo where a bad review reflects on the team.
- Companion to `github-code-review`: load both. That one is the tool; this one
  is the QA checklist.

## The non-negotiable sequence

### 1. Get LIVE state — never trust a handoff diff
A `.diff` file dropped in chat or `/tmp` is a SNAPSHOT and may be a stale draft.
The branch is often tightened BEFORE push. Critiquing it produces a review of
code that isn't in the PR — the exact "look stupid" failure.
- `git diff main...HEAD` on the local checkout. First confirm you're actually on
  the PR branch: `git branch --show-current`.
- `gh pr diff N --repo O/R` for the remote truth.
- If they disagree, the local checkout is stale — trust `gh` output and say so.

### 2. Verify the bug premise against `main`
Do not accept the PR's rationale. Read the actual code on `main`:
- `git show main:<path>` (pipe through sed/awk to the function), or
- `git worktree add -q /tmp/hm-main main`, read/run there, then
  `git worktree remove /tmp/hm-main --force`.
Confirm the broken branch/symptom the PR claims to fix REALLY exists on main.
If it doesn't, the fix may be mischaracterized (partial, or already fixed).
State it explicitly.

### 2a. Prove the finding is a DEFECT, not the documented design
A reproducible observation is not a defect. Read the project's own intent for the behaviour and
name which bar the finding clears:
- a user-visible failure — duplicate execution, wrong or lost data, a crash;
- a demonstrated violation of a written invariant under the conditions you measured;
- proof the behaviour is unintended: a surface requests a resource nothing needs.
Read the area's `AGENTS.md`, the user docs, and any "do not fix this" list, and quote the line that
settles it. Topology is the trap: two processes, two holders of one file, a second connection or
lock all look alarming and are usually the architecture. The mechanism is not the harm — a count, a
holder, or a repeated shape only counts together with the failure it produces. State the falsifier
(the observation that would show the behaviour is intended) and look for it before you file or fix.

### 2b. Runtime-changing fix? Prove it on the live system FIRST
Green tests are not this proof: they show the function is right on the inputs you handed it, not that it is reached when the bug happens, nor that its inputs are populated then. Author-side gate: `github-pr-workflow` §2b. Run it against the PR head before any sign-off.
- Rebuild the artifact the real entry point loads and confirm the change is in it — a stale build exercises the old code and produces a false reading either way.
- Reproduce the original symptom; capture the process tree with parent PIDs, listening ports, `lsof` on the contested file, and the record the decision reads.
- If the live run shows the fix does not work, that IS the finding. Say so and send it back (or withdraw), rather than signing off on unit tests.
- If it cannot be run in this environment, say what was verified and what was not. Never imply the live behaviour is confirmed.

### 3. RUN the test suite — in the repo's own interpreter
Never trust a PR body's "17 passed". Execute it.
- `python` is often NOT on PATH. Check for `venv/bin/python` (target version per
  `.python-version`), or use `uv run`. Repo venv example:
  `./venv/bin/python -m pytest tests/tui_gateway/test_x.py -q`
- Run the touched file AND the sibling suites the PR depends on.
- Test node IDs are CLASS-qualified: `file.py::TestClass::test_method`, not
  `file.py::test_method` (the latter fails with "no match"). Grep the class name
  first if unsure.
- Record the real pass/fail counts in your review output.

### 4. Verify evidence claims in the PR/issue body
If the body cites a "pre-existing failure" or a specific test as proof, RUN that
exact test on `main` AND on the branch. A reviewer who runs the suite will catch
a false claim — so you must catch it first. If a claim is false or orthogonal
(e.g. cites a GUI test that passes and is unrelated to the logic touched), strip
it via `gh pr edit N --repo O/R --body-file <file>` — you have edit rights on
your own account's PR. Never leave a verifiable falsehood in a public PR.

### 4a. Audit the evidence register
For a multi-finding PR or issue, define the counted unit and count each item once at its highest impact. Separate fixes included in the current head from requests, overlaps, and unresolved findings. Map every row to its exact artifact, commit, test, and status. Record the evidence boundary: base or head, commit or composition, environment, and measurement time when relevant. Missing transferred artifacts or unrun tests do not establish a claim; list them as separate unverified follow-ups.

### 5. Scope & rubric fit
Read the repo's `AGENTS.md` / `CONTRIBUTING.md`. Check specifically:
- **Speculative infrastructure** — shared registries/helpers with NO in-PR
  consumer. Textbook case: a `_X_KEYS` frozenset + `_drop_stale_key` helper
  gating behavior `config.pop` already provides. Trace the code: if an unknown
  key already survives a persist (e.g. `dict(existing)` copy + the function never
  enumerates it), the registry adds ZERO behavior. Flag and recommend deletion.
- New `HERMES_*` env vars for non-secret config, cache-breaking mid-conversation
  changes, scope creep that revives a closed direction.
- Feature requests belong in SEPARATE issues, not bundled into a bugfix PR.
- The bars a good fix meets: "fix real bugs well" + "behavior contracts over
  snapshots" + "E2E validation not just green mocks".

### 6. Posting the sign-off — GitHub blocks self-approval
`gh pr review N --approve` from the PR AUTHOR's account fails:
`Review Can not approve your own pull request` (hard API rule, not policy).
- Do NOT fake an outside-approver stamp or spin up a second account.
- Post a transparent QA-pass COMMENT instead: `gh pr comment N --repo O/R
  --body-file <file>`. Lead with "QA pass" (honest provenance), document
  the substance, the test numbers you actually ran, and any housekeeping fixed.
### 6b. When you also own the MERGE lane
Self-approval being impossible does NOT block the merge — review and merge are
separate permissions. Check the real gates instead of assuming a human must act:
`gh api repos/O/R/branches/main --jq .protected` and `gh api repos/O/R --jq .permissions`.
With no branch protection and `admin`, merge it yourself (`gh pr merge N --repo O/R
--<method>`), then post the QA-pass comment on the merged PR and read the merge back.
- Take the merge METHOD from the repo's own history, not the provider default:
  `git rev-list --count --merges origin/main`. Zero merges = linear history, so use
  `--rebase` or `--squash`; a bare `--merge` would add the repo's first merge commit.
  Record the choice and the rejected alternative in the receipt.
- Rebase/squash REWRITE the SHAs you audited. State the new main SHA and note that the
  pre-merge SHA still exists on the branch/PR refs, or the receipt contradicts the audit.
- Re-check the stack after every merge: re-read `mergeable`/`mergeStateStatus` on the remaining open PRs before merging the next (UNKNOWN means GitHub is recomputing, wait and re-read). A sibling landing can turn a CLEAN PR CONFLICTING; that PR stays open with a rebase note, and the new head is re-verified before merge. Verified 2026-09-17.
- For issues: post scoping nits (e.g. "proposed `sessions list --model` collides
  with the existing `sessions list` command — extend it instead") as
  `gh issue comment`.

### 6c. Say it was an automated post

Anything the agent writes and posts itself (a PR body, a review, an issue or PR
comment) closes with one short line saying a machine wrote it:

> Automated posting by agentic team with human oversight.

- Last line of the body or comment, as a blockquote. GitHub renders it muted, so it
  reads as a footnote instead of a claim inside the argument.
- No team or product name, no apology, no hedging, no "I am only an AI" framing, no
  offer to defer to a human. It is a fact sentence like any other.
- Once per thread. A second PR from the same team gets its own line; a comment on a
  thread whose body already carries one does not repeat it, so read the body first.
- Provenance is not a discount. The evidence bar here (red-on-base test, real
  counts, live state) does not drop because the post is automated, and the line
  never softens a claim or an ask.
- **Read the body before posting any comment.** The line lives once per thread, and
  on your own PR the body is that place. So check first, every time:
  `gh pr view N --repo O/R --json body --jq '.body' | grep -c 'Automated posting'`
  Non-zero: the thread is already disclosed, so the comment goes without the line.
  Zero: either it is someone else's thread, or your own body never got one — add it.
  Skipping this check is how a comment ends up repeating a disclosure that is already
  rendered directly above it.
- Commit bodies stay in the repo's own register (short, no trailer). The PR body
  carries the disclosure for the branch.

### 6d. A runtime fix is only proven against the live process tree

A green unit test proves the decision function works on the inputs you handed it. It says nothing about whether that function is reached at the moment the bug happens, or whether its inputs are populated when it runs. Run this gate **before the PR exists** (`github-pr-workflow` §2b); an auditor runs the same steps against the PR head, and a fix that has not passed it is not ready to publish. For any fix claiming to stop a process being spawned, a file being written, or a route being taken, reproduce it live and name the evidence: the process list with parent PIDs, the listening port, `lsof` on the contested file, and the record the decision reads.

- **A stale build tests the old code.** Rebuild the artifact the entry point actually loads and confirm your change is in it before drawing any conclusion from the run.
- **A cache fed by a later event cannot affect the first decision.** If the input arrives from a poll, a status response, or any request that happens after startup, it is empty exactly when a boot-time decision runs. Read the authoritative record the other process already publishes, ideally one that revalidates liveness on read, instead of mirroring it in memory.
- **Check that the process you route to is the process you mean.** "Route it to the primary" is wrong whenever the primary is a different instance from the one the problem is about; only the live socket wiring proves which is which.
- **If the live run shows the fix does not work, withdraw rather than land.** Close the PR with the evidence, state what the fix cannot do, and file the reproduction where triage will see it. A withdrawn PR with a live repro beats a merged one that does not fix the bug.

## Cross-session audit SOP (own repos — standing rule)

Every PR on a team-owned repo ships in two sessions. Build session stages the PR unmerged on a branch plus a handoff prompt file beneath the project's delegation cache directory with PR URL, head SHA, advisory verdicts, reference paths, and standing constraints. Fresh-eyes session on different model configs re-verifies every claim live, then merges on PASS or returns defect rows on FAIL. Build session refreshes the PR body on every push so it always declares the live head SHA. A body naming a superseded head fails audit on paperwork alone (hermes-desktop-mods #2). Proven: hermes-desktop-mods #1, where fresh eyes caught 2 real defects the build session missed. Staged verdicts are advisory only, never merge authority. Journal every SOP step.

When a fix has two defensible policies and the maintainer should pick one, ship
both as independent commits on one branch rather than asking first. One review
thread, no second branch to rebase, and their pick is a single revert instead of
a request for you to redo the work.

- Commit 1 is the base fix; commit 2 swaps in the alternative, so HEAD carries
the alternative and one revert returns the base.
- In the body, say what each does, which is HEAD, and that a revert switches
policies. Name the trade-off in one line each (what is lost, what is paid).
- Keep both commits green on their own. A commit that only passes on top of the
  other is not a choice.
- Keep the title neutral about which commit is HEAD. A title lifted from one
  commit's subject (or a checkmark on one policy) reads as the recommendation you
  were trying not to make. Name the shared outcome — "no card renders without a
  title" — and let the body say what each policy does.

## Keep the public text short

Reviewers pay for every word. The audit work is verbose; the PR text is not.

- **Plain-language floor applies to PR/issue text.** If the repo's audience is
  not all-native-English or not all-steeped-in-the-project, the PR title, body
  and comments follow the same bar as a README: say what the change does in the
  first lines, no jargon when a plain word exists, one idea per sentence, no
  invented hyphen compounds. A reviewer who cannot parse the body will not parse
  the diff either.
- **PR body: one screen.** What it does, why it matters, repro, one test line, the
  checklist. Cut the reasoning that the diff and tests already show.
- **Comments: a few lines.** State what changed and anything a reviewer must know to
  judge it. Do not restate the body or narrate the investigation.
- **Recommend, don't direct, on a repo you do not maintain.** An imperative in a
  comment ("Keep one, close the other three", "Settle the contract first") reads as
  authority you do not have. Give the observation and leave the decision with the
  maintainer: "this is the only one covering both platforms, so it may be the cleanest
  to keep — maintainers' call". Same rule for issues and review requests.
- **State the fact, do not forecast the merge.** "This one skips non-regular files;
  #109752 refuses them" — not "one difference if this one lands". Predicting whether it
  merges hedges and reads as an order at once.
- **Superseded comments get deleted, not stacked.** Self-correcting in a new comment
  leaves a stale claim in the thread; edit or delete it and post one current comment
  (the user reads the whole thread cost first).
- **Check whether the repo enforces its template before obeying it.** A
  `pull_request_template.md` proves nothing on its own — sample the last ~15 merged PRs
  (`gh pr list --state merged --limit 15 --json number,author,title`, then read each
  `.body`). hermes-agent: none use the template; house bodies are 14–29 non-blank lines
  with no checklist, shaped as an outcome sentence → `## Changes` (terse
  `path::symbol — what` bullets) → a before/after `## Validation` table → refs. A body
  3–4× that reads as a diary, and a checklist nobody else fills in is not a virtue.
  Match the merged-PR register; keep whatever sections the house style actually uses.
- **Only condense where nobody has engaged.** Editing the description of a PR or issue that
  already has comments or reviews makes contributors re-read text they had already judged
  (and looks like rewriting history under discussion). Zero third-party comments/reviews is
  the bar; leave the rest alone.
- **Check where a long explanation lands before parking it.** A code comment or commit
  body is read only by someone already in that file or history — but "in that file" is not
  automatically cheap: a file that is `@embedFile`'d into a binary, or written to disk by an
  installer, ships its comments to every installation. Grep the ship path first, then match
  the neighbouring comments' length (2-3 lines is the usual register) and keep only the why.
- **Measure the prose share of an asset diff.** Count added comment bytes against total
  added bytes; a file grown mostly by prose is a review liability and a per-install
  footprint at once. Trim to the why and let the tests carry the rest.
- **Match the maintainer's real register for commit bodies.** Sample their recent commits
  (`gh api repos/O/R/commits?author=X`) and count non-blank body lines instead of guessing;
  a body several times the house median reads as a diary. Keep root cause plus a pointer to
  the proof, leave raw test output in the PR body where a reviewer looks for it, and keep
  the subject on one line.
- **Copy the maintainer's SHAPE, not just their length.** Read 3-4 of their PR bodies before
  writing on that repo (`gh pr list --repo O/R --state merged --author <them> --limit 4 --json
  number`, then `gh pr view N --repo O/R --json body`). hermes-agent / teknium1, verbatim from
  #109880, #109841, #109649: one sentence giving the new behaviour in plain words, blank line,
  `## Root cause` (1-2 sentences), `## Changes` (terse `path::symbol — what` bullets),
  `## Validation` as a before/after table, then plain lines for follow-ups. No hedging (`may`,
  `worth`, `arguably`), no framing lines ("Two notes for..."), no first person, no restating the
  diff. A comment is the same voice in 2-3 lines.
- **Never open with a frame you invented.** These are AI tells a reader deletes: "Two things worth
  stating plainly", "Findings first, because", "The honest gap I will not paper over", "I want to
  be upfront that", "One caveat worth flagging". A frame that promises the reader something is not
  the thing. Start with the fact.
- **State a limitation as a fact, not a confession.** "Not verified live: idle-reap persistence is
  unit tests only" beats any sentence about being honest; the reader forms the trust judgement.
- **Do not vouch for your own compliance.** "Only the test file changed, and it is exactly the salvage
  that check asked for" is the agent assuring the reader it followed instructions; the maintainer edited
  it to "Only the test file changed (the salvage that check asked for)". State the correspondence flatly,
  or put it in a parenthesis. Same family as the verdicts and rankings below.
- **Keep drafting scaffolding out of posted text.** "DRAFT 1", "Option (a) vs (b)", "PLAN, pending
  your go" belong in chat while a decision is pending, never in a PR body, issue, or comment.
- **Narrate the result, not the search.** "after tracing", "I checked X and found", "it turns out".

### 6e. Before you post, run the prose gate

The register rules in this skill are enforced by a command, because a comment went out
carrying five em dashes and a self-referential opener while the writing skill sat unloaded:

```bash
python3 scripts/protean-drafts/check-prose.py <file-to-post>
```

Exit 1 blocks the post. It flags em dashes, clause-stitching semicolons, banned frame
openers and signposts, paragraphs over 420 characters, and internal identifiers, and it
skips fenced code so quoted command output is not punished. Fix or justify each hit, post,
then re-fetch the live body and run it again:

```bash
gh api repos/O/R/issues/comments/<id> --jq .body > /tmp/live.md
python3 scripts/protean-drafts/check-prose.py /tmp/live.md
```

A clean local file proves nothing about the published text, and the gate is the only check
that has actually caught anything. Posting with it unrun is the failure mode to avoid, not
a style preference.

### 6f. Draft or ready: what the state does and does not prove

Read the state with the rest of the live data, never from the body text:
`gh pr view N --repo O/R --json isDraft,state,headRefOid,mergeable,mergeStateStatus`.

- **A draft cannot be merged.** A merge recommendation is valid only for a ready head, so
  re-read `isDraft` immediately before any merge command. Converting a ready pull request back
  to a draft re-locks the merge until it is marked ready again.
- **Code owners are not automatically requested on a draft.** Their absence on a draft is
  documented platform behaviour, not a missing step: do not file it as a defect and do not read
  it as reviewers ignoring the change.
- **Marking ready is what requests code-owner review.** Anything read about review state after
  that event is a live read, never an assumption carried over from the draft.
- **Do not infer check or protection behaviour from the state.** Whether checks run on a draft,
  and how draft state interacts with branch protection, rulesets, required checks, or merge
  queues, is not stated where the draft rules are stated. Read check runs and branch rules live
  and say which of the two you read.
- **Ready is not approval, a verdict, or green CI**, and a draft is not evidence that the code is
  incomplete, unsafe, or unreviewed. The state carries only the facts above.

Audit a draft as readiness feedback. The exact-head merge verdict applies to a ready head, and any
new head voids the previous verdict.

## Never publish internal identifiers

Public text carries no internal names: profile names, team or agent names, local filesystem paths,
usernames, hostnames, session ids. A profile becomes "a custom profile"; a home path becomes a
relative placeholder. Ambient detail feels harmless while writing and is exactly what the reader
reads as a leak.

Run the pass before posting, not after:

```bash
TEXT=comment.md
grep -niE "<profile names>|<team name>|<usernames>|<absolute home path>" "$TEXT" || echo clean
```

A non-zero `EXIT:` from the wrapper means a review-required label class, so inspect before posting.
`IP_ADDRESS` on a loopback literal (`127.0.0.1`) is informational. After posting, re-fetch the
published body and grep it again: an audit of the local file proves nothing about the live text.

**Audit by surface class, not by what you just posted.** An issue body is a body you own, and it is
the surface most often missed — a sweep that covers the comment you just wrote leaves the report you
opened the thread with. Enumerate every surface you authored in the engagement, then grep each:
every PR body, every issue body, every comment, and any quoted command output inside them. Quoted
terminal output is where identifiers hide: a pasted `served_profiles` list, `lsof` rows, and
`--profile <name>` command lines carry names and home paths that prose does not. Redact the list to a
count (`"served_profiles": [9 profiles, names withheld]`) and a home path to a relative
placeholder.
A second model's independent pass is what caught the issue body the author's own audit missed.

**Timestamp a point-in-time measurement in the artifact itself.** A number taken from `ps` or `lsof`
(RSS, fd counts, pids) cannot be reproduced minutes later, so an independent verifier can only call it
unverifiable, and a reader cannot tell whether it was ever true. Write the value with its basis —
"462.7 MB RSS at 12:11Z (`ps -o rss= -p 69004`)". Structural claims re-verify on demand; measurements
carry their timestamp or they decay into noise.

## Pitfalls
- **A rebase is not verified by 'it applied cleanly'. Compare trees.** `git merge-tree --write-tree <base> <prhead>` (git 2.38+) prints the tree a correct three-way merge would produce, and exits 0 when the merge is clean. If that tree hash equals the rebased head's tree (`git rev-parse <rebased>^{tree}`), the rebased commit IS the merge result: no hand-edit, no mis-resolved hunk, no silently dropped file can hide in it. Pair it with `git range-diff <old-base>..<prhead> <new-base>..<rebased>`, which shows path renames (the usual rebase-byproduct) and any hunk that actually changed, and with `git diff --numstat <new-base> <rebased>` to confirm the file scope is exactly the PR's.
- **A wide pytest run can die on the shell's file-descriptor limit and look like broken code.** On macOS the default is `ulimit -n 256`; a multi-file invocation then fails during tmp-path iteration with `OSError: [Errno 24] Too many open files`, producing hundreds of collection ERRORs. Re-run with `ulimit -n 6144` before reporting or dismissing them, and say in the receipt which limit was in force.
- **Prove red-on-base without mutating the checkout.** `git show <base>:<path> > <path>` edits a tracked file in the tree you are auditing. Instead extract a read-only copy: `mkdir -p /tmp/base && git archive <base-sha> | tar -x -C /tmp/base`, copy the PR's NEW test files over it, and run pytest from there with the repo's interpreter. `git archive` writes nothing back, and the failures you get are genuine base failures (name them: the missing symbol in the AttributeError is the proof the test binds to the new code).
- **A scanner that only sees the diff is not a scanner.** A repo gate that
  enumerates via `git add -A -n` (or `git status`) lists only index-relative
  changes — on a clean checkout it scans **zero files** and prints PASS. Prove a
  gate enumerated something before trusting its PASS: in a throwaway clone run
  `git read-tree --empty`, then re-run it. The first PASS on a pristine clone is
  usually vacuous; the real failure appears only once a file is modified.
- **Count the terms a scan loaded, not the ones you assume.** A term/denylist
  built from environment or a gitignored config is empty in your checkout, so one
  scan can miss most names actually present. Check the inventory size, and use a
  direct `grep` per known name to get the true exposure count before reporting
  either a leak or a clean pass.
- **A pre-existing gate failure is still a merge gate.** If a branch's
  public-safety scan also fails on `main`, reproduce it in a `main` worktree and
  report it as a blocker with an owner decision — never silently edit a deliberate
  authored artifact (branding copy, published names) just to force green.
- **Review comments are claims, not results.** When an automated/peer review flags
  your PR, reproduce the finding against the PR HEAD in a throwaway worktree
  (`git worktree add /tmp/prN <sha>`) before replying: the substance can be right
  while the detail is wrong (a bot claimed PyYAML folds `y`/`n` to bools — it does
  not; they resolve as strings). Then run the PR body's OWN "how to test" steps —
  a body that documents a repro which doesn't reproduce is worse than no repro,
  because the next reviewer runs it. Best reply = confirm what's real, correct the
  wrong detail, add the case the comment missed, and name what is deliberately out
  of scope.
- **Check for an adjacent instance of the same bug class the comment missed.** A
  guard keyed on a parsed type silently ignores the same value written in another
  form (e.g. a `isinstance(value, bool)` gate misses the quoted STRING `'false'`
  that the CLI itself writes for string-typed defaults). Probe the neighbouring
  writer/entry point, not just the reported token.
- **Read the consumer's precedence before judging a fallback's policy.** When a PR
  adds a fallback value to a payload field, the component that READS the field may
  prefer it over a different fallback it already applies further down, so the new
  value displaces a better existing label/behaviour — and the variant the body calls
  the "safer default" can be the one that loses information. Grep the field to its
  read site and name which source wins the `orelse`/`??`/`||` chain. Live user data
  is the tiebreak: the artefact on the author's own machine showed the displaced
  value in use while the prose claimed otherwise.
- **A new test can pass with the change deleted — test the trigger, not the tick.**
  Attribute each new case individually. If an earlier fallback short-circuits the
  condition the case is meant to exercise, its assertion is vacuous (delete the new
  clause and it still passes). Build the input only the new branch can decide (the
  unreadable/keyless case, not the readable one an existing fallback already covers)
  and confirm that case goes red without the code.
- **Intent comes from the repo's own user-facing surfaces, not from inference.** To
  settle "is this behaviour a bug or intended", quote the maintainers' own artefacts:
  a settings label, a documented model, the framing of the linked issue. A defect-filed
  issue plus a merged guard on the same class settles it; a behaviour the author merely
  likes is a fork concern, not a reason to re-open PR scope.
- **Detector/linter additions must be idempotent and meaning-preserving.** For any
  check that rewrites config on `--fix`: run it twice and assert the second pass
  reports and rewrites nothing (a guard that re-fires every run is worse than no
  check), and pin that the rewrite never changes the resolved runtime behavior.
  Prefer the value the runtime already resolves to over "the sane default" — the
  fix's job is to make an existing state legible, not to choose for the user.
- **Flag resolver-side accidents instead of cementing them.** When a legacy value
  only resolves the way it does through an accident (e.g. a blank/null value
  stringified to `"none"` and caught by an alias map), the surface fix should name
  it and preserve behavior, and the PR/comment should hand the underlying quirk to
  the resolver's owners as its own item.
- **A text search for a key's value is wrong in both directions — read the parsed node.**
  Detection that greps a file for the value while reading the effective value from a
  dotted key will report a documented value as drift when a decoy line exists
  elsewhere (another section, a block scalar, a duplicate block), AND miss the shapes
  a value really takes: flow style, a quoted key, an anchored `*alias`, and a
  duplicate block whose last entry wins. `yaml.compose()` + walking to the key's own
  node gives the scalar as written (quoted vs plain, `off` vs `false`) with no
  false-positive surface. Write the test table with both classes: decoys that must
  stay silent, and shapes that must be caught.
- **A repo's self-test that clones HEAD tests the last COMMIT, not your working tree.**
  A `fresh-clone-test.sh`-style gate (`git clone <repo> <tmp>` internally) silently
  re-verifies the previous commit while your new edits sit uncommitted — it passes, and
  proves nothing about the change you are about to push. Commit first, then re-run the
  gate, and check the gate's own printed SHA equals your new HEAD.
- **A fresh `git clone` lands on the DEFAULT branch, not the PR.** `git clone` then
  `git diff origin/main...origin/pr` audits correctly, but running the repo's gates in
  that working tree runs them against `main` — and they PASS, so nothing looks wrong.
  Fetch `refs/pull/N/head`, `git checkout --detach <head-sha>`, assert
  `git rev-parse HEAD` equals the audited head, and only then run the gates. Re-run after
  any such slip and say so; a green suite on the wrong tree is a fabricated result.
- **Merging is not publishing.** Before claiming a site or deploy update, prove a deployer
  exists: a CI workflow, a git-linked hosting project (a Vercel `link: null` plus deployments
  carrying no commit sha = manual CLI uploads only), or hosting enabled (`GET /repos/O/R/pages`
  → 404 = disabled). A merged docs PR with no linked deployer changes zero served bytes.
- **Credentials + a found project do not authorise a production write.** Knowing where the
  site lives and holding a valid token is not a documented deployment path. When no repo,
  KB or runbook defines the artifact set and the deploy would publish more than the audited
  diff, report "merged, site pending external deployment" and hand the user the decision
  instead of inventing a deploy — and never let a merge imply a live change.
- **A frozen-lockfile failure on a dependency-bot PR is the lockfile, not the bump.** On
  bun/pnpm/yarn repos the bot edits `package.json` and leaves the lockfile alone, so the
  install step dies with `lockfile had changes, but lockfile is frozen` and every later
  step (typecheck, tests) is skipped. The red check reads as a compatibility failure it
  never tested, so say which steps did not run. Repair: run the installer on the branch,
  commit the lock diff, push to the bot's branch, then read the new head back. Check the
  lock diff holds only the bumped entries, so unrelated packages were not re-resolved.
- **Same change mirrored across repos/forks: compare TREES, not titles or SHAs.** When the
  same PR appears in an upstream repo and one or more forks/siblings, a different head SHA
  can still be a byte-identical change. Prove it with the tree hash
  (`git rev-parse <head>^{tree}`) and file hashes — equal trees mean one review covers all,
  and the change must land in each repo or be synced. A per-repo head SHA alone tells you nothing.
- **A fork's CI can show "no checks reported" because the workflow never ran there.**
  `gh api repos/O/R/actions/runs --jq .total_count` = 0 with `actions/permissions.enabled=true`
  means the fork's Actions were never triggered (GitHub disables workflows in forks by default),
  not that the branch is clean. State the count; do not read an empty rollup as a pass.
- **A "partition"/split PR pair is atomic: reconcile both deletion sets against the base.**
  Two PRs that split one tree must have complementary, non-overlapping deletion sets whose kept
  unions re-cover the base; if one lands alone the repos sit in an inconsistent split. Flag the
  pair as one change with two merge points, and check the KIT/TEAM (or A/B) classification is
  backed by a real artifact — a body citing "per manifest" when no manifest uses those terms is
  an unsourced hand-assignment.
- **Stale handoff diff** → you review phantom code. Always re-diff live.
- **Trusting PR-body test counts** → false evidence a reviewer catches. Run it.
- **`gh pr diff` needs `--repo O/R`** when not inside a cloned repo context.
- **`gh pr review --approve` self-block** → use a comment, never a fake approve.
- **`python` missing from PATH** → use `./venv/bin/python` or `uv run`.
- **Unqualified test IDs** → class-qualify them (`TestClass::test_method`).
- **Editing a PR body you don't own** → only do it on your own account's PRs.
- **`gh pr comment --edit-last` REPLACES the comment body.** It edits your last
  comment in place; it does not append. So never write "Correction to my comment
  above/below" — after the edit nothing remains to point at. Rewrite the whole
  comment self-contained.
- **GitHub auto-cross-references — check the timeline before posting a pointer.**
  When another PR or issue names this one, GitHub adds a "referenced this" event to
  the timeline on its own. So a comment that says "this is already handled in #N" is
  redundant the moment #N already names this item. Check first:
  `gh api repos/O/R/issues/N/timeline --jq '[.[] | select(.event=="cross-referenced") | .source.issue.number]'`
  — if the PR you would name is in that list, the link is already visible in the
  thread. Comment only when it would otherwise be invisible.
- **One cross-reference comment per PR, not two.** Two tracking notes on the same
  PR read as two maps of one thing. Fold them into one, then delete the redundant
  one — list ids with `gh api repos/O/R/issues/N/comments --jq '.[] | "\(.id)
  \(.user.login) \(.body[0:40])"'`, delete your own with `gh api -X DELETE
  repos/O/R/issues/comments/<id>`.
- **Don't tie your mechanism to a peer's reproduction without checking the harness.**
  A comment claimed a peer's orphan-FD count "partly stemmed from" another writer;
  their harness ran against a temp database with no such process in it. Read what
  the reported repro actually runs before claiming it is your bug too — the
  retraction costs more than the claim was worth.
- **Prove red on the real base, not in prose.** Do not assert the old behaviour
  in the body. Swap the base version of the touched file into the working tree
  (`git show origin/main:<path> > <path>`), run the new tests, restore, and quote
  the exact failure. A test that never failed against the base can pass for the
  wrong reason, and a reviewer who runs it will find out.
- **Do not claim an unverified half.** When the repo's toolchain is missing
  locally (no zig, no rust, no pnpm), fix and test the surface you can execute
  and say in the body which surface you could not build. Never let a green local
  run imply the unbuilt half passes; drop it from the diff or flag it plainly.
- **Verify which artifact carries a cost before acting on it — or dismissing it.** "This
  ships with every install" is a claim about one specific surface: git metadata, an
  embedded/installed file, or reviewer attention. Measure the mechanism before agreeing or
  pushing back (grep how the file reaches the user, size the delta) and name the surface
  that pays. The fix often lands in a different artifact than the claim names — and when the
  named surface is right, the delta can still be too small to matter (hundreds of bytes in a
  multi-MB binary). Argue from the measurement, not from the instinct.
- **Writing into a live install: verify both ends by hash, and quote the restore path from
  a listing you read.** Prove the backup equals the pre-change source and the installed file
  equals the new source (`shasum` on both sides, `git show ref:path | shasum` as the
  reference), then state the rollback command from the real filenames — tooling flattens or
  renames copies (`_Users_name_.hermes_plugins_x___init__.py`), so a path you assembled from
  memory does not exist. An unverified restore instruction is worse than none, because it is
  followed at the worst moment.

## When a docs pass is the actual task

Sometimes the request is not "audit this PR" but "this text confused a reader,
fix the writing". The audit discipline still applies, scoped down:

- Verify the served/repo text live (API or curl), not a cached copy. Baseline
  the SHA before editing; read the result back from the API after pushing — a
  push that reports success but changes no served bytes is a failed push.
- Edit on a branch even for docs-only changes; commit with a message naming the
  pass (`docs: rewrite README in plain language`), not a vague `docs update`.
- Enumerate the reader-facing surfaces before editing: README, repo About line
  (`gh repo view --json description`), site HTML (often `index.html` in the repo
  root, served from the same repo), landing-page meta description. One branch,
  one PR, all surfaces — so the reviewer sees the whole pass in one thread.
- Copy in place when the asset lives in the same repo: a site rewrite is a
  normal file edit, no new repo or deploy step. Verify what is actually served
  with a cache-busted fetch before and after.
- Structure is not copy: in a page rewrite touch only text nodes, `title`,
  `meta description`, `og:title`. CSS classes, ids, anchors, asset references
  and the nav stay byte-identical or rendering breaks. Verify: HTML parses, all
  `#anchor` links resolve to existing ids, local serve returns 200 for the page
  and each referenced asset.
- Specific method names (Erlang/OTP, YAML, Apache-2.0) stay — introduced with
  one plain sentence each, not stripped.
- If the text sits in an open PR thread a human already judged, the
  only-condense-where-nobody-has-engaged rule applies to it too.

## References
- `references/verification-recipe.md` — copy-paste command sequence for a full
  pre-merge audit (live diff, main premise check, venv test run, body-claim
  verification, comment posting).
