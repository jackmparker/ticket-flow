---
name: jira-sync
description: Use when asked to move Jira tickets to match their pull requests, or to check whether tickets are in the right column. Examples - "move any approved tickets into ready for staging", "review my jira tickets and move any that have been approved", "see if any of the zoneless tickets need to be moved", "are my tickets in the right columns". With no arguments, check every ticket assigned to the user. A word such as "zoneless" or "OP Agent", an epic key, or a list of keys narrows the set.
---

# Sync Jira tickets with their PRs

## Overview

Compare each ticket with the state of its GitHub PR. Move the ticket forward when the PR is
ahead of it. Never move a ticket backward. Report every ticket, moved or not, so the user can
see the whole board at once.

Moves are safe to make without asking, because each one only follows a fact on GitHub (an
approval or a merge). Columns that QA or a deploy owns are report-only.

## 1. Find the tickets

Pick the JQL from the request:

| Request | JQL |
|---|---|
| No arguments | `assignee = currentUser() AND statusCategory != Done ORDER BY key` |
| A word, such as "zoneless" | `text ~ "<word>" ORDER BY key` (add `OR summary ~ "<synonym>"` when the PR titles use another word, for example zoneless PRs say "OnPush") |
| An epic key | `parent = <EPIC> ORDER BY key` |
| A list of keys | `key in (<keys>)` |

```bash
aikit jira issues search --jql '<jql>' --fields key,summary,status,assignee,parent --limit 100
```

Tickets with no assignee, or in `Dev Requirements`, `To Do`, `Icebox` or `Parking Lot`, are not
started. Count them in the report and do not look for PRs.

## 2. Find each ticket's PR

Match on the ticket key in the PR title. Use `gh pr list`, not `gh search prs`: only
`gh pr list` returns `headRefName` and `baseRefName`.

```bash
gh pr list -R <owner/repo> --state all --limit 200 --search "<KEY>" \
  --json number,title,state,isDraft,reviewDecision,baseRefName,headRefName,mergedAt,author
```

For many tickets, run one search with `--search "<KEY1> OR <KEY2> OR ..."` and map the results
by key. The default repo is the repo of the current directory. When there is none, ask once.

- Ignore PRs whose title starts with "DON'T REVIEW" (proofs of concept). List them in the report.
- A ticket with no PR: check for a branch (`gh api 'repos/<owner/repo>/branches?per_page=100' --paginate --jq '.[].name' | grep -i <key>`). Report "no PR yet" and do not move it.
- A PR that is `CLOSED` but not merged: check whether its head commit is in a merged PR (see `stack-cleanup`). If it is, treat it as merged by that PR.
- `reviewDecision` already accounts for dismissed reviews. Trust it.

## 3. Decide

| Ticket status | PR state | Action |
|---|---|---|
| `In Progress` | Open, not draft | Move to `To Be Reviewed` |
| `To Be Reviewed` | Open, `APPROVED` | Move to `Ready for Staging` |
| `To Be Reviewed` | Open, `CHANGES_REQUESTED` | Report only. Do not move backward |
| `Ready for Staging` | Any | Report only. The deploy moves it (see the `deploy` skill) |
| `On Stage - Ready for Test`, `On Stage - In Test`, `Ready for Prod` | Any | Report only. QA owns these columns |
| `Ready for Prod` | Deployed to prod (see below), or the user says so | Move to `On Prod` |
| `On Prod`, `Ready for Merge` | Merged into the default branch | Move to `Accepted` with "Code Merged, Set as Accepted" |
| Any earlier column | Merged | Report only. The merge does not skip QA |

To check a prod deploy, look for a successful check run whose name starts with
`BuildAndDeploy_Prod` on the PR head commit:

```bash
gh api 'repos/<owner/repo>/commits/<headRefOid>/check-runs?per_page=100' \
  --jq '.check_runs[] | select(.name | startswith("BuildAndDeploy_Prod")) | .conclusion'
```

The full forward order in the WORK project is: To Do, In Progress, To Be Reviewed, Ready for
Staging, On Stage - Ready for Test, On Stage - In Test, Ready for Prod, On Prod, Ready for
Merge, Accepted.

## 4. Move

Always use `--transition-id`. Some targets have two transitions. For example, both "Accepted"
(431) and "Code Merged, Set as Accepted" (351) lead to Accepted, so `--to "Accepted"` fails with
`ambiguous`.

Known IDs in the WORK project:

| Move | ID |
|---|---|
| In Progress to To Be Reviewed ("Ready for Review") | 41 |
| To Be Reviewed to Ready for Staging | 51 |
| Ready for Staging to On Stage - Ready for Test ("Deploy to Staging") | 91 |
| Ready for Prod to On Prod ("Deployed") | 131 |
| Ready for Merge to Accepted ("Code Merged, Set as Accepted") | 351 |

Group tickets by move and apply each group in one call:

```bash
aikit jira issues transitions apply <KEY1> <KEY2> --transition-id 51
```

If an ID fails, list the ticket's transitions and pick the forward one by name:

```bash
aikit jira issues transitions list <KEY>
```

Never pick `Nevermind`, `Back to In Progress`, `Needs More Work`, `Closed` or `Dev Requirements`.
Those move a ticket backward or out of the flow.

## 5. Report

Lead with what moved. Then group the rest, and give one reason per group.

```
Moved 2 tickets to Ready for Staging (PRs approved today):
1. WORK-37877 (#9210)
2. WORK-37879 (#9208)

Already correct:
- Ready for Staging, PR approved: WORK-37874, WORK-37878, ...
- Accepted, PR merged: WORK-37873 (#8915)
- In Progress, no PR yet: WORK-37876

Not started (no assignee, Dev Requirements): 17 tickets. Not changed.
```

End with one next action, for example "Merge #9181 to start the stack."
