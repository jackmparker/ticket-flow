---
name: deploy-prod
description: Use when asked to deploy a moonbeam ticket to production in one step. It first checks that the branch does not pin a component library snapshot (an unmerged or unreleased op-component-library PR); it stops if the library PR must merge first, and bumps moonbeam to the release when one exists. Examples - "deploy 40393 to prod", "ship WORK-40393 to prod and tell Tami", "run deploy-prod on this branch". It runs three skills in order - catch-up (merge master into the branch and push), the aikit deploy skill to prod, then prod-handoff (move the ticket to On Prod and message QA) while the deploy runs. Takes a ticket number, ticket key, PR URL or number, or branch name, and an optional person to message (default Tami). With no ticket, use the branch or PR of the current session. moonbeam only.
---

# Deploy a moonbeam ticket to production

## Overview

One skill for the full prod deploy of a moonbeam ticket. It runs a check and three skills in this order:

1. A check that the branch does not pin a component library snapshot. A library change must be
   merged and released first, and moonbeam must pin the release.
2. `ticket-flow:catch-up` merges master into the branch and pushes.
3. The aikit `deploy` skill deploys the branch to `prod` and waits for the result.
4. `ticket-flow:prod-handoff` starts while the deploy runs. When the deploy succeeds, it moves the
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

Check that no deploy of this branch runs now. The catch-up push in step 3 would cancel it:

```bash
aikit circleci pipelines list --project gh/observepoint/moonbeam --branch <branch> --limit 3
```

If a workflow on this branch is `running`, stop. Tell the user which workflow runs, and wait
until they say go.

## 2. Check the component library version

moonbeam installs `@observepoint/ui-components` from op-component-library. A moonbeam PR that needs
a library change pins a **snapshot**, a build of an unmerged library branch, for example
`0.0.0-dev-20261005201624`. Prod must never ship a snapshot. The library PR merges first, its
release is published, and moonbeam pins that release. This step finds out where that chain stands.

Read the version on the branch and on master:

```bash
gh api "repos/observepoint/moonbeam/contents/package.json?ref=<branch>" --jq .content | base64 -d | jq -r '.dependencies["@observepoint/ui-components"]'
gh api "repos/observepoint/moonbeam/contents/package.json?ref=master" --jq .content | base64 -d | jq -r '.dependencies["@observepoint/ui-components"]'
```

| Branch version | Action |
|---|---|
| Same as master | Go to step 3 |
| A release (`9.12.0`, no `-dev`) newer than master | Go to step 3. Name it in the report |
| A release older than master | Stop. The deploy would roll the library back. Report both versions |
| Not a registry version (`file:`, `workspace:`, a path) | The library lives in moonbeam now. Go to step 3 |
| A snapshot (`-dev-` in it) | Find its library PR, below |

**Find the library PR of a snapshot.** The library's Snapshot Release workflow comments the
version on the PR it built. It edits that one comment for each new snapshot, so only the newest
snapshot is in it:

```bash
gh search prs --repo observepoint/op-component-library "<version>" --json number,title,url,state
```

If that finds nothing, match the time. The last 14 digits of the version are the UTC time the
version step ran (`YYYYMMDDHHmmss`). The run starts earlier, often 10 to 15 minutes, because tests
run first. List the successful runs that started up to 30 minutes before that time, and confirm
each candidate by finding the exact version in its log:

```bash
gh run list -R observepoint/op-component-library --workflow "Snapshot Release" --limit 300 --json headBranch,createdAt,conclusion,databaseId
gh run view <databaseId> -R observepoint/op-component-library --log | grep -c "<version>"
gh pr list -R observepoint/op-component-library --head <headBranch> --state all --json number,title,url,state,mergedAt
```

| Library PR | Action |
|---|---|
| Open, closed without a merge, or no PR for the branch | Stop. Do not deploy. The library PR must merge first |
| Merged, and no release published since | Stop. Do not deploy. The open `chore: version packages` PR in op-component-library publishes the release when it merges |
| Merged, and a release published since | Bump moonbeam to that release (below), then go to step 3 |
| Not found | Stop. Report the version and that no library PR was found |

To find the release, take the oldest `chore: version packages` commit on the library's `main`
after the PR's `mergedAt` (the API lists the newest first, so take the `last`), and read the version
there:

```bash
gh api "repos/observepoint/op-component-library/commits?sha=main&since=<mergedAt>&per_page=100" --jq '[.[] | select(.commit.message | startswith("chore: version packages"))] | last | .sha'
gh api "repos/observepoint/op-component-library/contents/projects/observepoint/ui-components/package.json?ref=<sha>" --jq .content | base64 -d | jq -r .version
```

No such commit means no release yet. Find the open release PR with
`gh pr list -R observepoint/op-component-library --head changeset-release/main`.

**Bump to the release.** In a worktree on the branch (`git worktree add .aikit/worktrees/<label>
<branch>`, or the worktree that already has it), set the exact version in `package.json`, then
run `npm install`, `npm run lint:pkg`, `npx tsc --noEmit --isolatedModules` and
`npx ng build --configuration=development`. If any of them fails, stop and report it; a release can
differ from the snapshot. Commit `<KEY>: Pin ui-components <version> (released from op-component-library #<n>)`
with only `package.json` and `package-lock.json`, and push. The push starts the pipeline that
step 4 deploys.

**When you stop**, report the moonbeam PR, the snapshot version, the library PR and its state, and
what has to happen in order: merge the library PR, merge the `chore: version packages` PR, then run
this skill again (it bumps moonbeam to the release by itself).

## 3. Catch up with master

Invoke the Skill tool with `skill: "ticket-flow:catch-up"` and `args: "<branch>"`.

| Outcome | Action |
|---|---|
| `up-to-date` | Go to step 4 |
| `merged` and pushed | Go to step 4. The push starts a new pipeline. The prod deploy uses it |
| `conflict`, `skipped`, or a failed fast-forward | Stop. Report what catch-up reported. Do not deploy |

## 4. Deploy to prod

Invoke the Skill tool with `skill: "deploy"` and `args: "prod --branch <branch>"`.

- Do not pass `--jira`. `prod-handoff` moves the ticket in step 5.
- Do not pass `--notify`. `prod-handoff` sends the QA message in step 5.
- Do not pass `--no-wait`. The `deploy` skill must wait, because it decides whether the deploy
  succeeded. It reads the deploy job, not the workflow status, and it reports each environment
  in `also_deploys`.

The `deploy` skill can stop before the deploy (for example, another prod deploy runs, or prod
runs a branch that is not merged). Then stop here too. Do not run step 5.

When the `deploy` skill has started the deploy and starts its background wait, go to step 5 at
once. Do not end the turn before step 5 has started.

## 5. Hand off to QA while the deploy runs

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

## 6. Report

Lead with the result.

```
WORK-40393 is on prod.

1. Library: pins ui-components 9.11.0, same as master.
2. Catch-up: merged master into feature/work-40393-toolbar and pushed (12 commits came in).
3. Deploy: pipeline 25075, the prod deploy job passed. https://app.observepoint.com
4. Moved WORK-40393 from Ready for Prod to On Prod. Sent Tami a Slack message to smoke test #9230.

Next: merge #9230 into master after Tami signs off.
```

On failure, name the step that stopped, the reason, and what was not done.
