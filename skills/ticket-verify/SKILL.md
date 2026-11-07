---
name: ticket-verify
description: Use to prove a ticket's code change works and reads well before it is committed. Examples - "verify this ticket", "run ticket-verify on 40393", "QA and review my changes", "is this ready for a PR". Run it twice per ticket - once right after jira-start (the QA agent writes the test plan and takes before screenshots), and again when the code is written (QA tries to break it in the browser or against the API, a review team checks the diff against the repo's patterns and past PR comments, fixes go in, a final check runs, and the report PDF and screenshots are shown to the user). It ends by asking whether to commit, attach the evidence to Jira and open a PR, and touches Jira only after a yes: one PDF attachment and one short comment. Takes a ticket key or number; with none, use the ticket of the current session.
---

# Verify a ticket before the PR

## Overview

Two phases, run by two calls of this skill:

| Phase | When | What happens |
|---|---|---|
| **Plan** | Right after `jira-start`, before any code | A QA agent reads the ticket, writes an adversarial test plan, and records the "before" state |
| **Verify** | When the code for the ticket is written | Gates, QA run, code review, fixes, final check, show the evidence, ask, then attach to Jira on a yes |

Pick the phase from the worktree: no changes against the base yet (`git diff origin/<base>` is
empty, counting uncommitted edits) means **Plan**; any change means **Verify**. If **Verify** starts and no plan exists, run **Plan** first. The
"before" state then comes from the base branch, never from the changed code.

The user's global rules still apply: work in your own worktree, never steal browser focus, never
open SSO pages, ask before any commit or PR.

### Independent agents

The QA agent and the review agents are subagents with a fresh context. Give them the ticket, the
plan, the diff and the paths below, and nothing of your own reasoning about the code. An agent that
reads why the code is right tends to agree with it. Do not tell them what you expect them to find.

### Picky by design

This is the user's own code, and reviewers comment on small things. Be nitpicky: a finding that a
teammate's review (`pr-review`) would skip still gets fixed here. Every agent reports every
finding it sees, style and minor ones included. You fix every finding. Write `not changed` only
with a reason the user would accept (for example "the ticket asks for this exact text"), never
"minor" or "out of scope" for code the diff adds or changes.

### Evidence folder

Keep everything for the ticket in `<worktree>/.aikit/ticket-verify/<KEY>/` (`.aikit/` is
gitignored):

```
ticket.md            ticket text, acceptance criteria and linked pages
plan.md              the test plan
before/  after/      screenshots, same names in both (01-reports-gallery.png)
runs/round-<n>.md    each QA run: case results, console errors, failed requests
review.md            review findings and what was done with each
proof/  compare/     test proof backup; screen compare images (step 3)
report.json          the facts for the report (format in build-report.py)
<KEY>-verify-<date>.pdf, comment.json   built by build-report.py; what goes to Jira
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
   QA misses file: `references/qa-misses/<repo>.md` in this skill folder, when it exists. It lists
   bugs that QA found after this skill passed a ticket (the `fix` skill adds them).
5. Kind of change:
   - **UI**: the repo serves screens (moonbeam, op-component-library). QA runs in the browser.
   - **Backend**: everything else. QA runs against the API, the CLI or the tests.
6. Level. **Full** is the default. Use **Light** only when all of these are true, and say why in
   the report: one or two files, no new logic (copy, a style value, a config value, a rename), and
   no change to an API, a database, permissions or a shared component.

| Step | Full | Light |
|---|---|---|
| Test plan | Adversarial plan, all categories in step 2 | Happy path plus the 2 riskiest cases |
| Review | `code-review` skill, all areas | One reviewer subagent that checks every pattern of every kind and the QA misses list |
| Test proof, new console errors, production build | Yes | Yes |
| Screen compare, accessibility scan | Yes, for UI changes | Only for the screens the change touches |
| Screenshots | Visual changes only, at most 3, cropped | One, cropped |

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
- Give the QA agent the QA misses file (step 1) when it exists. For each entry that fits the
  change, add its test as a case. These are bugs that past QA runs missed.

**"Before" state.**
- UI: screenshots only of what the ticket will change visually, before the change: at most 3,
  each cropped to the area that changes (`Page.captureScreenshot` with a `clip` around the element),
  not the whole screen. A behavior change with no visual difference gets no screenshot; its test
  case is the proof. Use
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

**Test proof.** A test that passes with and without the change proves nothing. For the specs the
change adds or changes:

1. Save the changed source files (not the specs) to `<evidence>/proof/backup/`, and save
   `git diff` to `<evidence>/proof/diff-before.patch`.
2. Write the base version of each changed source file in its place
   (`git show origin/<base>:<path> > <path>`). A new source file: delete it.
3. Run those specs. Each new or changed spec file must have at least one failing case.
4. Put the saved files back from the backup, and check that `git diff` is the same as
   `diff-before.patch`. Stop and report if it is not.

A spec that still passes does not test the change: make it test the change, then run the proof
again. A spec for a pure refactor (no behavior change) may pass; say so. Record the result as a
case in `plan.md` (area "Test proof").

### 3.2 QA run

Start the QA subagent again, fresh, with `plan.md`, the diff (`git diff <base>...HEAD`), the
evidence folder and the round number. It runs every case and writes `runs/round-<n>.md`:

- Each case: pass or fail, and what it saw. Screenshots only for the visual changes planned in
  step 2, plus one for a failure whose cause is visual.
- Every browser console error and every failed network request (status 4xx or 5xx) that it met,
  with the page or request where it happened, even when the case passed.
- New problems it found outside the plan, added as new cases.
- **New console errors fail.** A console error or failed request on a page the change touches,
  which the same steps do not cause on the base (`https://master.observepointstaging.com` when its
  `master` is the base), is a failed case, not a note.
