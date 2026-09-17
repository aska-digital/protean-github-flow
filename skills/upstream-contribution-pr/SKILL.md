---
name: upstream-contribution-pr
description: "Rework/reopen a fork PR against an upstream repo."
version: 1.3.0
author: the Protean publication
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, pull-request, fork, upstream, git-worktree]
---

# Upstream Contribution PR (fork → upstream repo)

Managing a PR raised from your fork of an upstream repository. Covers reworking a PR to a narrower scope on a
maintainer's direction, and the GitHub reopen blocker that follows a head-branch
rewrite.

## Active contribution stance

Contribution is not reactive. When the team pulls from, ingests, or works with an open-source repository, every member actively looks for bugs, improvements, missing features, or documentation gaps that would substantiate a PR or issue. The obligation:

1. **Identify** — during ingestion, capability audit, or any work touching external repos, flag specific issues with file:line evidence and a clear fix description.
2. **Draft** — prepare a GitHub PR or issue following the project's contribution conventions (labels, templates, commit style, CLA).
3. **Review** — show the draft to the user for approval before pushing. The team does not self-approve
external contributions.
4. **Track** — record contribution status in the project awareness log: `proposed → submitted → merged/rejected`.

Repos we depend on get improvements we identify, not just references we index. This is a standing duty, not optional side work.

## Posting shape: an external contribution opens as a draft

The entry state for work on a repository we do not administer is a draft, in two layers:

1. **Local draft.** While remote writes are off, the deliverable is a local branch, a commit, a test
   run, and a rendered draft. No remote write of any kind happens, including a push to a fork.
2. **GitHub Draft.** Once the exact bytes are approved, or a bounded grant covers them, open the
   pull request as a draft: `gh pr create --draft ...`, or `"draft": true` on the REST body.

The ready transition is a separate action, not a second attempt at the same one:

- Marking ready (`gh pr ready`, or "Ready for review" in the merge box) is the documented moment
  code owners are requested. Nothing requests them while the pull request is a draft.
- The approval or grant must cover that transition explicitly. An approval that covers draft
  creation alone does not cover it; the ready step needs its own approval or a grant that names it.
- A draft cannot be merged, and converting a ready pull request back to a draft re-locks the merge
  until it is marked ready again. Keeping the change as a draft is the correct state while it is
  still being fixed or discussed.
- A new head voids the prior review. Re-read the live head before the ready transition and before
  any merge-side recommendation.

Not stated where the draft rules are documented: whether checks or Actions run on a draft, and how
draft state interacts with branch protection, rulesets, or required checks. Read the live repository
state for both, and never write a claim about draft CI behaviour.

A ready state is not an approval and not green CI. An upstream merge is never autonomous.

## Reopen after force-push is BLOCKED (platform rule)

GitHub refuses to flip a CLOSED PR back to open once its head branch was
force-pushed or recreated. `gh pr reopen` fails with `Could not open the pull
request`; the REST PATCH returns HTTP 422 `state cannot be changed. The
<branch> branch was force-pushed or recreated.` Mechanism: a rewritten head is
a different branch identity; GitHub will not reopen a closed PR on it.

Rule: expect this whenever the scope fix requires rewriting the head branch's
history. Do NOT keep retrying reopen. The escape is a NEW PR from the same
already-pushed head branch:

```bash
gh pr create --repo <upstream> --head <fork>:<branch> --base main \
  --title "..." --body "$BODY"
```
- New PR body references the original PR number and the reviewer comment URL
  (why it is split/renamed), plus a `Supersedes: <old-pr-url>` line.
- Leave a redirect comment on the old (closed) PR pointing at the new number.
- Verify the new PR: `state=OPEN`, `mergeable`, and `changedFiles`/diffstat list
  ONLY the intended files.

## Scoped-rebuild procedure (strip a feature per reviewer direction)

When asked to land just one half of a combined PR:

1. Fetch fresh upstream `main`; record its head. `git merge-base <pr_head>
   <upstream_main>` tells how stale the branch is.
