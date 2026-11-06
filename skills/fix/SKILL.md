---
name: fix
description: Use when feedback on the user's tickets needs a code fix - review comments on their open PRs, or a bug that QA found and reported in Jira (the ticket is in Waiting for Fix). It reads the feedback, skips a QA bug that is already fixed and on its way to the environment, reproduces a QA bug first, fixes it in the ticket's own branch, checks it (lint, specs, and for a QA bug a QA run in the browser), carries the fix into combined branches and up stacks, then decides by itself what comes next from the ticket's state - push only, or redeploy to the staging environment that runs the ticket and move it back to On Stage. It replies on the GitHub thread or with a short Jira comment for QA, and teaches ticket-verify what reviewers and QA caught. Examples - "fix what Tami found in 41060", "fix 41060", "address the review comments", "Cam left comments on 9208, fix them", "check my PRs and tickets for anything that needs fixing". With no arguments, check every open PR the user authored and every ticket of theirs in Waiting for Fix. A ticket key, PR URL or number, or a repo narrows the set.
---

# Fix review comments and QA bugs

## Overview

Two kinds of feedback, one flow:

| | Review comment | QA bug |
|---|---|---|
| Comes from | A GitHub review thread on the ticket's PR | A Jira comment from QA; the ticket is in `Waiting for Fix` |
| Before the fix | Nothing | Reproduce the bug |
| Check after the fix | Lint and specs | Lint, specs, and a QA run in the browser |
| Reply | On the GitHub thread | A short Jira comment for QA |
| Teaches | The repo's review patterns | The repo's "missed by QA" list |

After the fix, step 5 decides what comes next from the facts (push only, or push and redeploy).
The feedback kind does not decide it.

Replies are signed as the user and land on a teammate's review or ticket. So:

- **Clear code request or a reproduced QA bug**: fix, check, push, carry the fix, redeploy when
  step 5 says so, and reply. Do not stop to ask.
- **Question, suggestion, "I wonder if...", a request you think is wrong, or a QA bug you cannot
  reproduce**: do not change code. Show the user a draft reply (and, for a suggestion, the change
  you would make) and wait.

When you are not sure which kind it is, treat it as the second kind.

The user's rules apply: your own worktree, never steal browser focus, never push while a deploy of
that branch runs.

## 1. Find the feedback

**Review comments.**

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
For a ticket key, search `is:pr is:open author:@me <KEY>`.

A thread waits for the user when all of these are true:

- `isResolved` is false.
- The last comment's author is not the user (`gh api user --jq .login`). If the user has the
  last word ("Fixed in ..."), the reviewer has not answered yet. Skip it.
- The last comment's author is not a bot.

A review body also waits for the user when it has text, its author is not the user or a bot,
and no later PR comment from the user answers it (`gh pr view <n> --json comments`).

An `isOutdated` thread can still be open. Read the code at the head commit to see if the ask
is already done. If it is, reply with the commit that did it and do not change code.

**QA bugs.**

```bash
aikit jira issues search --jql 'assignee = currentUser() AND status = "Waiting for Fix"' --fields status,summary
```

For one ticket, read its status instead. For each ticket in `Waiting for Fix`, read what QA found:

```bash
aikit jira issues get <KEY> --fields comment,environment,status
aikit jira attachments list <KEY>
aikit jira attachments download <attachmentId> --issue-key <KEY> --output <evidence folder>/fix/
```

QA's finding is in the newest comments by someone other than the user (for example a
"QA Results" comment). Read the screenshots it names. Write each bug as one line: what QA did,
what they expected, what they saw, and on which environment (the `environment` field, for
example US2).

Group all feedback by ticket. A ticket's PR is the open PR whose title holds its key and no other
key (its own PR), not the combined PR.

**Is a QA bug already handled?** Someone (you, another agent, the user) may have fixed it, and the
ticket stays in `Waiting for Fix` until a deploy lands. Before you work on such a ticket, check:

1. QA's time: when QA posted the comment with the bug (T).
2. Fix commits after T. Fetch, then look on the ticket's own branch and on each combined branch or
   stack top that holds it (step 6 says how to find them):

   ```bash
   git fetch origin
   git log origin/<ticket branch> --no-merges --since=<T> --format='%h %cI %s'
   git log origin/<combined branch> --no-merges --since=<T> --grep=<KEY> --format='%h %cI %s'
   ```

3. A "Fixed in" comment from the user on the ticket after T.
4. A deploy to the ticket's environment that runs now, for one of those branches: in
   `aikit circleci pipelines list --project gh/observepoint/moonbeam --branch <branch> --limit 3`,
   a `BuildAndDeploy_Stage` workflow whose `deploy-<env>` job (`aikit circleci workflows get <id>`)
   is running or queued.
5. A deploy that already landed with the fix: `<skill folder>/env-branch.sh <env>` names one of
   those branches, and its commit holds the fix commit
   (`git merge-base --is-ancestor <fix sha> <deployed commit>`).