- **Accessibility scan** (UI). On each page the change touches, run
  `<this skill folder>/a11y_scan.py` (axe-core, a standard accessibility checker) on the base and
  on the branch, in the same state: `exec(open('<path>').read()); print(a11y_scan())` inside
  browser-harness. A rule that is new on the branch, or fails on more elements, is a failed case.
  Problems that were there before are not this ticket's, but list them in the report.
- **Screen compare** (UI). Find every screen that uses what the change touches: the changed
  components (search the templates for their selectors), shared styles and services. Up to 10
  screens, most used first. On each, take a full-page screenshot on the base and on the branch,
  with the same window size, account, data and scroll, in light and dark theme, and run
  `<this skill folder>/screen-diff.py <before> <after> <diff>`. A changed pixel on a screen, or a
  part of a screen, that the ticket does not mean to change is a failed case: look at the diff
  image and name what moved. Save the diff images in `<evidence>/compare/`. They do not go to
  Jira unless a failure needs one.

UI: the QA agent uses browser-harness with its own client id, so it never shares your window:
`BU_CLIENT=<session id>-qa browser-harness -c '...'`. It starts each call with `claim_tab()`,
uses the checkout's `moonbeam-dev url`, takes the "after" screenshots with the same names and the
same crop as the "before" ones, and calls `release_tab()` when done.

Backend: it runs the service or tests locally, calls the endpoints or commands for each case, and
records request, status and body.

**Failures.** Fix them (you, not the QA agent), run the gates again, and start a new QA round with
the failed cases plus the cases next to them. Stop after round 3 if cases still fail: report what
fails and ask the user.

### 3.3 Code review

Only after QA passes.

- **Full:** invoke the Skill tool with `skill: "code-review"`, delegated mode, and the full diff
  against the base: `--mode delegated --scope full --base origin/<base>`. In `--prompt`, give only
  paths: `ticket.md`, `plan.md`, the patterns file and the QA misses file, plus one line: "Report
  every finding, style and minor ones included, and check the diff against every pattern in the
  patterns file." Do not explain or defend the change.
- **Light:** one fresh subagent reads the diff, `ticket.md`, the patterns file and the QA misses
  file, checks the diff against every pattern of every kind, and reports every finding with file
  and line.

**Second reviewer: Gemini** (Full and Light, when available). A different AI model misses
different things. In T3 Code, call `mcp__t3-code__orchestrator_capabilities` (load it with
ToolSearch). When the `antigravity` provider has `canRunChildTask: true` and a Gemini model (for
example `gemini-3.8-flash`), start it at the same time as the review above, with
`mcp__t3-code__delegate_task`: `target: {providerInstanceId: "antigravity", model: "<gemini model>",
options: {thinking_level: "high"}}`, `role: "review"`, `mode: "async"`, title
"Gemini review <KEY>". Its task, with absolute paths:

```
You are a code reviewer. Read only: do not change files, commit or post anything.
The change: git -C <worktree> diff origin/<base>   (uncommitted edits count)
Read the files around it in <worktree>. Also read: <evidence>/ticket.md, <evidence>/plan.md,
<patterns file>, <QA misses file>.
Report every finding: bugs, edge cases, accessibility, missing or weak tests, unclear names,
anything a careful reviewer would comment on. For each: file and line, what is wrong, the fix,
in two sentences at most. End with how many files you read.
```

Gemini is a second opinion, not a judge: check each of its findings against the code before you
act. A real one is fixed like any other finding. One that is wrong goes in `review.md` as
`not changed` with why it is wrong. Mark each Gemini finding "(Gemini)".

