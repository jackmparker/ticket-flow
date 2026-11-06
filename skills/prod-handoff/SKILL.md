---
name: prod-handoff
description: Use when the user has started a production deploy and asks you to watch it, move the ticket (or every ticket of a combined PR) to On Prod when it lands, tell QA they can smoke test, and then start ticket-flow:merge in watch mode, which merges the PR and moves the tickets to Accepted as soon as QA moves them to Ready for Merge. Examples - "I just kicked off the prod deploy, watch it and move the ticket to on prod when it's there, then message tami", "watch the prod deploy for 40393 and let QA know", "tell Tami to smoke test when 9230 is on prod". Takes a ticket number, ticket key, PR URL or number, or branch name, plus the person to message. With no ticket, use the branch or PR of the current session.
---

# Hand a prod deploy off to QA

## Overview

Wait for a production deploy to finish. When it succeeds, move the Jira tickets to On Prod,
send the QA person a Slack message that they can smoke test, and start the merge watch (step 6).
When it fails, do none of these.

The user started the deploy and asked for the message, so do not ask again before you move the
tickets, send the message or start the merge watch. Skip the merge watch only when the user says
not to merge.

**Tickets.** A PR can hold one ticket or several (a combined PR, for example
"WORK-41048 + 41060 + 41064: FE bug fixes (combined)"). The tickets are every key in the PR title
(a bare number after a `WORK-` key is a WORK key too) and the keys in the body's ticket table.
Every step below acts on all of them.

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

Read it for every ticket. If a ticket is not in `Ready for Prod`, tell the user before the deploy ends. The move in
step 4 skips QA columns only if the user agrees.

## 3. Wait

Run the wait in the background. You are notified when it ends.

```bash
aikit circleci workflows wait <workflow-uuid> --interval 60 --timeout 3600 | tail -1 \
  | jq -c '{reason: .emission_reason, status: .workflow_status, notDone: [.jobs | to_entries[] | select(.value != "success") | "\(.key): \(.value)"]}'
```

`wait` prints one NDJSON line per poll. Each line has `workflow_status`, `emission_reason` and
`jobs`, which maps each job name to its status. It is not the same shape as
`aikit circleci workflows get`, which nests the status under `.workflow` and lists jobs as an array.

If the background command fails (for example, a jq error), do not treat it as a failed deploy.
Check `aikit circleci workflows get <uuid> | jq -r '.workflow.status'` and act on that.

Tell the user the pipeline number, the job that runs now, and what you will do when it ends.

| Final status | Action |
|---|---|
| `success` | Go to step 4 |
| `failed`, `error`, `canceled` | Report the jobs that did not succeed and their URLs. Do not move the ticket. Do not send the message |
| `on_hold` | A job waits for approval. Tell the user. Wait again after they approve |
| `reason` is not `terminal` (timeout) | Check `aikit circleci workflows get <uuid>`. If it still runs, wait again |

## 4. Move the tickets

Move every ticket from Ready for Prod to On Prod with the "Deployed" transition. Use the ID, not
the name.

```bash
aikit jira issues transitions apply <KEY1> <KEY2> ... --transition-id 131
```

If ID 131 fails (another project), run `aikit jira issues transitions list <KEY>` and pick the
transition whose target is `On Prod`. Never pick `Nevermind`, `Closed` or any backward move.

If a ticket is already in On Prod or a later column, do not move it.

## 5. Message QA

Send one short message. Name the tickets, what changed, and the PR.

```bash
aikit slack send <alias> "<KEY> is on prod and ready for a smoke test: <PR title>. <PR url>"
aikit slack send <alias> "WORK-41048, WORK-41060 and WORK-41064 are on prod and ready for a smoke test: <PR title>. <PR url>"
```

Do not send it if the deploy failed, or if step 4 failed for a reason other than "already
moved".

## 6. Start the merge watch

Invoke the Skill tool with `skill: "ticket-flow:merge"` and `args: "watch <PR url> <KEY1> <KEY2> ..."`.
It checks Jira once a minute. As soon as QA has moved every ticket to Ready for Merge, it merges the
PR, closes the tickets' own PRs for a combined PR, and moves the tickets to Accepted.

Start it only when the deploy succeeded and the tickets are in On Prod.

## 7. Report

```
WORK-40393 is on prod. Pipeline 25075 passed.
Moved WORK-40393 from Ready for Prod to On Prod.
Sent Tami a Slack message to smoke test #9230.
Watching Jira once a minute. When Tami moves WORK-40393 to Ready for Merge, I merge #9230 and move it to Accepted.
```

On failure:

```
The prod deploy for WORK-40393 failed in `build-prod` (pipeline 25075): <job url>.
I did not move the ticket, message Tami or start the merge watch.

Next: open the job log and rerun the workflow from failed.
```