2. Conflict probe BEFORE committing to a path: does upstream main still contain
   the touched files unchanged from the branch base? If `git diff --stat
   <base> <upstream_main> -- <files>` is empty, saved diffs apply cleanly onto
   current main; a NEW test file main does not yet have is a clean add, not a
   conflict. If those files moved on main, rebase instead.
3. Extract the in-scope changes file-by-file:
   `git diff <commit>~1 <commit> -- <kept-file>`; omit the file whose hunk IS
   the dropped feature. Rewrite the test file to drop that feature's test(s)
   and its docstring bullets (a test file can carry both halves — edit it, don't
   just copy).
4. Rebuild on current main, not the old base; squash to ONE commit. Verify
   `git show --stat HEAD` lists only intended files. Keep commit author = the
   contribution identity.
5. Re-scope title + body: delete the dropped half, describe the kept half alone
   with reproduction + test-evidence kept honest. The maintainer read the old
   body; stale claims about the removed feature will be caught.
6. Force-push the head branch (same name), then reopen → expect the 422 block
   → go to the NEW-PR path.

## Before opening or reopening: prove the fix on the running system

A fix that changes runtime behavior needs a live run before it becomes a public PR, and a
withdrawn PR costs more trust than the run costs time. For process spawn/reap, file writes,
routing, resolution chains, and lifecycle changes: rebuild the artifact the real entry point
loads (a stale build tests the old code), reproduce the original symptom, and capture the
process tree with parent PIDs, the listening ports, and `lsof` on the contested file. Full gate:
`github-pr-workflow` §2b; auditor-side version: `github-pr-audit` §6d. If the run shows the fix
does not work, fix it before publishing, or file the reproduction as an issue instead.

## First: prove the finding is a defect, not the documented design

Before writing any patch, clear one bar and name it in the issue: a user-visible failure (duplicate
execution, wrong or lost data, a crash), a written invariant violated (quote the document and line),
or unintended behaviour proven (a surface requests a resource nothing needs). Read the area's
`AGENTS.md` and user docs, including any "do not fix this" list, and quote the line that settles
intent. Process and topology findings are the trap: an extra process, an extra connection, or two
holders of one file is usually the architecture, and the mechanism is not the harm — state the
mechanism, the failure it causes, and the falsifier that would show the behaviour is intended. A
change that rests on a design decision is a proposal for the maintainers, not a fix. Author-side
gate: `github-pr-workflow` §2a.

## Before writing anything: prove the bug is still live on upstream main

The most expensive failure here is a correct fix for an already-fixed bug. A stale local checkout
makes a landed fix look like a live defect: a proposed one-line patch was written against a tree
157 commits behind `origin/main`, where the maintainer had already replaced the offending
allow-list (`git log -S "<symbol>" -- <file>` names the landing commit) — merging it would have
re-added the deleted table and regressed the newer, better fix.

Cheap checks, in order:

1. `git fetch origin main` (retry on a transient HTTP 429; a failed fetch leaves `origin/main`
   stale and every "behind N" number wrong).
2. `git log -S "<symbol-or-string>" --oneline -- <file>` — if the landing commit is an ancestor of
   `HEAD`, stop: nothing to fix.
3. Read the CURRENT file, not your memory of it: `git show origin/main:<file> | grep -n <pattern>`
   or fetch it raw. Line numbers and even whole functions move between revisions.
4. `gh search issues` AND `gh search prs` for the symptom before opening anything. A duplicate PR
   gets closed (`action=closed-duplicate`) and a competing second PR for a one-line fix is noise.

## Validate someone else's PR before endorsing or rebasing it

`mergeable: UNKNOWN` is just GitHub still computing; re-query. `CONFLICTING`/`DIRTY` means it needs
a rebase, and a rebase is not always mechanical:

```bash
git fetch origin pull/<n>/head:pr-<n>
git worktree add --detach /tmp/pr<n>-check origin/main
cd /tmp/pr<n>-check && git merge --no-commit --no-ff pr-<n>   # then read the conflict markers
```

