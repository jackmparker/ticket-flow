---
name: catch-up
description: Use when asked to bring a branch or PR up to date with master by merging master into it, then pushing. Examples - "catch 40350 up with master", "merge the latest from master into 40282", "Drew just merged, merge master into my branch again then push", "catch the last ticket in the stack up with master so it's ready to go to prod". Takes a ticket number, ticket key, PR URL or number, or branch name. Merges only. Never rebases or force-pushes.
---

# Catch a branch up with master

## Overview

Merge the latest default branch into a feature branch and push it. Work in a git worktree so
the user's main checkout and any uncommitted work stay untouched.

If the user also asks to deploy, finish this skill first. Then run the `deploy` skill. It
already sets the Jira Environment field and moves the ticket after a successful deploy.

## 1. Resolve the branch

| Input | How |
|---|---|
| PR URL or number | `gh pr view <pr> --json headRefName,baseRefName,state` |
| Ticket number or key (`40350`, `WORK-40350`) | `gh pr list -R <owner/repo> --state open --search "WORK-<n>" --json number,headRefName,baseRefName` |
| Branch name | Use it as is |

If the PR is merged or closed, stop and say so.

If the PR targets another feature branch (it is in a stack), the user still asked for master.
Merge master, and tell the user that the PRs below it in the stack are not updated.

Find the local clone. Check the current directory first, then common places:

```bash
for d in ~/*/ ~/*/*/; do [ -e "$d/.git" ] && git -C "$d" remote get-url origin 2>/dev/null | grep -q "<repo>" && echo "$d"; done
```

## 2. Get a worktree on the branch

```bash
cd <clone>
git fetch origin <default> <branch>
git worktree list
```

- The branch is already checked out in a worktree: use that worktree. If it has uncommitted
  changes, stop and ask.
- The local branch exists: `git worktree add .aikit/worktrees/<label> <branch>`.
- No local branch: `git worktree add --track -b <branch> .aikit/worktrees/<label> origin/<branch>`.

Do not use `aikit git worktrees create` here. It always makes a new branch, and it fails
with "a branch named ... already exists".

Bring the local branch level with origin before the merge:

```bash
git -C <worktree> merge --ff-only origin/<branch>
```

If the fast-forward fails, the local branch and origin have split. Stop and report it.

## 3. Merge and push

```bash
cd <worktree>
aikit git backmerge --base origin/<default>
```

| Outcome | Action |
|---|---|
| `up-to-date` | Report it. Nothing to push |
| `merged` | `git push origin <branch>` |
| `conflict` | Report the files in `conflict.fileSamples`. HEAD did not change. Ask the user before you resolve anything |
| `skipped` | The worktree has uncommitted files. Report them and stop |

Never rebase and never force-push. Other people review these branches.

## 4. Report

```
Merged master into feature/work-40350-page-toolbar-fill and pushed. No conflicts. 274 commits came in.
I did not run tests or a build after the merge.

Next: run /deploy us2, or wait for CI on #9198.
```

Leave the worktree in place. The user may need it again for the next catch-up.
