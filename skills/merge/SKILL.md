---
name: merge
description: Use to merge a ticket's PR into the default branch and finish its tickets - one ticket's PR, a combined PR that holds several tickets' PRs, or the top PR of a stack. It merges the PR, checks that every smaller PR is inside it, closes those PRs with a comment, deletes their branches and local worktrees, and moves every ticket to Accepted. With "watch", it first waits until QA moves every ticket to Ready for Merge (Jira checked once a minute), then merges at once so others can deploy. prod-handoff starts the watch after a prod deploy. Examples - "merge 9442", "merge the OP Agent stack and clean it up", "watch for Tami to move 41048 to ready for merge, then merge it", "I just merged the top ticket in the stack for OP Agent", "the stack is merged, clean up the other branches". Takes a PR URL or number, a ticket key, or a feature name such as "OP Agent", plus extra ticket keys whose commits ride in the PR without a PR of their own.
---

# Merge a PR and finish its tickets

## Overview

Three shapes, one flow:

| Shape | What it looks like | Smaller PRs |
|---|---|---|
| Single | One ticket, one PR into the default branch | None |
| Combined | One PR (for example `bug/combined/fe-bugs-2026-11-06`) that merges several tickets' branches. The title lists the keys, the body has a table of the tickets and their PRs. The tickets' own PRs stay open | The tickets' own PRs |
| Stack | Each PR targets the branch of the PR below it. Only the top PR merges | The lower PRs |

The flow: (watch mode only) wait for Ready for Merge, merge the main PR, check that every smaller
PR is inside it, close the smaller PRs and delete their branches, move every ticket to Accepted.

Merging, closing PRs and deleting branches are hard to undo. The merge checks in step 3 and the
safety gate in step 4 are the point of this skill. Never skip them.

## 1. Find the main PR, the smaller PRs and the tickets

| Input | How |
|---|---|
| PR URL or number | `gh pr view <pr> -R <owner/repo> --json number,title,body,url,state,baseRefName,headRefName,headRefOid` |
| Ticket key | `gh pr list -R <owner/repo> --state open --search "WORK-<n>" --json number,title,baseRefName,headRefName`. A ticket that is in a combined PR finds both its own PR and the combined one: the combined PR is the main PR |
| Feature name | Look in the user's open PRs, then recent merges (below) |
| Nothing | The PR that this session already worked on. If there is none, ask |

```bash
gh pr list -R <owner/repo> --author @me --state open --limit 100 \
  --json number,title,baseRefName,headRefName,headRefOid
gh pr list -R <owner/repo> --author @me --state merged --limit 20 \
  --json number,title,baseRefName,headRefName,mergedAt,mergeCommit
```

Find the shape:

- **Stack**: another PR targets the main PR's branch, or the main PR targets a branch that is not
  the default branch. The top PR is the one no other PR in the chain targets. Walk down by
  `baseRefName`: follow each base to the PR whose head is that branch, until you reach a PR that
  targets the default branch. If the top PR was retargeted to master before the merge, match by
  the ticket name or feature words in the titles, and confirm with the safety gate.
- **Combined**: the title holds more than one ticket key, or the body lists other PRs (`#<n>`) for
  the tickets. The smaller PRs are the PRs in that list. Confirm each one is open and its title
  holds one of the keys.
- **Single**: neither. No smaller PRs.

Do not include PRs that are not part of it, such as a proof-of-concept PR ("DON'T REVIEW") that
also targets master. Name them in the report and leave them open.

**Tickets**: every key in the main PR's title and in each smaller PR's title, plus the keys the user
named. A key that has no PR (`gh pr list --state all --search "WORK-<n>"` is empty) may ride
inside as a commit. Find it with `git log --oneline origin/<main head branch> --grep=<KEY>`. If it
is inside, it moves with the others in step 6. If it is not, report it and do not move it.

If the main PR is already merged, go to step 4.

## 2. Watch for Ready for Merge (watch mode only)

