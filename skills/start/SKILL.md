---
name: start
description: Use to start and do a Jira ticket from end to end. Examples - "start 40393", "start WORK-40393", "work on WORK-40393", "pick up 40393 and get it ready for a PR". It creates a git worktree, runs the aikit jira-start skill in it, has ticket-verify write an adversarial test plan and record the "before" state, writes the code, runs ticket-verify again (QA in the browser or against the API, a review against the repo's past PR comments, fixes, a final check, the Jira attachments), and stops only at the end to ask whether to commit and open a PR. Takes a ticket key or number.
---

# Start a ticket and take it to a PR

## Overview

One skill for the whole ticket. It runs these steps in order, with no pause between them:

1. Create a worktree.
2. Run the aikit `jira-start` skill inside it.
3. Run `ticket-flow:ticket-verify` (Plan phase): test plan and "before" state.
4. Write the code.
5. Run `ticket-flow:ticket-verify` (Verify phase): gates, QA, review, fixes, final check, Jira
   attachments, and the question about the commit and PR.

Invoke the skills with the Skill tool. Do not copy their steps into this skill.

**Keep working.** The user asked for the whole ticket when they ran this skill. Do not stop to
report progress, to show a plan, or to ask "should I continue". The one planned stop is the commit
and PR question at the end of `ticket-verify`.

**Questions.** Ask one only when you are blocked and research cannot answer it: read the ticket and
its linked pages, the code, the repo docs, past PRs on the same area, and the user's memory first.
Then ask every open question together, in one message, each with your recommended answer. Work on
any part that does not depend on the answers while you wait. A choice with a sensible default is
not a question: take the default and name it in the final report.

## 1. Ticket and repo

- Ticket key from the argument (`40393` means `WORK-40393`). With no argument, ask.
- Repo: the git repo of the current directory. If the current directory is not in a repo, find
  the repo from the ticket (its summary prefix, components, linked PRs), else ask.
- Base branch: `master`, or `main` in a repo that has no `master`.

## 2. Worktree

If the session already runs in a worktree that has no commits and no changes of its own, use it.
Otherwise, from the repo's main checkout:

```bash
git fetch origin <base>
aikit repo worktrees create <key-lowercase> --base origin/<base> --branch tmp/start-<key-lowercase>
```

`jira-start` refuses a worktree with no branch (detached HEAD), so the worktree gets a temporary
branch. `jira-start` then creates the real branch from `origin/<base>` and switches to it; delete
the temporary branch after that (step 3). Then `cd` into the printed `path`. Every later step runs
there.

Start the dependency install in the background now (`npm install` in moonbeam), so it runs while
the next steps read the ticket.

## 3. jira-start

Invoke the Skill tool with `skill: "jira-start"` and `args: "<KEY>"`, from inside the worktree.

When `jira-start` offers decisions, pick the option marked as default, unless the ticket or the
user's rules say otherwise. Ask only when no option fits.

Its first decision is the base branch, because the worktree is on `tmp/start-<key>`. The default,
"Branch from `origin/<base>`", is right. Never pick "Branch from `tmp/start-<key>`".

`jira-start` creates the branch from `origin/<base>`, and the user's rules add the ticket to the
active sprint. Check that the branch is checked out in the worktree, then delete the temporary
branch: `git branch -D tmp/start-<key-lowercase>`.

## 4. Test plan

Invoke the Skill tool with `skill: "ticket-flow:ticket-verify"` and `args: "<KEY>"`. With no code
changes yet, it runs its Plan phase: the QA agent writes `plan.md` from the ticket and records the
"before" state.

## 5. Write the code

Do the ticket in the worktree:

- Read the repo's guidance first (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, the docs it links)
  and the patterns file for the repo in `ticket-verify`'s `references/review-patterns/`, so the
  code avoids what reviewers flag.
- Use `plan.md`: every acceptance criterion in it must work when you are done.
- Write or update tests for the logic you change, as the repo's docs say.
- Run the repo's fast checks on the changed files as you go.
- Do not commit. `ticket-verify` checks the uncommitted change against the base.

## 6. Verify

Invoke the Skill tool with `skill: "ticket-flow:ticket-verify"` and `args: "<KEY>"` again. With
code changes, it runs its Verify phase and ends by asking the user whether to commit and open a
PR. That question is where this skill stops.

If the user says yes, commit, push and open the PR the way the user's rules say (ready for review,
reviewers, Jira transition), then watch the PR's checks and fix failures.
