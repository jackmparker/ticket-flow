---
name: prod-handoff
description: Use when the user has started a production deploy and asks you to watch it, move the ticket to On Prod when it lands, and tell QA they can smoke test. Examples - "I just kicked off the prod deploy, watch it and move the ticket to on prod when it's there, then message tami", "watch the prod deploy for 40393 and let QA know", "tell Tami to smoke test when 9230 is on prod". Takes a ticket number, ticket key, PR URL or number, or branch name, plus the person to message. With no ticket, use the branch or PR of the current session.
---

# Hand a prod deploy off to QA

## Overview

Wait for a production deploy to finish. When it succeeds, move the Jira ticket to On Prod and
send the QA person a Slack message that they can smoke test. When it fails, do neither.

The user started the deploy and asked for the message, so do not ask again before you move the
ticket or send the message.

## 1. Resolve the PR and the person

| Input | How |
|---|---|
| PR URL or number | `gh pr view <pr> -R <owner/repo> --json number,title,url,headRefName,headRefOid,state` |
| Ticket number or key (`40393`, `WORK-40393`) | `gh pr list -R <owner/repo> --state open --search "WORK-<n>" --json number,title,url,headRefName,headRefOid` |
| Branch name | `gh pr list -R <owner/repo> --head <branch> --json number,title,url,headRefName,headRefOid` |
| Nothing | The ticket, PR or branch that this session already worked on. If there is none, ask |

When the repo is not clear, find it with `gh search prs "WORK-<n>" --state open --json number,repository`.

Find the Slack recipient for the named person:

```bash
aikit slack alias list
```

Match the name to an alias (`tami`, `tamera`). If no alias matches, run `aikit slack find "<name>"`.
If there is no match, or more than one person matches, ask the user. If the user named nobody,
ask who to message.

## 2. Find the prod workflow

Read the check runs on the PR head commit. CircleCI reports each workflow as a check run, and
`details_url` holds the workflow UUID.

```bash
gh api 'repos/<owner/repo>/commits/<headRefOid>/check-runs?per_page=100' \
  --jq '.check_runs[] | select(.name | startswith("BuildAndDeploy_Prod")) | "\(.status) \(.conclusion) \(.details_url)"'
```

| Result | Action |
|---|---|
| One run, `completed` and `success` | The deploy is already done. Go to step 4 |
| One run, `in_progress` or `queued` | Take the UUID after `/workflow/` and go to step 3 |
| One run, `completed` and not `success` | Report the failure. Stop |
| No run | The user may have deployed another commit. Ask for the pipeline or workflow URL |

If the user pushed after the deploy started, the head commit has no prod run. Ask for the
workflow URL. Do not guess from an older commit.

Read the ticket status now:

```bash
aikit jira issues get <KEY> | jq -r '.status.name'
```

If the ticket is not in `Ready for Prod`, tell the user before the deploy ends. The move in
step 4 skips QA columns only if the user agrees.

## 3. Wait

Run the wait in the background. You are notified when it ends.

```bash
aikit circleci wait <workflow-uuid> --interval 60 --timeout 3600 2>&1 | tail -1 \
  | jq -c '{status: .workflow.status, notDone: [.jobs[] | select(.status != "success") | {name, status}]}'
```

Tell the user the pipeline number, the job that runs now, and what you will do when it ends.

| Final status | Action |
|---|---|
| `success` | Go to step 4 |
| `failed`, `error`, `canceled` | Report the jobs that did not succeed and their URLs. Do not move the ticket. Do not send the message |
| `on_hold` | A job waits for approval. Tell the user. Wait again after they approve |
| Timeout | Check `aikit circleci status <uuid>`. If it still runs, wait again |

## 4. Move the ticket

Move it from Ready for Prod to On Prod with the "Deployed" transition. Use the ID, not the
name.

```bash
aikit jira issues transitions apply <KEY> --transition-id 131
```

If ID 131 fails (another project), run `aikit jira issues transitions list <KEY>` and pick the
transition whose target is `On Prod`. Never pick `Nevermind`, `Closed` or any backward move.

If the ticket is already in On Prod or a later column, do not move it.

## 5. Message QA

Send one short message. Name the ticket, what changed, and the PR.

```bash
aikit slack send <alias> "<KEY> is on prod and ready for a smoke test: <PR title>. <PR url>"
```

Do not send it if the deploy failed, or if step 4 failed for a reason other than "already
moved".

## 6. Report

```
WORK-40393 is on prod. Pipeline 25075 passed.
Moved WORK-40393 from Ready for Prod to On Prod.
Sent Tami a Slack message to smoke test #9230.

Next: merge #9230 after Tami signs off.
```

On failure:

```
The prod deploy for WORK-40393 failed in `build-prod` (pipeline 25075): <job url>.
I did not move the ticket or message Tami.

Next: open the job log and rerun the workflow from failed.
```
