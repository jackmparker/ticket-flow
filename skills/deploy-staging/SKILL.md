---
name: deploy-staging
description: Use when asked to deploy a moonbeam ticket to staging. It deploys to US2 (the user's own FE staging environment) unless the user names another environment such as US8. Examples - "deploy 41083 to staging", "send 9442 to us2", "deploy WORK-41083 to us8". It merges master into the branch and pushes (ticket-flow:catch-up), deploys at once with the aikit deploy skill without waiting for the DefaultPR checks, and when the deploy lands sets each ticket's Environment field and moves every ticket in Ready for Staging or Waiting for Fix to On Stage - Ready for Test. Meanwhile it watches DefaultPR; if it fails, it fixes the cause, pushes after the deploy ends, and deploys to the environment again. Works for one ticket's PR, a combined PR that holds several tickets, and a stack of PRs. Takes a ticket number, ticket key, PR URL or number, or branch name, and an optional environment. With no ticket, use the branch or PR of the current session. moonbeam only.
---

# Deploy a moonbeam ticket to staging

## Overview

1. Find the PR, its tickets and the environment (US2 by default).
2. `ticket-flow:catch-up` merges master into the branch and pushes.
3. The aikit `deploy` skill deploys the branch at once. It does not wait for DefaultPR.
4. While the deploy runs, watch DefaultPR. If it fails, fix it, and push only after the deploy ends.
5. When the deploy lands, set the Environment field and move every ticket to On Stage - Ready for Test.
6. If step 4 pushed a fix, deploy again (steps 3 and 5).

Invoke each skill with the Skill tool. Do not copy their steps into this skill.

The user asked for the deploy and the Jira moves when they ran this skill. Do not ask again before
each step. Do not send QA a message: QA reads the Jira columns.

Repo: `observepoint/moonbeam`. If the request is for another repo, stop and say that this skill
is for moonbeam only.

## 1. Resolve the PR, the tickets and the environment

| Input | How |
|---|---|
| PR URL or number | `gh pr view <pr> -R observepoint/moonbeam --json number,title,body,url,headRefName,headRefOid,state,reviewDecision` |
| Ticket number or key (`41083`, `WORK-41083`) | `gh pr list -R observepoint/moonbeam --state open --search "WORK-<n>" --json number,title,url,headRefName` |
| Branch name | `gh pr list -R observepoint/moonbeam --head <branch> --json number,title,url,headRefName` |
| Nothing | The ticket, PR or branch that this session already worked on. If there is none, ask |

A ticket that is in a combined PR finds two open PRs: its own and the combined one (the title
lists several keys). Deploy the one the user named; for a bare ticket key, deploy the combined PR.

If the PR is merged or closed, stop and say so.

**Tickets**: every key in the PR title (a bare number after a `WORK-` key is a WORK key too) and the
keys in the body's ticket table. Do not use the branch name: a combined branch such as
`bug/combined/fe-bugs-2026-11-06` holds no key. For that reason, do not pass `--jira` to the
`deploy` skill. Step 5 moves the tickets.

**Stack.** If another open PR targets this PR's branch, or this PR targets a branch that is not
master, the PR is part of a stack. Deploy the top PR (the one that no other PR targets): its branch
holds the whole stack. The tickets are the keys of every PR in the chain, from the top PR down to
the PR that targets master. Find the chain as `ticket-flow:merge` step 1 says (walk down by
`baseRefName`).

**Environment**: `us2`, unless the user named another one (`us8`, `ua6`, `dave`). Use the short
name in lowercase for the deploy, and in uppercase for Jira (`us8` -> `US8`, `dave` -> `Dave`).

Read each ticket's status:

```bash
aikit jira issues get <KEY> --fields status | jq -r '.status.name'
```

A ticket that is not in `Ready for Staging` (for example, its PR is not approved yet) does not stop
the deploy. Step 5 leaves it where it is. Name it in the report.

**Someone else's tickets on the environment.** US2 is the user's own environment; skip this check
for US2. For any other environment, look for tickets that QA tests there now:

```bash
aikit jira issues search --jql 'project = WORK AND cf[11600] = <ENV> AND status in ("On Stage - Ready for Test", "On Stage - In Test")' --fields status,summary,assignee
```

`cf[11600]` is the Environment field. If a ticket that is not one of this PR's tickets is listed,
the deploy would remove its code. Stop and ask the user. Name the tickets, their status and
their assignee.

**A deploy of this branch that runs now.** The catch-up push in step 2 would cancel it:

```bash
aikit circleci pipelines list --project gh/observepoint/moonbeam --branch <branch> --limit 3
```

If a deploy workflow on this branch is `running`, wait for it to end before step 2. Tell the user.

## 2. Catch up with master

Invoke the Skill tool with `skill: "ticket-flow:catch-up"` and `args: "<branch>"`.

| Outcome | Action |
|---|---|
| `up-to-date` | Go to step 3 |
| `merged` and pushed | Go to step 3 at once. The push starts a new pipeline. Do not wait for its DefaultPR |
| `conflict`, `skipped`, or a failed fast-forward | Stop. Report what catch-up reported. Do not deploy |

## 3. Deploy

Invoke the Skill tool with `skill: "deploy"` and `args: "<env> --branch <branch>"`.

- Do not pass `--jira`. Step 5 moves the tickets.
- Do not pass `--notify`.
- Do not pass `--no-wait`. The `deploy` skill must wait, because it decides whether the deploy
  succeeded from the deploy job.

When the `deploy` skill has started the deploy and starts its background wait, go to step 4 at
once. Do not end the turn before step 4 has started.

If the `deploy` skill stops before the deploy, stop here too and report why.

## 4. Watch DefaultPR while the deploy runs

Find the DefaultPR workflow of the branch's head commit (the commit that the deploy uses):

```bash
gh api 'repos/observepoint/moonbeam/commits/<head sha>/check-runs?per_page=100' \
  --jq '.check_runs[] | select(.name | startswith("DefaultPR")) | "\(.status) \(.conclusion) \(.details_url)"'
```

The workflow UUID is after `/workflow/` in `details_url`. The check run can take a minute to
appear after a push; read it again until it does. Wait for it in the background:

```bash
aikit circleci workflows wait <workflow-uuid> --interval 60 --timeout 3600 | tail -1 \
  | jq -c '{reason: .emission_reason, status: .workflow_status, notDone: [.jobs | to_entries[] | select(.value != "success") | "\(.key): \(.value)"]}'
```

| DefaultPR result | Action |
|---|---|
| `success` | Nothing to do |
| `failed` | Find the cause with the `circleci` skill. For a flaky failure, rerun from failed (`aikit circleci moonbeam rerun <workflow> --from-failed`). For a real failure, fix it in the branch's worktree (`git worktree add .aikit/worktrees/<label> <branch>`, or the worktree that already has it), run the failed spec or lint locally, and commit with the ticket key. Push only when the deploy job has ended (below) |

**Never push while the deploy runs.** A push cancels the running deploy. When the fix is
committed and the `deploy` skill's wait has ended, push, then go back to step 3 to deploy the
fixed branch. Do step 5 for the first deploy before that only if it succeeded. Watch DefaultPR
again for the new commit. Stop after 3 fix rounds and report what still fails.

## 5. Move the tickets when the deploy lands

When the `deploy` skill reports that the deploy job succeeded:

Set the Environment field on every ticket:

```bash
aikit jira issues set-field <KEY1> <KEY2> ... --field environment --value "<ENV>"
```

On `set-field-value-not-allowed`, the error lists the valid options. Retry once with the option
that matches the environment (case-insensitive). When none matches, leave the field and report it.

Move every ticket that is in `Ready for Staging` with the "Deploy to Staging" transition, and
every ticket in `Waiting for Fix` (a redeploy after a QA fix) with its "Ready for Staging"
transition. Both lead to `On Stage - Ready for Test`. Use the IDs:

```bash
aikit jira issues transitions apply <KEYS in Ready for Staging> --transition-id 91
aikit jira issues transitions apply <KEYS in Waiting for Fix> --transition-id 371
```

If 91 or 371 fails, run `aikit jira issues transitions list <KEY>` and pick the transition whose
`targetStatus` is `On Stage - Ready for Test`. A ticket that is already in an On Stage column
stays where it is. A ticket in an earlier column (for example `To Be Reviewed`) stays where it is;
name it in the report. Never move a ticket backward.

The Jira API sometimes closes the socket. A result with `"retryable": true` or "socket connection
was closed" is not a refusal: retry that key once, then read the status again.

If the deploy failed, do not change Jira. Report the failed job.

`on_hold` on an `e2e-bypass-approve-*` job means the E2E tests failed. Never approve it and never
ask the user to approve it. Report the failed tests.

## 6. Report

Lead with the result.

```
WORK-41083 is on US2. https://us2.observepointstaging.com

1. Catch-up: merged master into bug/work-41083-card-row-clicks and pushed (4 commits came in).
2. Deploy: pipeline 25311, the us2 deploy job passed.
3. Jira: Environment set to US2. Moved WORK-41083 from Ready for Staging to On Stage - Ready for Test.
4. DefaultPR: passed.
```

When DefaultPR failed and you fixed it, say what failed, the fix commit, and that the second deploy
passed. On failure, name the step that stopped, the reason, and what was not done.
