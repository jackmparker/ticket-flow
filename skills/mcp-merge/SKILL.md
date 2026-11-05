---
name: mcp-merge
description: Use when asked to merge the user's approved PRs in the observepoint-mcp repo. Examples - "merge my reviewed MCP tickets", "merge the approved MCP PRs", "get the MCP tickets merged", "run mcp-merge". It finds the user's approved MCP PRs, makes all required checks pass (it fixes failures and conflicts itself), squash-merges them one at a time, waits for each deploy, catches the next PR up with main, and moves each ticket to Accepted. A PR number or ticket key narrows the set.
---

# Merge the approved MCP PRs

## Overview

Repo: `observepoint/observepoint-mcp`. Default branch: `main`. Local clone:
`~/ObservePoint/observepoint-mcp`.

For each approved PR of the user: make the required checks pass, squash-merge it, move the
ticket to Accepted, wait for the deploy, and catch the next PR up with main. Repeat until no
approved PR is left.

The user asked for the merges when they ran this skill. Do not ask again before a merge, a
push, a conflict fix or a Jira move. Stop and ask only where a step below says so.

Two facts drive the order:

1. A merge to `main` starts the CircleCI `deliver` pipeline. It deploys staging, then
   production. A second merge while `deliver` runs is a push to a branch that a deploy runs on.
   CircleCI then marks the older pipeline's jobs `not_run`, and that change never reaches
   production (this happened to #341). So merge one PR, wait for its `deliver` pipeline, then
   merge the next.
2. The repo allows squash merges only. After each merge, the other PRs are behind `main`. Catch
   each one up and wait for its new checks before you merge it. Never merge on checks from an
   older head commit.

## 1. Find the PRs

```bash
gh pr list -R observepoint/observepoint-mcp --author @me --state open --limit 100 \
  --json number,title,url,headRefName,headRefOid,isDraft,reviewDecision,mergeStateStatus
```

Keep a PR when all of these are true:

- `reviewDecision` is `APPROVED`.
- `isDraft` is false.
- The title has a ticket key (`WORK-<n>`).
- The title does not start with "DON'T REVIEW".

Do not touch PRs by other authors or by dependabot. If the user named a PR or ticket, keep only
that one.

Read each ticket's status and summary:

```bash
aikit jira issues get <KEY> --fields status,summary
```

If the list is empty, report the user's open MCP PRs and their `reviewDecision`. Stop.

Tell the user the PRs and the order before you start (step 2).

## 2. Pick the order

1. `CLEAN` first. These can merge now.
2. Then `BLOCKED` (a required check failed or still runs), `BEHIND` and `DIRTY` (conflicts).
3. Inside a group, the oldest PR number first.

`UNKNOWN` means GitHub still computes the state. Query the PR again after 30 seconds. It is not
a blocked PR.

## 3. Make the required checks pass

Read only the checks that branch protection requires:

```bash
gh pr checks <N> -R observepoint/observepoint-mcp --required
```

If this list is empty, read the required jobs from `.github/required-checks.json` on the PR head.

| Result | Action |
|---|---|
| All `pass`, and `mergeStateStatus` is `CLEAN` | Go to step 4 |
| Any `pending` | Wait in the background: `gh pr checks <N> -R observepoint/observepoint-mcp --required --watch --interval 60`. Then read the result again |
| Any `fail` | Fix it (below) |
| `mergeStateStatus` is `BEHIND` or `DIRTY` | Catch up (step 6), then come back here |

### Fix a failed check

Get a worktree on the branch, as in the `catch-up` skill, step 2. Read the failed job log:

```bash
gh run view <run-id> -R observepoint/observepoint-mcp --log-failed | tail -200
```

Sort the failure into one of two kinds:

- **Caused by the PR.** Examples: `check` (format, lint, typecheck, tests, repo rules),
  `coverage`, the generated SDK diff, `audit` on a dependency the PR adds. Fix the code in the
  worktree. Run the full gate locally:

  ```bash
  DESCRIPTION_CHECK_BASE=origin/main npm run check
  ```

  When it passes, commit with a short message that names the ticket key, and push.
- **Caused by the environment.** Examples: `contract`, `write-sweep` or `oauth-flow` failing on
  the staging API, a timeout, or a missing secret. Rerun the failed jobs once:

  ```bash
  gh run rerun <run-id> -R observepoint/observepoint-mcp --failed
  ```

  If it fails again and the PR did not change what that check tests, stop work on this PR.
  Report it and go to the next PR.

After a push, wait for the new checks on the new head commit. Then read `reviewDecision` again.
If it is no longer `APPROVED` (the push dismissed the approval), do not merge. Report it and go to
the next PR.

Limit: 3 fix rounds per PR. After the third, stop work on this PR, report the failing check and
go to the next PR.

## 4. Merge

```bash
gh pr merge <N> -R observepoint/observepoint-mcp --squash --delete-branch
```

The repo does not delete branches on merge, so keep `--delete-branch`.

Remove the worktree for the merged branch, if you made one:

```bash
git -C ~/ObservePoint/observepoint-mcp worktree remove <worktree>
```

## 5. Move the ticket to Accepted, then wait for the deploy

Move the ticket as soon as the merge succeeds. Use the transition ID, because two transitions
lead to Accepted and `--to "Accepted"` fails as ambiguous:

```bash
aikit jira issues transitions apply <KEY> --transition-id 431
```

If 431 is not available, run `aikit jira issues transitions list <KEY>` and use "Code Merged, Set
as Accepted" (351) or "Accepted" (431). If neither is in the list, report the ticket status and
do not force it. Never pick `Closed`, `Nevermind` or any backward move. A ticket already in
Accepted needs no move.

Find the `deliver` pipeline for the merge commit:

```bash
gh pr view <N> -R observepoint/observepoint-mcp --json mergeCommit --jq .mergeCommit.oid
aikit circleci pipelines list --project gh/observepoint/observepoint-mcp --branch main --limit 3
```

Pick the item whose `commit_sha` is the merge commit. Take the `deliver` workflow ID from
`workflows[]`. If it is not there yet, list again after 30 seconds.

Wait in the background:

```bash
aikit circleci workflows wait <workflow-id> --interval 60 --timeout 3600 | tail -1 \
  | jq -c '{reason: .emission_reason, status: .workflow_status, notDone: [.jobs | to_entries[] | select(.value != "success") | "\(.key): \(.value)"]}'
```

While it runs, do step 6 for the next PR. A push to a feature branch does not touch the `main`
deploy. Do not run `/deploy` or start a `stage_branch` pipeline for this repo while `deliver`
runs.

| Final status | Action |
|---|---|
| `success` | The change is on production. Go on to the next merge |
| `failed`, `error`, `canceled` | Stop all merges. Report the failed jobs and their URLs. `main` is broken, and the next merge would deploy on top of it |
| `on_hold` | A job waits for approval. Tell the user and wait |
| `reason` is not `terminal` (timeout) | Check `aikit circleci workflows get <workflow-id>`. If it still runs, wait again |

## 6. Catch up the next PR

Follow the `catch-up` skill, steps 1 to 3, with `main` as the default branch:

```bash
git -C ~/ObservePoint/observepoint-mcp fetch origin main <branch>
# worktree on <branch>, then:
git -C <worktree> merge --ff-only origin/<branch>
cd <worktree> && aikit git backmerge --base origin/main
```

One difference from `catch-up`: on `conflict`, resolve the conflicts yourself. Do not ask. Read
both sides, keep the intent of `main` and of the PR, and then run
`DESCRIPTION_CHECK_BASE=origin/main npm run check`. Commit the merge only when the check passes.
If you cannot tell what one side meant, stop work on this PR and report the files.

Push with `git push origin <branch>`. Never rebase and never force-push.

Then go back to step 3 for this PR.

## 7. Repeat

Go back to step 1 after each merge, and list the PRs again. A reviewer can approve another PR
while you work. Stop when no approved PR is left, or every one left is blocked.

## 8. Report

Lead with what merged.

```
Merged 2 MCP PRs. Both are on production.

1. #368 WORK-41024: merged, deliver pipeline 568 passed. Ticket moved from Ready for Staging to Accepted.
2. #369 WORK-41030: caught up with main, fixed a lint failure (a1b2c3d), merged, deliver pipeline 569 passed. Ticket moved to Accepted.

Not merged:
- #370 WORK-41100: `write-sweep` failed twice on a staging timeout. The PR does not touch writes.

Next: rerun `write-sweep` on #370 when staging is back.
```

Name every fix commit you pushed, and every PR you left open with its blocking check.