| What you find | Action |
|---|---|
| No fix commit and no "Fixed in" comment | Not handled. Fix it (steps 2 to 10) |
| A fix commit, and a deploy with it runs now | Do not touch the code. Wait for that deploy job in the background (`aikit circleci workflows wait <id>`). When its `deploy-<env>` job succeeded and the ticket is still in `Waiting for Fix`, set its Environment field and move it with transition 371 (step 5 of `deploy-staging` says how). Report "fix on its way" |
| A fix commit, and a deploy with it already landed | The fix is on the environment, but nobody moved the ticket. Move it as above, and post the Jira comment for QA (step 8) if the user has not |
| A fix commit, and no deploy with it | Do not fix again. Start at step 5 with that commit as the fix: it decides whether to redeploy |

Name the fix commit and who made it in the report.

## 2. Get the branch

Fix in the ticket's own branch, so its PR stays right for review. Use the `catch-up` skill, step 2,
to get a worktree on that branch that is level with origin. If the local branch has split from
origin, compare the two. When origin holds the reviewed commits and the local commits are an old
copy (for example from before a restack), reset the local branch to origin. The old tip stays in
the reflog. Say that you did it.

If the PR is already merged, stop and ask: the fix needs a new branch.

## 3. Reproduce a QA bug

Skip this step for review comments.

Reproduce on the environment QA used (`https://<env>.observepointstaging.com`, for example
`https://us2.observepointstaging.com`), with browser-harness and the user's browser rules. If the
environment no longer runs this ticket (step 5 finds out), reproduce on the branch run locally with
`moonbeam-dev start`. Save a cropped screenshot of the bug in
`<worktree>/.aikit/ticket-verify/<KEY>/fix/before/` when it is visual.

If it does not reproduce after two tries, do not change code. Draft a Jira reply to QA that says
what you tried and asks for the exact steps, and show it to the user.

## 4. Fix and check

Read the whole thread or QA comment, and the code around it. Make the smallest change that fixes
it. Do not fix other things in the same commit.

Check with the repo's own commands (`CLAUDE.md`, `AGENTS.md`, `package.json` scripts,
`scripts/ai/`). Lint the changed files and run the specs next to them. In moonbeam:

```bash
npx eslint <changed files>
./scripts/ai/run-tests.sh -i '**/<name>.component.spec.ts'
```

For a QA bug, also:

- Add or change a spec that fails without the fix, when the logic can be tested that way.
- Run a QA round as `ticket-verify` step 3.2 says, on the branch run locally (`moonbeam-dev start`):
  the cases are QA's bug, plus the cases in `<worktree>/.aikit/ticket-verify/<KEY>/plan.md` when it
  exists (the fix must not break what passed before). Save an "after" screenshot with the same
  name and crop as the "before" one. Fix and run again if it fails; stop after 3 rounds and report.

If a check fails and you cannot fix it in the same small change, stop and report. Do not push.

Commit one fix per comment or bug, with the ticket key:

```bash
git commit -m "<KEY>: <what changed> (review feedback on #<pr>)"
git commit -m "<KEY>: <what changed> (QA feedback)"
```

Do not push yet. Never rebase and never force-push.

## 5. Decide what comes next

Read the facts, then pick one row. Do this for each ticket.

1. The ticket's status and `environment` field (`aikit jira issues get <KEY> --fields status,environment`).
2. What runs on that environment now. This prints the branch of the newest successful deploy:

   ```bash
   <skill folder>/env-branch.sh <env lowercase>
   ```

   "This branch" below means the ticket's own branch, a combined branch that holds it (its PR
   lists the ticket's PR or key), or the top branch of a stack that holds it.
3. Whether a deploy of that branch runs now:
   `aikit circleci pipelines list --project gh/observepoint/moonbeam --branch <branch> --limit 3`.
4. What the fix changed: app code, or only specs, tests and code comments.

| Facts | Action |
|---|---|
| The fix changed only specs, tests or code comments | Push only |
| Ticket not on an environment yet (`In Progress`, `To Be Reviewed`, `Code Review`, `Ready for Staging`, or the field is empty) | Push only |
| Ticket in an On Stage column, `Waiting for Fix` or `In Test`, and the environment runs this branch | Push, then redeploy (step 7) |
| The environment runs another branch, or `env-branch.sh` found none | Push only. Tell the user which branch runs there: a redeploy would remove that branch's code |
| Ticket in `Ready for Prod`, `On Prod` or `Ready for Merge` (a bug found on prod or just before it) | Push, then redeploy to the ticket's staging environment for a retest (step 7), and tell the user. Never deploy to prod |

A deploy of the branch that runs now never changes the row. It only delays the push: wait for it
to end first, because a push cancels it.

## 6. Push and carry the fix

Push the ticket's branch: `git push origin <branch>`.

**Up a stack.** Find the PRs that build on this branch. Repeat until no PR is left:

