---
name: ticket-verify
description: Use to prove a ticket's code change works and reads well before it is committed. Examples - "verify this ticket", "run ticket-verify on 40393", "QA and review my changes", "is this ready for a PR". Run it twice per ticket - once right after jira-start (the QA agent writes the test plan and takes before screenshots), and again when the code is written (QA tries to break it in the browser or against the API, a review team checks the diff against the repo's patterns and past PR comments, fixes go in, a final check runs, and the report and screenshots are attached to the Jira ticket). It ends by asking whether to commit and open a PR. Takes a ticket key or number; with none, use the ticket of the current session.
---

# Verify a ticket before the PR

## Overview

Two phases, run by two calls of this skill:

| Phase | When | What happens |
|---|---|---|
| **Plan** | Right after `jira-start`, before any code | A QA agent reads the ticket, writes an adversarial test plan, and records the "before" state |
| **Verify** | When the code for the ticket is written | Gates, QA run, code review, fixes, final check, Jira attachments, then ask to commit |

Pick the phase from the worktree: no changes against the base yet (`git diff origin/<base>` is
empty, counting uncommitted edits) means **Plan**; any change means **Verify**. If **Verify** starts and no plan exists, run **Plan** first. The
"before" state then comes from the base branch, never from the changed code.

The user's global rules still apply: work in your own worktree, never steal browser focus, never
open SSO pages, ask before any commit or PR.

### Independent agents

The QA agent and the review agents are subagents with a fresh context. Give them the ticket, the
plan, the diff and the paths below, and nothing of your own reasoning about the code. An agent that
reads why the code is right tends to agree with it. Do not tell them what you expect them to find.

### Evidence folder

Keep everything for the ticket in `<worktree>/.aikit/ticket-verify/<KEY>/` (`.aikit/` is
gitignored):

```
ticket.md            ticket text, acceptance criteria and linked pages
plan.md              the test plan
before/  after/      screenshots, same names in both (01-reports-gallery.png)
runs/round-<n>.md    each QA run: case results, console errors, failed requests
review.md            review findings and what was done with each
report.md            the summary that goes to Jira
```

## 1. Resolve the ticket, repo and level

1. Ticket key: from the argument, else from the branch name (`aikit repo tickets`), else ask.
2. Write `ticket.md`: `aikit jira extract <KEY> --linked`, then keep the summary, description,
   acceptance criteria and QA steps.
3. Repo: the name of the `origin` remote (`moonbeam`, `observepoint-mcp`, `authentication`, ...).
4. Patterns file: `references/review-patterns/<repo>.md` in this skill folder, or a file whose
   intro says it also covers this repo (`grep -l <repo> references/review-patterns/*.md`). If none
   exists for the repo, the review runs without one; say so in the report. Read its "Built on" date. When it
   is more than 90 days old, or no file exists, start a background subagent (`run_in_background`)
   that invokes the Skill tool with `skill: "ticket-flow:refresh-patterns"` and `args: "<repo>"`,
   and go on with the file you have. Do not wait for it. Also apply the entries under
   `## New, not yet grouped` in the file: they are recent misses that no pattern holds yet.
5. Kind of change:
   - **UI**: the repo serves screens (moonbeam, op-component-library). QA runs in the browser.
   - **Backend**: everything else. QA runs against the API, the CLI or the tests.
6. Level. **Full** is the default. Use **Light** only when all of these are true, and say why in
   the report: one or two files, no new logic (copy, a style value, a config value, a rename), and
   no change to an API, a database, permissions or a shared component.

| Step | Full | Light |
|---|---|---|
| Test plan | Adversarial plan, all categories in step 2 | Happy path plus the 2 riskiest cases |
| Review | `code-review` skill, all areas | One reviewer subagent with the patterns file |
| Screenshots | Every changed screen and state | The changed screen |

## 2. Plan phase: the QA agent writes the plan

Start one subagent (`general-purpose`). Brief it with the ticket file, the kind of change and the
evidence folder, and ask for `plan.md` and the "before" state. The plan:

- One table row per case: id, area, steps, expected result, why it matters.
- Acceptance criteria first, one or more cases each.
- Then try to break it. Pick the categories that fit the change:
  - Empty, very long, special-character and boundary inputs; zero, one and many items.
  - Read-only users and other permission levels; a shared-link visitor.
  - Double clicks, fast repeat actions, back and forward, reload in the middle of a flow.
  - Slow or failed requests, and what the screen shows then.
  - Light and dark theme, when colors or styles change. Desktop width only.
  - Screens next to the change that use the same component, service or endpoint.
  - Backend: invalid and missing fields, wrong types, unknown ids, duplicate requests, permission
    checks, large payloads, and the effect on existing data and callers.
