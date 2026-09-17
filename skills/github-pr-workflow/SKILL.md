---
name: github-pr-workflow
description: "GitHub PR lifecycle: branch, commit, open, CI, merge."
version: 1.5.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(uv run python "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/git-credential-token.py")
    fi
  fi
fi
echo "Using: $AUTH"
```

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 2a. Before the fix: prove the finding is a defect, not the design

A fix is worth writing only when the behaviour is actually wrong. Clear one bar and write down which:

- **User-visible failure** — duplicate execution, wrong or lost data, a crash, a hang.
- **Written invariant violated** — name the document and quote the line.
- **Unintended behaviour proven** — a surface requests a resource that nothing needs.

Read the area's `AGENTS.md` and the user docs first, including any "do not fix this" list, and quote
the line that settles intent. An extra process, an extra connection, or two holders of one file is
usually the documented architecture; the mechanism is not the harm, so state both the mechanism and
the failure it causes, plus the falsifier that would show the behaviour is intended. When the change
lands on a design decision rather than a defect, it is a feature proposal for the maintainers, not a
patch — say so instead of shipping code.

## 2b. Prove the fix on the live system before the PR exists

Unit tests prove the function is right on the inputs you handed it. They do not prove it is reached when the bug happens, or that its inputs are populated then. For any fix that changes runtime behavior — process spawn/reap, file writes, routing, resolution chains, lifecycle — prove it on the running system first, and open the PR only after that run:

- **Load the artifact the real entry point loads.** Rebuild the bundle/binary the app actually imports (a stale build silently exercises the old code) and confirm your change is present in it.
- **Reproduce the original symptom, not a proxy for it.** Capture the process tree with parent PIDs, the listening ports, `lsof` on the contested file, and the record your decision reads.
- **Show the symptom is gone and nothing new appeared.** A quiet log is not evidence that a process stopped spawning.
- **Say in the PR body what the live run covered and what it did not.**
- **If the live run shows the fix does not work, do not open the PR.** Fix it first, or file the reproduction as an issue and say so. Withdrawing a PR after a reviewer has already spent time on it costs far more trust than the live run costs time.

## 3. Pushing and Creating a PR

### PR body register

Write the body as an evidence register, not an investigation diary:

- Open with one plain sentence describing the changed behavior.
- Separate root cause, changed paths, validation, and follow-ups.
- Use one row per fix area. Count each area once at its highest impact.
- Tie every row to a commit or path and a real test result. Label the exact head, environment, and any unverified surface.
- Separate included fixes from new requests, overlaps, and unresolved findings.
- Keep the body short enough to scan. Preserve test counts and the evidence boundary; cut search narration and repeated conclusions.

A reviewer must be able to identify the scope, proof, and remaining limits without reconstructing the author's investigation.

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

## 3a. Draft and ready: state semantics and transition rules

The whole platform contract for a draft pull request, from the pull-requests reference page
(https://docs.github.com/en/pull-requests/reference/pull-requests#draft-pull-requests):

- A pull request can be a draft from the first action: "When you create a pull request, you can
  choose to make it a draft pull request."
- "Draft pull requests cannot be merged". No exception or bypass is stated.
- Code owners are not automatically requested on a draft: "...and code owners are not automatically
  requested to review them."
- The documented purpose is work-in-progress sharing, not invisibility: "Drafts are useful when you
  want to share work-in-progress without formally requesting reviews."
- The ready transition is the code-owner request moment: "Marking a pull request as ready for review
  will request reviews from any code owners."

Conversion back to a draft is always available ("You can convert a pull request to a draft at any
time") and it re-locks the merge completely; the same how-to page states the effect, "No one can
merge the pull request until you mark the pull request as ready for review again." Subscribers stay
subscribed through the change, so draft state is not confidentiality. Both flips are documented in
"Changing the stage of a pull request": "Ready for review" sits in the merge box, "Convert to draft"
under the Reviewers sidebar, and `gh pr ready` is the CLI form.

**Not stated there:** whether checks or Actions run on a draft, and how draft state interacts with
branch protection, rulesets, required checks, or merge queues. Never write a claim about
draft-dependent CI or protection behaviour; read the live repository state. A ready state is not an
approval, a review verdict, or green CI, and a draft state is not proof the code is unreviewed.

### Entry state by contribution class

| contribution class | state at open | who opens it | when ready is allowed |
|---|---|---|---|
| Small fix in a repository we administer | Ready | the implementer, after the independent pre-post review passes | already ready; convert back to a draft if scope or evidence becomes unstable |
| Large change in a repository we administer | Draft | the implementer, after the pre-post review passes and the handoff receipt is complete | when the bounded slice, body, tests, and evidence are stable and the pre-ready review has passed; a byte or scope change repeats that review |
| Small contribution to a repository we do not administer | local branch and rendered draft while remote writes are off; a GitHub Draft once the exact bytes are approved or a bounded grant covers them | the contribution author; no fork push while remote writes are off | only when the approval or grant covers the ready transition and the current head has been re-read |
| Large or high-attention contribution to a repository we do not administer | local draft first, then a GitHub Draft; never opened ready | the contribution author; no unsolicited or competing-thread write | only by an approval or grant naming the exact repository and thread, with new-fact evidence and target rules satisfied |

Transition rules:

1. The stronger constraint wins: a large or high-attention item is a draft at entry, and a "small"
   label never defeats a high-attention signal.
2. A draft is not a review request. Ready is the only documented event that requests code owners.
3. Before marking ready, confirm the approval or grant covers that transition, the bytes are
   unchanged, the pre-ready review is PASS, and the live head is the intended head.
4. Any push, rebase, force-push, or fix creates a new head and voids the previous review; re-audit
   the new head.
5. A draft cannot merge. Merge approval is valid only for a current ready head.
6. When state, scope, authority, or a gate is ambiguous, stay in draft or blocked; never ready.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

## 6. Merge readiness: repair before rejection

Do not treat a PR that is not immediately mergeable as disposable. Separate the change from the branch state and the review findings:

1. Inspect the current diff, intent, tests, provenance, and dependency boundaries.
2. If the issue is mechanical and low-risk (rebase conflict, stale generated output, missing documentation link, formatting, a narrow test correction), repair it on the PR branch when authorized, then rerun the complete gates.
3. If the issue is a small semantic mismatch that can be resolved without inventing product policy, propose and apply the narrowest compatible adjustment, and explain it in a PR comment.
4. If the PR is deeply incompatible with current architecture, do not close or discard it silently. Leave a concrete maintainer comment identifying the conflicting current paths/invariants, the required rebase or redesign, the acceptance tests, and the next mergeable shape. Keep the PR open unless the project team closes it or it is genuinely superseded.
5. Re-fetch `origin/main` before deciding. A branch can become conflicting because another PR merged while it was under review.
6. Verify the updated head, checks, diff scope, and relevant live or generated artifact before reporting merge readiness.

A clean check result is not sufficient when the branch is stale. A conflict is a repair task first, not an automatic rejection. Never force-merge a branch whose behavior or provenance remains unverified.

### 6a. Stale branch, no force push: merge main in, never rebase

When a `--force` push is forbidden (or history must stay append-only), update a stale PR branch by
merging `origin/main` **into** the branch. The merge commit has the old head as an ancestor, so the
push is a plain fast-forward (`old..new`, no forced marker) and the PR's own commits survive. A rebase
would rewrite them and require a force push — refuse that when the instruction says no force push.

After the merge, restate the PR's scope as the three-dot diff `git diff --stat origin/main...HEAD`: it
should equal the PR's original file set with 0 deletions. If it shrank or grew, the merge changed the
review surface — investigate before pushing. Note in your report that the branch's copy of files
changed by main (e.g. `index.html`) moves to main's version; that is inherent to the update and does
not put those files in the PR diff.

A branch that is *textually* mergeable can still be *semantically* broken: git merges cleanly when two
sides add the same heading/identifier number, key, or enum value in different places. Check the merged
tree, not just `mergeable: MERGEABLE` — grep the merged file for duplicate `^## [0-9]+\.` headings,
duplicate keys, and duplicate enum members after the merge. Resolve by renumbering the *newer* side to
the next free value, and grep the whole tree for the old number (`§N`, `Section N`, `#N`, `path#anchor`)
to catch references that would become false. Run the repo gate on the merged tree *after* committing,
because fresh-clone/CI gates read committed refs and would otherwise validate the pre-fix tree.

## 7. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## 7. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