```bash
gh pr list -R <owner/repo> --state open --base <branch> --json number,headRefName
```

Work from the lowest PR up. For each one, get a worktree level with origin, then merge the
branch below it and push:

```bash
git merge --no-edit origin/<branch below>
git push origin <this branch>
```

**Into combined branches.** Find open PRs that hold this ticket: their title lists more than one
key and holds this key, or their body lists this ticket's PR (`#<n>`). For each one, in a worktree
level with origin:

```bash
git merge --no-ff --no-edit origin/<ticket branch>
git push origin <combined branch>
```

Before each push, check again that no deploy of that branch runs. Fetch after each push, so the
next merge uses the new tip. If a merge has conflicts, abort it (`git merge --abort`), stop, and
report the files. The fix is already pushed on the ticket's PR, so its reply can still go out.

**Approval.** A new commit can dismiss an approval. After the push, read
`gh pr view <n> -R <owner/repo> --json reviewDecision,latestReviews`. If the PR was approved and
`reviewDecision` is no longer `APPROVED`, ask the same reviewers again
(`gh pr edit <n> -R <owner/repo> --add-reviewer <login>`) and say so in the report.

## 7. Redeploy

Only when step 5 says so. Invoke the Skill tool with `skill: "ticket-flow:deploy-staging"` and
`args: "<branch that runs on the environment> <env>"`. It merges master in, deploys, sets the
Environment field and moves the ticket from `Waiting for Fix` (or `Ready for Staging`) to
`On Stage - Ready for Test`. Tickets of a combined PR in other columns (for example `In Test`)
stay where QA has them.

For a ticket that was on prod, deploy-staging cannot move it back. Leave its status and tell the
user.

## 8. Reply

Reply after the push (and after the deploy for a QA bug), so the links work.

**Review comment.** Use the `databaseId` of the first comment in the thread:

```bash
gh api -X POST repos/<owner/repo>/pulls/<pr>/comments/<databaseId>/replies -f body="<reply>"
```

Run each `gh api` call as its own plain command, not in a loop or a script. Then the user's
permission rules match it. For a review body, answer with one PR comment:
`gh pr comment <pr> -R <owner/repo> --body "<reply>"`. Do not resolve the thread. The reviewer
resolves it.

**QA bug.** One short Jira comment, in ADF (Atlassian Document Format, the JSON that Jira comments
use):

```bash
aikit jira issues comment <KEY> --adf '{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Fixed in <short sha>: <what was wrong, one sentence>. It is on US2 again, ready to test."}]}]}'
```

When step 5 chose push only, end with what QA should wait for instead, for example "It reaches US2
with the next deploy."

How to write a reply: start with the commit (`Fixed in <short sha>.`), then one short sentence on
what changed if it is not the exact thing asked. Plain words, no em dashes, no thanks-padding.

## 9. Teach ticket-verify

Use the ticket-flow clone at `~/ObservePoint/ticket-flow` (clone it if missing, and
`git pull --ff-only` first).

**Review comment.** Open `skills/ticket-verify/references/review-patterns/<repo>.md`. If no pattern
already covers what the reviewer asked, the review missed it, so add one line under
`## New, not yet grouped` at the end (create the heading if it is missing):

```
- <YYYY-MM-DD> <reviewer login>: <what they asked for, one sentence>. <comment URL>
```

**QA bug.** Open `skills/ticket-verify/references/qa-misses/<repo>.md` (create it with a
`# <repo>: bugs QA found after ticket-verify passed` heading). Our QA run missed this bug, so add
one line:

```
- <YYYY-MM-DD> <KEY> (<QA name>): <what broke, one sentence>. Test: <the case that finds it, one sentence>.
```

Skip questions and praise. Commit on `main` with the message
`Review patterns and QA misses: new feedback from <repo> <KEY or #pr>` and push. Do not update
the installed plugin for this. If the pull or push fails, leave the lines uncommitted and say so.

## 10. Report

Lead with the result. One block per ticket.

```
WORK-41060 fixed and back on US2. https://us2.observepointstaging.com

1. QA bug (Tamera): reprocess still sent runId 0 for a folder with no runs. Reproduced on US2.
   Fixed in 1a2b3c4d. Lint, specs and QA (bug plus 6 plan cases) pass.
2. Merged into bug/combined/fe-bugs-2026-11-06 and pushed.
3. US2 ran the combined branch, so I redeployed it. WORK-41060 moved to On Stage - Ready for Test.
4. Jira comment for Tamera posted. Added the bug to the moonbeam QA misses list.

WORK-41083, #9443 (Camden): 1 review comment fixed in 5e6f7a8b, reply posted.
Not deployed: the ticket is in To Be Reviewed.

Waiting for you (no code changed):
- #9301 report.service.ts:88 (Camden) asks why the cache is cleared twice. Draft reply: "..." Post it?
```

End with one next action, for example "Say 'post' to send the draft for #9301."