**Gemini is optional. It never blocks the ticket.** Skip it, go on with the rest of the review,
and write one line in the report ("Gemini review: skipped, <reason>") when:

- T3 Code's tools are missing (not in T3 Code), or the `antigravity` provider is off, signed out,
  has `canRunChildTask: false`, or lists no Gemini model.
- `delegate_task` returns an error, or the child fails, is cancelled, or reports a rate limit, a
  quota or a sign-in problem. Do not retry more than once.
- It has not finished when the rest of the review is done and fixed. Wait at most 15 minutes
  after that, then cancel it (`mcp__t3-code__task_cancel`) and skip it.
- It returns no file and line for its findings, or read no files. Treat that as no review.

Write `review.md`: each finding, then `fixed`, `not changed` with the reason, or `asked user`. Fix
the confirmed findings. A finding that changes behavior or a screen sends you back to 3.2 for the
cases it touches.

### 3.4 Final check

After the last fix: gates again, the test proof again when specs changed after it ran, and a
production build (moonbeam: `npx ng build --configuration=prod`; other repos: their release build).
It catches template, type and size-limit errors that the dev server does not. Then one fresh QA run
of the acceptance-criteria cases and every case that failed in an earlier round. Take the final "after" screenshots in this run, so they show
the code that will be committed.

### 3.5 Report

Jira gets two things: one PDF with all the evidence, and one short comment. Never attach loose
screenshots or logs.

1. Write `report.json` in the evidence folder, from `plan.md`, the last QA run and `review.md`.
   The format is at the top of `build-report.py` (in this skill folder). "found_fixed" holds what
   QA found and the review fixes that changed behavior, one line each: what broke, and what it does
   now. Wording and naming nitpicks go in "review" only. "still_open" is never left out; an empty
   list prints "None".
2. Remove secrets from `report.json` and the screenshots now: tokens, cookies, `accessKey` values,
   API keys, passwords, and customer data that is not test data. Jira is visible across the company.
3. Build: `python3 <this skill folder>/build-report.py <evidence folder>`. It writes
   `<KEY>-verify-<date>.pdf`, one to three pages: the result, found and fixed, still open, review
   findings not changed (with the reason), the full test plan as one table (final result per case, with
   a short round history), then the before and after pairs. Long text (logs, full API bodies) goes to `<KEY>-verify-<date>-logs.txt` instead. It also
   writes `comment.json`, the short Jira comment, and prints what to attach as JSON ("attach").
   The test plan is ONE table: each case once, with its steps, expected result and final result,
   and its result in each round from `runs/round-<n>.md` ("rounds"). Never one table per round.

Do not touch Jira yet. No attachment and no comment until the user says yes in 3.6.

### 3.6 Show the evidence and ask

Show the user, in the thread:

- The result line, the QA rounds, and the count of review findings fixed and not changed.
- A link to the PDF (absolute path), so they can open it.
- Every screenshot pair, embedded as images with absolute paths, before then after, each with its
  one line on what changed: `![before](/abs/path/before/01-x.png) ![after](/abs/path/after/01-x.png)`.
  For a backend change, the request and response pairs instead.
- The comment text exactly as it will be posted.

Then ask one question: commit, attach the PDF and post the comment on the Jira ticket, and open the
PR? Do not commit, push or touch Jira before a yes. If the user asks for changes to the code, the
report or the screenshots, make them, run what they affect again (3.2 to 3.4), build the report
again, and show it again.

On a yes, post to Jira first, then hand back to the caller (or commit and open the PR yourself when
run alone). The ticket gets ONE comment from the user, with the summary and the PDF in it, not a
loose attachment. `aikit jira` uses the user's own Jira login, so the comment is posted as them.

```bash
aikit jira attachments add <KEY> --file <each path in "attach"> > <evidence folder>/attach-result.json
python3 <this skill folder>/build-report.py --embed <evidence folder> <evidence folder>/attach-result.json
aikit jira issues comment <KEY> --adf <evidence folder>/comment.json
```

The first command uploads the PDF (and the `-logs.txt` file when there is one). The second puts
them into `comment.json` as file cards at the end, right below its last line: "For full details and
before and after screenshots, see the attached PDF". Every comment ends with that line. The third posts the one
comment. If an upload fails, `--embed` stops: upload the failed file again, then run `--embed`
again. Post the comment once per yes; do not post a second comment for the same report.

"attach" holds the PDF, and the `-logs.txt` file only when there was long text (logs, full API
bodies). Keep long text out of the PDF: `build-report.py` moves it to that file.

### 3.7 Clean up

`release_tab()` for every client id you or the QA agent used, `moonbeam-dev stop` for any server
started only for this skill (the base-branch server in step 2), and delete test data you created.
