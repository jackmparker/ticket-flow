---
name: stack-cleanup
description: Use to merge the top PR of a stacked PR chain, or after it is merged, to close the lower PRs, delete their branches and move every ticket in the stack to Accepted. Examples - "merge the OP Agent stack and clean it up", "I just merged the top ticket in the stack for OP Agent", "the stack is merged, clean up the other branches", "delete the other branches and leave a comment pointing to the last PR". Takes a PR URL or number, a ticket key, or a feature name such as "OP Agent", plus extra ticket keys whose commits ride in the stack without a PR of their own.
---

# Merge and clean up a PR stack

## Overview

In a stack, each PR targets the branch of the PR below it. Only the top PR is merged
(squash-merged into master), so the lower PRs stay open with code that is already merged.
This skill merges the top PR when it is still open, then closes the lower PRs, deletes their
branches, and moves all the tickets to Accepted.

Merging, closing PRs and deleting branches are hard to undo. The confirmation in step 2 and
the safety gate in step 3 are the point of this skill. Never skip them.

## 1. Find the stack

Find the top PR. If the user gave a feature name, look in the user's open PRs first, then in
recent merges:

```bash
gh pr list -R <owner/repo> --author @me --state open --limit 100 \
  --json number,title,baseRefName,headRefName,headRefOid
gh pr list -R <owner/repo> --author @me --state merged --limit 20 \
  --json number,title,baseRefName,headRefName,mergedAt,mergeCommit
```

The top PR is the one no other PR in the chain targets. Walk down the chain by `baseRefName`:
follow each base to the PR whose head is that branch, until you reach a PR that targets the
default branch. If the top PR was retargeted to master before the merge, match by the ticket
name or feature words in the titles, and confirm with the safety gate.

Do not include PRs that are not in the chain, such as a proof-of-concept PR ("DON'T REVIEW")
that also targets master. Name them in the report and leave them open.

A ticket the user names that has no PR (`gh pr list --state all --search "WORK-<n>"` is empty)
may ride inside the stack as a commit. Find it with
`git log --oneline origin/<top head branch> --grep=<KEY>`. If it is in the stack, move it
with the others in step 5. If it is not, report it and do not move it.

## 2. Merge the top PR (only when it is still open)

If the top PR is already merged, go to step 3.

Read its state:

```bash
gh pr view <TOP> -R <owner/repo> \
  --json baseRefName,reviewDecision,mergeable,mergeStateStatus,statusCheckRollup
```

Ask the user before you merge, unless they already said to merge in this request. Show:

- The review decision and whether it is mergeable.
- The checks that failed or are pending. Deploy workflows that were never approved show with no
  conclusion and make the state `UNSTABLE`. That alone does not block the merge. Say so.
- Whether QA signed off, if a prod handoff happened in this session.

Do not merge when `reviewDecision` is not `APPROVED`, `mergeable` is not `MERGEABLE`, or a
PR check (for example `DefaultPR`) failed. Report it and stop.

When the user says yes:

```bash
gh pr edit <TOP> -R <owner/repo> --base <default>   # only if it targets a stack branch
gh pr merge <TOP> -R <owner/repo> --squash
gh pr view <TOP> -R <owner/repo> --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid)"'
```

Retarget first. A squash merge into the branch below would leave master without the stack.

## 3. Safety gate: is every lower PR inside the merged PR?

A squash merge makes a new commit, so `compare` shows the lower branches as "diverged". Do not
use it. Do not use `gh pr view --json commits` either: it returns at most 100 commits, and a
long stack has more, so a head commit past the 100th reads as missing.

Fetch the top PR's head (it survives a deleted branch) and test each lower head with git:

```bash
git fetch origin pull/<TOP>/head:refs/remotes/origin/pr-<TOP>
git merge-base --is-ancestor <headRefOid> origin/pr-<TOP> && echo in || echo MISSING
```

If one lower PR is missing, stop. Report which PR is missing and do not close anything. That
PR has commits that never reached master.

## 4. Close the PRs and delete the branches

Work from the top of the stack down. Then no PR is left targeting a branch that is gone.

```bash
gh pr close <N> -R <owner/repo> \
  --comment "Closing. This change was merged to master as part of the stack in #<TOP> (squash merge <short merge sha>)."
```

Write the comment in plain words. Do not use em dashes.

Delete each branch through the API. `gh pr close --delete-branch` can close the PR and still
leave the remote branch, for example when it runs inside a git worktree:

```bash
gh api -X DELETE "repos/<owner/repo>/git/refs/heads/<branch>"
```

GitHub usually deletes the top PR's branch on merge. A `422 Reference does not exist` means
the branch is already gone. That is not an error. Confirm none are left:

```bash
git ls-remote --heads origin | grep -E "<branch1>|<branch2>|..."
```

## 5. Move the tickets

Take the ticket key from each PR title, including the top PR, plus any ticket from step 1
that rides in the stack. Check the current status:

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

## 6. Report

```
Merged #9170 into master (squash 5a8cf69). Check: it holds the head commit of each lower PR.

1. Closed with a comment that points to #9170: #9169, #9168, #9164, #9161, #9160, #9151
2. Deleted the 6 branches. GitHub had already deleted the #9170 branch.
3. Jira: WORK-40188, ... moved from Ready for Merge to Accepted.

Not touched: #9001 (proof of concept, still open). Close it too?
```