Read both sides of every conflict. A shifted-neighbourhood conflict (adjacent keys added upstream)
resolves mechanically; a conflict where the PR's ANCHOR was deleted upstream does NOT — check
`grep <anchor-test-name>` on main and find where that test/class MOVED (root-level `tests/*.py`
modules are the common new home for template/invariant tests). Re-inserting a test beside a deleted
anchor leaves a docstring referencing something that no longer exists.

Verify the PR's assertion actually DISCRIMINATES: run it against the artifact as shipped AND with
the PR's change, and show the two differ. A test that passes either way is not evidence.

To hand the author a ready resolution, do it in the scratch worktree and report the result in a PR
comment — do not push to someone else's branch, and do not open a competing PR without asking them
first in that thread.

### When the author says "rebased, verified, nothing needed from you"

That is a self-report. Re-fetch and check it before agreeing:

```bash
git fetch origin pull/<n>/head:pr-<n>-rebased && git worktree add --detach /tmp/pr<n>v pr-<n>-rebased
cd /tmp/pr<n>v
git diff --stat origin/main...HEAD    # three dots = the PR's OWN change vs its merge base
git diff --stat origin/main..HEAD     # two dots  = also shows main's newer commits, reversed
```

The three-dot view is the PR. If the two-dot view is much larger, the branch is based on an OLDER
main — harmless for review, but it is the stale-branch shape CONTRIBUTING warns about for squash
merges, and it is a genuinely useful thing to tell the author (they cannot see it from GitHub's
`MERGEABLE`). Re-run their exact commands and reproduce their counts; then re-run the
discrimination check yourself (flip the value the fix depends on, confirm the test fails, restore).
Report all three: numbers reproduced, discrimination reproduced, plus anything they did not mention.


## Worktree staging — never mutate the live checkout

Test/build contribution branches in a git worktree off the LIVE main checkout
(the tree running services import from), never on the live working tree. Use
`scripts/run_tests.sh` (the repo's own runner), not bare pytest.

```bash
git worktree add -b fix/x /tmp/<name>-wt <upstream_main>
cd /tmp/<name>-wt
# ... apply diffs, copy tests, run scripts/run_tests.sh, commit
```

## Pitfall: a failed `cd` leaves later git ops in the WRONG tree

If `git worktree add -b <name>` fails (target branch name already exists) it
creates no worktree — and the next `cd /tmp/<name>-wt` ALSO fails, silently
leaving every following command running in the session's cwd, which is the LIVE
checkout. `git apply` then rewrites production files with no error. This is how
worktree staging dirties a live tree.

Guards (before applying anything):
- Make the target branch name free first: `git branch -D fix/x` (after checking
  it is stale/unused) or pick a fresh name; verify `git branch --list 'fix/x'`
  is empty.
- After `cd`, confirm you are inside the worktree (`git rev-parse
  --show-toplevel` or `pwd`) before applying/committing.
- Verify live checkout is clean with `git status --porcelain` (empty) before
  AND after. Revert accidental dirt immediately: `git checkout -- <file>`.
- `git apply --check <diff>` before `git apply <diff>`.

## Prove your tests are red on base, and that failures are not yours

- Red on base: `git stash push -- <source file>` inside the worktree, re-run the test file, capture
the failure, `git stash pop`. When the fix ADDS the function under test the base failure is an
`AttributeError` rather than an assertion — say so plainly in the PR body instead of implying an
assertion-level red.
- A broad run will surface pre-existing failures. Do NOT attribute them to your change by
reasoning that your diff "cannot affect" them: run the SAME failing files in the unmodified
checkout and compare the failure set. Identical counts and file lists on base is the proof; it is
usually environmental (launchd state, plugin discovery, sqlite, collection-timeout).

## Cleanup after the branch is pushed

```bash
git worktree remove /tmp/<name>-wt --force && git worktree prune
git branch -D fix/x
```
Confirm `git worktree list` shows only the live checkout (plus any worktree that was already there
before you started — leave that one alone) and `git status` on it is clean. Leave the live tree
byte-identical to how you found it.

Keep the pushed branch when a review round is plausible (a review invite, a maintainer request for
changes): the PR already holds the commits, and `git fetch fork <branch>` reconstructs a worktree if
it is deleted anyway.