- No mobile cases unless the ticket is about a narrow screen.

**"Before" state.**
- UI: screenshots of each screen and state the plan covers, before the change. Use
  `https://master.observepointstaging.com` when its `master` is the branch's base. Otherwise run
  the base in its own worktree with `moonbeam-dev start`. Same window size, account, data and
  theme as the "after" shots will use.
- Backend: the current response or behavior for each case (request, status, body), from staging
  or from the base branch run locally.

**Test data.** Use the account and data rules in the user's memory: an existing test account
first, else create the data, and delete what you create at the end. Never use production data.

## 3. Verify phase

### 3.1 Gates

Run the repo's fast checks before QA spends time on a build that does not compile: type check,
lint on the changed files, and the specs for the changed folders. In moonbeam:
`npx tsc --noEmit --isolatedModules`, `npx eslint <changed files>`,
`./scripts/ai/run-tests.sh -i '<changed folders>/**/*.spec.ts'`. Fix failures before QA.

### 3.2 QA run

Start the QA subagent again, fresh, with `plan.md`, the diff (`git diff <base>...HEAD`), the
evidence folder and the round number. It runs every case and writes `runs/round-<n>.md`:

- Each case: pass or fail, what it saw, and the screenshot or response for it.
- Every browser console error and every failed network request (status 4xx or 5xx) that it met,
  with the page or request where it happened, even when the case passed.
- New problems it found outside the plan, added as new cases.

UI: the QA agent uses browser-harness with its own client id, so it never shares your window:
`BU_CLIENT=<session id>-qa browser-harness -c '...'`. It starts each call with `claim_tab()`,
uses the checkout's `moonbeam-dev url`, takes the "after" screenshots under the same names as the
"before" ones, and calls `release_tab()` when done.

Backend: it runs the service or tests locally, calls the endpoints or commands for each case, and
records request, status and body.

**Failures.** Fix them (you, not the QA agent), run the gates again, and start a new QA round with
the failed cases plus the cases next to them. Stop after round 3 if cases still fail: report what
fails and ask the user.

### 3.3 Code review

Only after QA passes.

- **Full:** invoke the Skill tool with `skill: "code-review"`, delegated mode, and the full diff
  against the base: `--mode delegated --scope full --base origin/<base>`. In `--prompt`, give only
  paths: `ticket.md`, `plan.md`, and the patterns file. Do not explain or defend the change.
- **Light:** one fresh subagent reads the diff, `ticket.md` and the patterns file, and reports
  findings with file and line.

Write `review.md`: each finding, then `fixed`, `not changed` with the reason, or `asked user`. Fix
the confirmed findings. A finding that changes behavior or a screen sends you back to 3.2 for the
cases it touches.

### 3.4 Final check

After the last fix: gates again, then one fresh QA run of the acceptance-criteria cases and every
case that failed in an earlier round. Take the final "after" screenshots in this run, so they show
the code that will be committed.

### 3.5 Report and Jira

Write `report.md`, short enough to read in two minutes:

1. Result: ready, or not ready and why.
2. Level and why; repo; base commit and head commit.
3. Test plan table with the final result of each case, and the number of QA rounds.
4. Problems QA found and how each was fixed.
5. Review findings and what was done with each.
6. Console errors and failed requests still seen, if any, and why they are not from this change.
7. Screenshot pairs: before and after file names, one line on what changed.

Before you attach anything, remove secrets from the report and screenshots: tokens, cookies,
`accessKey` values, API keys, passwords, and customer data that is not test data. Jira is visible
across the company.

Attach: `aikit jira attachments add <KEY> --file report.md --file before/<file> --file after/<file> ...`
Name the report `<KEY>-verify-<date>.md` so a second run does not look like the first. Do not
attach `runs/` or raw logs; the report holds what matters from them.

### 3.6 Ask

Show the user: the result line, the QA rounds, the count of review findings fixed and not changed,
and the Jira link. Then ask whether to commit and open a PR. Do not commit or push before a yes.

### 3.7 Clean up

`release_tab()` for every client id you or the QA agent used, `moonbeam-dev stop` for any server
started only for this skill (the base-branch server in step 2), and delete test data you created.
