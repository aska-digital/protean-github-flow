The GitHub workflow skill pack: issue triage, issue-to-PR, PR lifecycle, PR audit, and upstream-contribution procedures.

# protean-github-flow

The GitHub workflow ingredient of the Protean Kit distribution. It carries the
five procedures that take a repository from an inbound issue to a verified,
reviewed pull request.

## Do you need this?

ROLE: The GitHub workflow skill pack. Five procedures take a repository from inbound issue triage to a verified, reviewed pull request, including fork upstream contribution.

USE WHEN:
- An inbound issue must be triaged and then carried to a verified PR, starting at `skills/github-issues/SKILL.md`.
- A merge decision needs the formal audit in `skills/github-pr-audit/SKILL.md`, which reads the live head and keeps an evidence register.
- A fork PR must be reworked or reopened upstream with neutral publication attribution.

SKIP WHEN:
- The forge is not GitHub. Every procedure assumes issues, branches, pull requests, and CI.
- The need is the human-facing draft review page or the pipeline itself. Those live in `protean-drafts` and `protean-doctrine`, which this manifest only recommends.

## What it installs and where

| Path | Contents |
|---|---|
| `skills/github-issues/` | issue triage and creation, with templates |
| `skills/github-issue-to-pr/` | carry an issue to a verified pull request |
| `skills/github-pr-workflow/` | branch, commit, open, CI, merge, with references and templates |
| `skills/github-pr-audit/` | live-head audit, evidence register, formal review protocol |
| `skills/upstream-contribution-pr/` | rework or reopen a fork pull request upstream |
| `gates/protean-github-flow/` | the two gates and the leak blocklist |

The GitHub workflow pack installs five skills. The installed paths are given by
this ingredient's manifest, which is authoritative; the source layout of any
private working tree is not a public contract.

## Install

```bash
bash install.sh --target <dir>
bash install.sh --target <dir> --dry-run
```

Bash and coreutils only, zero network calls, every written path printed, and no
`--target` means no run. A dry run writes nothing.

Installs alone with this command, resolving only its required dependencies listed
in its manifest entry. Optional relationships are reported, not fetched.

## Requirements and recommendations

Requires none. Recommends `protean-drafts` (the review page every draft is shown
in) and `protean-doctrine` (the pipeline the procedures operate inside).

## Use

Each installed skill states when it applies and the exact commands it runs. Start
with `skills/github-issues/SKILL.md` for inbound triage, or
`skills/github-pr-audit/SKILL.md` before any merge decision. The audit procedure
reads the live head, never a pasted snapshot.

Committing on a repository the team owns: the procedures use the role codename
identity, set per command and never written into git configuration. On any
repository the team does not own, the poster's own identity is used.

## Gates

| Gate | Command (declared) |
|---|---|
| internal-name gate | `python3 gates/protean-github-flow/check-internal-names.py .` |
| skill frontmatter | `python3 gates/protean-github-flow/check-skill-frontmatter.py .` |

The frontmatter gate enforces that every shipped skill declares a name, a
description, a version, and the MIT license, and that no `author` field names a
person: a rewritten attribution reads "the Protean publication".

## Attribution in the pack

Every shipped skill was re-read for attribution. Two of the five carry the
neutral engine authorship already and were left unchanged. Three were rewritten:
one carried a team name fused with a role name, one carried a personal name and
handle, and one routed a worked example through a personal handle. Those now
carry the neutral attribution line, and the worked examples use documented
placeholders.

## Offline and cache behaviour

Used through the composer, this ingredient is fetched once from its pinned tag
and reused from a content-addressed cache keyed by commit SHA. `--offline`
performs zero network calls and fails closed when the cache entry is absent.

## Limits and open items

The pack ships procedure, not automation: it invokes the authenticated GitHub CLI
and assumes the operator holds the credentials. It names no account, no host, and
no repository of its own. Membership of this pack in the version 1 ingredient set
is an open item recorded by the manifest's own notes.

## License

MIT. The committed `LICENSE` file is authoritative.
