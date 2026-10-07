---
name: stack-cleanup
description: Use after the top PR of a stacked PR chain is merged, to close the lower PRs, delete their branches and move every ticket in the stack to Accepted. Examples - "I just merged the top ticket in the stack for OP Agent", "the stack is merged, clean up the other branches", "delete the other branches and leave a comment pointing to the last PR". Takes a merged PR URL or number, a ticket key, or a feature name such as "OP Agent".
---

# Clean up a merged PR stack

## Overview

In a stack, each PR targets the branch of the PR below it. The user merges only the top PR
(usually squash-merged into master), so the lower PRs stay open with code that is already
merged. This skill closes them, deletes their branches, and moves all the tickets to Accepted.

Closing PRs and deleting branches is hard to undo. The safety gate in step 2 is the point of
this skill. Never skip it.

## 1. Find the stack

Find the merged top PR. If the user gave a feature name, search the user's recent merges:

```bash
gh pr list -R <owner/repo> --author @me --state merged --limit 20 \
  --json number,title,baseRefName,headRefName,mergedAt,mergeCommit
```

Then list the user's open PRs and walk down the chain by `baseRefName`:

```bash
gh pr list -R <owner/repo> --author @me --state open --limit 100 \
  --json number,title,baseRefName,headRefName,headRefOid
```

Start from the PR whose head branch was the top PR's original base. Follow each `baseRefName`
to the PR whose head is that branch, until you reach a PR that targets the default branch.
The top PR may have been retargeted to master before the merge. In that case match by the
ticket name or feature words in the titles, and confirm with the commit check below.

Do not include PRs that are not in the chain, such as a proof-of-concept PR ("DON'T REVIEW")
that also targets master. Name them in the report and leave them open.

## 2. Safety gate: is every lower PR inside the merged PR?

A squash merge makes a new commit, so `compare` shows the lower branches as "diverged". Do not
use it. Instead, check that each lower PR's head commit is one of the merged PR's commits:

```bash
gh pr view <TOP> -R <owner/repo> --json commits --jq '.commits[].oid' > <scratch>/top-commits.txt
grep -q "^<headRefOid>" <scratch>/top-commits.txt && echo in || echo MISSING
```

If one lower PR is missing, stop. Report which PR is missing and do not close anything. That
PR has commits that never reached master.

## 3. Close the PRs and delete the branches

Work from the top of the stack down. Then no PR is left targeting a branch that is gone.

```bash
gh pr close <N> -R <owner/repo> --delete-branch \
  --comment "Closing. This change was merged to master as part of the stack in #<TOP> (squash merge <short merge sha>)."
```

Write the comment in plain words. Do not use em dashes.

GitHub usually deletes the top PR's branch on merge. If a delete returns
`422 Reference does not exist`, the branch is already gone. That is not an error.

## 4. Move the tickets

Take the ticket key from each PR title, including the top PR. Check the current status:

```bash
aikit jira issues get <KEY> --fields status
```

Tickets in `Ready for Merge` move with the "Code Merged, Set as Accepted" transition. Use the ID,
because `--to "Accepted"` is ambiguous (two transitions lead to Accepted):

```bash
aikit jira issues transitions apply <KEY1> <KEY2> ... --transition-id 351
```

If 351 fails, run `aikit jira issues transitions list <KEY>` and pick the transition named
"Code Merged, Set as Accepted". A ticket in an earlier column (for example `On Prod`) moves
forward one hop at a time. Report a ticket that has no forward path, and do not force it.

## 5. Report

```
Stack cleanup done. Check: #9170 was squash-merged and holds the head commit of each lower PR.

1. Closed with a comment that points to #9170: #9169, #9168, #9164, #9161, #9160, #9151
2. Deleted the 6 branches. GitHub had already deleted the #9170 branch.
3. Jira: WORK-40188, ... moved from Ready for Merge to Accepted.

Not touched: #9001 (proof of concept, still open). Close it too?
```