Run this step when the request says to wait for QA (for example from `prod-handoff`, or "watch for
Tami to move it to ready for merge"). Otherwise go to step 3.

Merge as soon as QA approves: other people wait to deploy until this PR is in master. Start the
watch in the background, from this skill's folder. It checks Jira once a minute, costs no tokens
while it waits, and runs up to 2 hours per start:

```bash
<skill folder>/watch-ready.sh 7000 <KEY1> <KEY2> ...
```

Run it with the Bash tool and `run_in_background: true`, `timeout: 7200000`. You are notified
when it ends. It prints one JSON line:

| Result | Action |
|---|---|
| `ready` (exit 0) | Every ticket is in Ready for Merge (or already Accepted). Go to step 3 at once. Do not ask the user |
| `timeout` (exit 4) | No change yet. Start the same watch again. Keep doing this until another result comes |
| `stopped` (exit 3) | A ticket left the wait (for example QA sent it back). Do not merge. Tell the user which ticket is in which column, and send the notification below |

The watch waits while tickets are in Ready for Prod or On Prod. In a combined PR, QA can move the
tickets one at a time; the watch waits for all of them.

Tell the user that the watch runs, which tickets it waits for, and that it merges by itself.

The approval to merge comes from the request that started the watch. When the watch reports
`ready`, do not ask again.

## 3. Merge the main PR

Read its state:

```bash
gh pr view <MAIN> -R <owner/repo> \
  --json baseRefName,reviewDecision,mergeable,mergeStateStatus,statusCheckRollup
```

Outside watch mode, ask the user before you merge, unless they already said to merge in this
request. Show the review decision, whether it is mergeable, and the checks that failed or are
pending.

Deploy workflows that were never approved show with no conclusion and make the state `UNSTABLE`.
That alone does not block the merge.

Do not merge when `reviewDecision` is not `APPROVED`, `mergeable` is not `MERGEABLE`, or a PR
check (for example `DefaultPR`) failed. `mergeable` can read `UNKNOWN` for a few seconds after a
push to master: read it again after 10 seconds. If it still blocks, report it, send the
notification below, and stop. For a conflict with master, say that `ticket-flow:catch-up` fixes it,
and that its push starts a new pipeline.

Merge with a squash. For a stack, retarget the top PR first. A squash merge into the branch below
would leave master without the stack.

```bash
gh pr edit <MAIN> -R <owner/repo> --base <default>   # stack only, when it targets a stack branch
gh pr merge <MAIN> -R <owner/repo> --squash
gh pr view <MAIN> -R <owner/repo> --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid)"'
```

## 4. Safety gate: is every smaller PR inside the merged PR?

Skip this step for a single PR.

A squash merge makes a new commit, so `compare` shows the smaller branches as "diverged". Do not
use it. Do not use `gh pr view --json commits` either: it returns at most 100 commits, and a
long stack has more, so a head commit past the 100th reads as missing.

Fetch the main PR's head (it survives a deleted branch) and test each smaller PR's head with git:

```bash
git fetch origin pull/<MAIN>/head:refs/remotes/origin/pr-<MAIN>
git merge-base --is-ancestor <headRefOid> origin/pr-<MAIN> && echo in || echo MISSING
```

If one smaller PR is missing, stop. Report which PR is missing and do not close anything. That
PR has commits that never reached master.

## 5. Close the smaller PRs and delete the branches

For a single PR, do only "Local worktrees" at the end of this step. For a stack, work from the top down. Then no PR is left targeting
a branch that is gone.

```bash
gh pr close <N> -R <owner/repo> \
  --comment "Closing. This change was merged to master as part of #<MAIN> (squash merge <short merge sha>)."
```

Write the comment in plain words. Do not use em dashes.

Delete each branch through the API. `gh pr close --delete-branch` can close the PR and still
leave the remote branch, for example when it runs inside a git worktree:

```bash
gh api -X DELETE "repos/<owner/repo>/git/refs/heads/<branch>"
```

GitHub usually deletes the main PR's branch on merge. A `422 Reference does not exist` means
the branch is already gone. That is not an error. Confirm none are left:

```bash
git ls-remote --heads origin | grep -E "<branch1>|<branch2>|..."
```

**Local worktrees.** Remove the local worktree of the main PR's branch and of each smaller PR's
branch (also for a single PR). Run it from the repo's main checkout, not from inside a worktree
you remove:

```bash
aikit repo worktrees list
```

For each entry whose `branch` is one of these branches:

1. Check for work that is not on GitHub: `git -C <path> status --porcelain` must be empty, and
   `git -C <path> log --oneline @{u}..` must print nothing (or the branch has no upstream because
   it is merged and deleted, and `git -C <path> log --oneline origin/<default>..HEAD` shows only
   commits that are inside the merged PR, which the safety gate in step 4 checked).
2. If both are clean, remove it. This also deletes the local branch:

   ```bash
   aikit repo worktrees remove <name> --yes
   ```

3. If not, leave it and name it in the report with what is left in it. Never discard changes.

A worktree outside `.aikit/worktrees/` (for example under `.claude/worktrees/`) needs
`--dir <that folder>`. Leave worktrees of branches that are not part of this merge.

## 6. Move the tickets

Check each ticket's status:

```bash
aikit jira issues get <KEY> --fields status
```

Tickets in `Ready for Merge` move with the "Code Merged, Set as Accepted" transition. Use the ID,
because `--to "Accepted"` is ambiguous (two transitions lead to Accepted):

```bash
aikit jira issues transitions apply <KEY1> <KEY2> ... --transition-id 351
```

The Jira API sometimes closes the socket. A result with `"retryable": true` or "socket
connection was closed" is not a refusal: retry that key once, then read the status again.

If 351 fails for another reason, run `aikit jira issues transitions list <KEY>` and pick the
transition named "Code Merged, Set as Accepted". A ticket in an earlier column (for example
`On Prod`) moves forward one hop at a time. Report a ticket that has no forward path, and do
not force it.

## 7. Report and notify

Lead with the result.

```
Merged #9442 into master (squash 5a8cf69). Check: it holds the head commit of each ticket's PR.

1. Closed with a comment that points to #9442: #9426, #9428, #9431, #9434, #9435, #9439
2. Deleted the 6 branches. GitHub had already deleted the #9442 branch. Removed 7 local worktrees.
3. Jira: WORK-41048, WORK-41060, WORK-41064, WORK-41065, WORK-41067, WORK-41070 moved from Ready for Merge to Accepted.

Not touched: #9001 (proof of concept, still open). Close it too?
```

In watch mode, also send a macOS notification when the merge is done, or when the watch or the
merge stopped:

```bash
aikit notify send --type update --title "Merged #9442" --body "6 tickets moved to Accepted"
aikit notify send --type failure --title "Merge stopped: #9442" --body "WORK-41064 went back to In Progress"
```
