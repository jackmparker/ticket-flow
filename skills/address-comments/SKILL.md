---
name: address-comments
description: Use when asked to handle review comments on the user's open PRs - fix what reviewers asked for, reply on each thread, and merge the fix into any PRs stacked on top. Examples - "address the review comments", "check my PRs for comments that haven't been addressed", "Cam left comments, fix them", "fix the comments on 9208 and merge it up the stack". With no arguments, check every open PR the user authored. A PR URL or number, a ticket key, or a repo narrows the set.
---

# Address review comments

## Overview

Find review comments that still wait for the user, fix them, reply on the thread, and carry
the fix up the PR stack.

Replies are signed as the user and land on a teammate's review. So the rule is:

- **Clear code request** (a bug, a missing call, a duplicate line, a rename the reviewer asked
  for): fix, test, push, merge downstream and reply. Do not stop to ask.
- **Question, suggestion or "I wonder if..."**, or a request you think is wrong: do not change
  code. Show the user a draft reply (and, for a suggestion, the change you would make) and wait.

When you are not sure which kind a comment is, treat it as the second kind.

## 1. Find comments that wait for the user

```bash
gh api graphql -F q='is:pr is:open author:@me' -f query='
query($q:String!){ search(query:$q, type:ISSUE, first:50){ nodes{ ... on PullRequest{
  number title url repository{nameWithOwner} baseRefName headRefName headRefOid
  reviewThreads(first:100){ nodes{ isResolved isOutdated path line
    comments(first:20){ nodes{ databaseId author{login} body createdAt } } } }
  reviews(last:20){ nodes{ databaseId author{login} state body submittedAt } }
} } } }'
```

Add `repo:<owner/repo>` to `q` to narrow it. For one PR, use `is:pr <number> repo:<owner/repo>`.

A thread waits for the user when all of these are true:

- `isResolved` is false.
- The last comment's author is not the user (`gh api user --jq .login`). If the user has the
  last word ("Fixed in ..."), the reviewer has not answered yet. Skip it.
- The last comment's author is not a bot.

A review body also waits for the user when it has text, its author is not the user or a bot,
and no later PR comment from the user answers it
(`gh pr view <n> --json comments`).

An `isOutdated` thread can still be open. Read the code at the head commit to see if the ask
is already done. If it is, reply with the commit that did it and do not change code.

## 2. Get the branch

Use the `catch-up` skill, step 2, to get a worktree on the PR's head branch that is level with
origin. If the local branch has split from origin, compare the two. When origin holds the
reviewed commits and the local commits are an old copy (for example from before a restack),
reset the local branch to origin. The old tip stays in the reflog. Say that you did it.

## 3. Fix

Read the whole comment thread and the code around `path:line` at the head commit. Make the
smallest change that does what the reviewer asked. Do not fix other things in the same commit.

Check the change with the repo's own commands. Look in the repo's `CLAUDE.md`, `AGENTS.md`,
`package.json` scripts or `scripts/ai/`. Lint the changed files and run the specs next to them.
In moonbeam:

```bash
npx eslint <changed files>
./scripts/ai/run-tests.sh -i '**/<name>.component.spec.ts'
```

If a check fails and you cannot fix it in the same small change, stop and report. Do not push.

Commit one fix per comment, with a message that names the change, then push:

```bash
git commit -m "<what changed> (review feedback on #<pr>)"
git push origin <branch>
```

Never rebase and never force-push.

## 4. Merge the fix up the stack

Find the PRs that build on this branch. Repeat until no PR is left:

```bash
gh pr list -R <owner/repo> --state open --base <branch> --json number,headRefName
```

Work from the lowest PR up. For each one, get a worktree level with origin, then merge the
branch below it and push:

```bash
git merge --no-edit origin/<branch below>
git push origin <this branch>
```

Fetch after each push, so the next merge uses the new tip. If a merge has conflicts, abort it
(`git merge --abort`), stop, and report the files. The fix is already pushed on the lower PR, so
the reply in step 5 can still go out.

## 5. Reply

Reply after the push, so the commit link works. Use the `databaseId` of the first comment in the
thread:

```bash
gh api -X POST repos/<owner/repo>/pulls/<pr>/comments/<databaseId>/replies -f body="<reply>"
```

Run each `gh api` call as its own plain command, not in a loop or a script. Then the user's
permission rules match it.

For a review body, answer with one PR comment: `gh pr comment <pr> -R <owner/repo> --body "<reply>"`.

How to write the reply:

- Start with the commit: `Fixed in <short sha>.` Then say in one short sentence what changed, if
  the fix is not the exact thing the reviewer wrote. Example: "Fixed in 957847afef. Kept the
  comment and dropped the second call."
- Plain words, no em dashes, no thanks-padding.
- Do not resolve the thread. The reviewer resolves it.

## 6. Report

```
Fixed 1 comment and replied:
1. #9208 privacy-requests.component.ts:574 (Camden): summary token leak. Fixed in 1a2b3c4d.
   Lint and spec pass. Merged into #9210 and pushed.

Waiting for you (no code changed):
2. wordpress-blank-theme #15 package.json:13 (Camden): asks about a "dummy" key.
   Draft reply: "..." Post it?

Already answered, waiting on the reviewer: #9190 (1 thread).
```

End with one next action, for example "Say 'post' to send the draft for #15."
