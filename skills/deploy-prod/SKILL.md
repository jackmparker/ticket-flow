---
name: deploy-prod
description: Use when asked to deploy a moonbeam ticket to production in one step. Examples - "deploy 40393 to prod", "ship WORK-40393 to prod and tell Tami", "run deploy-prod on this branch". It runs three skills in order - catch-up (merge master into the branch and push), the aikit deploy skill to prod, then prod-handoff (move the ticket to On Prod and message QA) while the deploy runs. Takes a ticket number, ticket key, PR URL or number, or branch name, and an optional person to message (default Tami). With no ticket, use the branch or PR of the current session. moonbeam only.
---

# Deploy a moonbeam ticket to production

## Overview

One skill for the full prod deploy of a moonbeam ticket. It runs three skills in this order:

1. `ticket-flow:catch-up` merges master into the branch and pushes.
2. The aikit `deploy` skill deploys the branch to `prod` and waits for the result.
3. `ticket-flow:prod-handoff` starts while the deploy runs. When the deploy succeeds, it moves the
   ticket to On Prod and sends QA a Slack message to smoke test.

Invoke each skill with the Skill tool. Do not copy their steps into this skill. Each skill has its
own checks and stops, and they all apply here.

The user asked for the deploy and the message when they ran this skill. Do not ask again before
each step. Stop and ask only where a step below, or one of the three skills, says so.

Repo: `observepoint/moonbeam`. If the request is for another repo, stop and say that this skill
is for moonbeam only.

## 1. Resolve the ticket, branch and person

| Input | How |
|---|---|
| PR URL or number | `gh pr view <pr> -R observepoint/moonbeam --json number,title,url,headRefName,state` |
| Ticket number or key (`40393`, `WORK-40393`) | `gh pr list -R observepoint/moonbeam --state open --search "WORK-<n>" --json number,title,url,headRefName` |
| Branch name | `gh pr list -R observepoint/moonbeam --head <branch> --json number,title,url,headRefName` |
| Nothing | The ticket, PR or branch that this session already worked on. If there is none, ask |

If the PR is merged or closed, stop and say so.

The person to message is Tami, unless the user named someone else.

Check that no deploy of this branch runs now. The catch-up push in step 2 would cancel it:

```bash
aikit circleci pipelines list --project gh/observepoint/moonbeam --branch <branch> --limit 3
```

If a workflow on this branch is `running`, stop. Tell the user which workflow runs, and wait
until they say go.

## 2. Catch up with master

Invoke the Skill tool with `skill: "ticket-flow:catch-up"` and `args: "<branch>"`.

| Outcome | Action |
|---|---|
| `up-to-date` | Go to step 3 |
| `merged` and pushed | Go to step 3. The push starts a new pipeline. The prod deploy uses it |
| `conflict`, `skipped`, or a failed fast-forward | Stop. Report what catch-up reported. Do not deploy |

## 3. Deploy to prod

Invoke the Skill tool with `skill: "deploy"` and `args: "prod --branch <branch>"`.

- Do not pass `--jira`. `prod-handoff` moves the ticket in step 4.
- Do not pass `--notify`. `prod-handoff` sends the QA message in step 4.
- Do not pass `--no-wait`. The `deploy` skill must wait, because it decides whether the deploy
  succeeded. It reads the deploy job, not the workflow status, and it reports each environment
  in `also_deploys`.

The `deploy` skill can stop before the deploy (for example, another prod deploy runs, or prod
runs a branch that is not merged). Then stop here too. Do not run step 4.

When the `deploy` skill has started the deploy and starts its background wait, go to step 4 at
once. Do not end the turn before step 4 has started.

## 4. Hand off to QA while the deploy runs

Invoke the Skill tool with `skill: "ticket-flow:prod-handoff"` and these `args`:

```
<KEY> <PR url> message <person>. The deploy skill already waits for workflow <workflow-uuid>
and decides the result. Do not start a second wait. Do steps 1 and 2 now, then do steps 4 to 6
only when the deploy skill reports that the prod deploy job succeeded.
```

Steps 1 and 2 of `prod-handoff` run now. They find the Slack recipient and read the ticket
status. If the ticket is not in `Ready for Prod`, tell the user now, before the deploy ends.

When the `deploy` skill's wait ends:

| Deploy result | Action |
|---|---|
| The prod deploy job succeeded | Finish `prod-handoff` steps 4 to 6: move the ticket to On Prod, message QA, report |
| The prod deploy job failed | Do not move the ticket and do not send the message. Report what the `deploy` skill found |
| `on_hold` on an `e2e-bypass-approve-*` job | The E2E tests failed. Never approve it and never ask the user to approve it. Report the failed tests. Do not move the ticket and do not send the message |

## 5. Report

Lead with the result.

```
WORK-40393 is on prod.

1. Catch-up: merged master into feature/work-40393-toolbar and pushed (12 commits came in).
2. Deploy: pipeline 25075, the prod deploy job passed. https://app.observepoint.com
3. Moved WORK-40393 from Ready for Prod to On Prod. Sent Tami a Slack message to smoke test #9230.

Next: merge #9230 into master after Tami signs off.
```

On failure, name the step that stopped, the reason, and what was not done.
