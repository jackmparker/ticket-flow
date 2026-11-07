# ticket-verify

`ticket-verify` proves that a ticket's code works and reads well before you commit it. It is
picky on purpose: it is your own code, and reviewers comment on small things. `start` runs it
twice per ticket. You can also run it alone: "verify this ticket", "is 40393 ready for a PR".

The skill itself is `skills/ticket-verify/SKILL.md`. This page explains every check in it.

## The two phases

| Phase | When | What happens |
|---|---|---|
| **Plan** | Right after `jira-start`, before any code | A QA agent reads the ticket, writes an adversarial test plan, and records the "before" state |
| **Verify** | When the code is written | Gates, test proof, QA rounds, code review, fixes, final check, then the report. Jira gets the evidence only after your yes |

The skill picks the phase by itself: no change against the base branch means Plan, any change
means Verify.

The QA agent and the review agents start with a fresh context. They get the ticket, the plan, the
diff and file paths, and nothing of the coding agent's reasoning, because an agent that reads why
the code is right tends to agree with it.

## Every check at a glance

| Check | What it proves | Fails when |
|---|---|---|
| [Test plan](#test-plan) | Every acceptance criterion has a case, and the change was attacked from many sides | (Written in Plan, run in Verify) |
| [Gates](#gates) | The code compiles, passes lint and its specs | Any error |
| [Test proof](#test-proof) | Each new or changed spec really tests the change | A spec still passes with the old code |
| [QA run](#qa-run) | Every case in the plan works in the browser or against the API | A case fails |
| [New console errors](#new-console-errors) | The change adds no browser errors or failed requests | An error or failed request that the base does not have |
| [Accessibility scan](#accessibility-scan) | The change adds no accessibility problem | A rule fails that did not fail on the base, or fails on more elements |
| [Screen compare](#screen-compare) | Screens the ticket did not mean to change still look the same | A changed pixel the ticket did not ask for |
| [Code review](#code-review) | The code is what this repo's reviewers want, checked by Claude and by Gemini | Any finding (all are fixed) |
| [Final check](#final-check) | The code that will be committed works and builds for production | A gate, the production build or a final QA case fails |

## Test plan

The QA agent writes `plan.md`: one table row per case (id, area, steps, expected result, why it
matters). The plan fits the size of the change: about 10 cases for a small fix, one case per
risk. A case that depends on time (retries, timeouts) makes the failure happen at once instead of
waiting; one that still needs more than a minute of waiting goes to the specs. Acceptance criteria
come first. Then it tries to break the change:

- Empty, very long, special-character and boundary inputs; zero, one and many items.
- Read-only users, other permission levels, a shared-link visitor.
- Double clicks, fast repeat actions, back and forward, reload in the middle of a flow.
- Slow or failed requests, and what the screen shows then.
- Light and dark theme when colors or styles change.
- Narrow screens (390 px and 768 px wide), when the screen already works at a narrow width, when
  people reach it on phones, or when the ticket is about a narrow screen. A screen built for
  desktop only is skipped. In moonbeam, most screens are desktop only, so most moonbeam tickets
  skip this. The plan states the decision and the reason for each screen.
- Screens next to the change that use the same component, service or endpoint.
- Backend: invalid and missing fields, wrong types, unknown ids, duplicate requests, permission
  checks, large payloads, and the effect on existing data and callers.
- Every entry in the repo's "missed by QA" list that fits the change (see
  [Where the lessons come from](#where-the-lessons-come-from)).

**Before state.** Screenshots of only what the ticket changes visually, cropped to the changed
area. There is no fixed number: one pair per distinct visual change, and no repeats of the same
change on other screens. They come from `https://master.observepointstaging.com` when its
`master` is the branch's base, otherwise from the base run locally. A backend change records the current request and
response for each case instead.

**Test data.** QA uses an existing test account first, else creates its own data, and deletes
what it created at the end. It never changes existing data in a way that starts real work (audit
or journey runs, scans, schedules, exports, emails, alerts). On 2026-11-06, unpausing paused test
audits started three real runs. For such actions it uses its own data, or intercepts the request.

## Gates

The repo's fast checks, before QA spends time on a broken build. In moonbeam:

```bash
npx tsc --noEmit --isolatedModules
npx eslint <changed files>
./scripts/ai/run-tests.sh -i '<changed folders>/**/*.spec.ts'
```

## Test proof

A test that passes with and without the change proves nothing. For the specs the change adds or
changes:

1. `test-proof.sh swap` saves the changed source files (not the specs) and the current
   `git diff`, puts the base version of each one in its place, and deletes new source files.
2. Run those specs. Each new or changed spec file must have at least one failing case.
3. `test-proof.sh restore` puts the saved files back and checks that `git diff` is exactly what
   it was.

The script takes each file as its own argument. A file list in a shell variable broke this step
twice on 2026-11-06: zsh did not split the list, so nothing was swapped.

A spec that still passes gets fixed so it tests the change. A spec for a pure refactor may pass;
the report says so. The result is a case in the plan, area "Test proof".

## QA run

A fresh QA agent runs every case in its own browser window (`BU_CLIENT=<session>-qa`, in the
headless agent Chrome, against the checkout's own dev server), or against the API for a backend
change. It writes `runs/round-<n>.md`: each case's result and what it saw, and new problems it
found outside the plan, added as new cases.

The coding agent fixes failures, runs the gates again, and starts a new round with the failed cases
and the cases next to them. After round 3, if cases still fail, it stops and asks you.

### New console errors

Every browser console error and every failed request (status 4xx or 5xx) on a page the change
touches is compared with the same steps on the base. An error that only the branch has is a failed
case, not a note.

### Accessibility scan

UI changes only. On each page the change touches, the QA agent runs axe-core (a standard
accessibility checker for the WCAG 2.2 AA rules) on the base and on the branch, in the same state:

```bash
browser-harness -c "claim_tab('<url>'); exec(open('<skill folder>/a11y_scan.py').read()); print(a11y_scan())"
```

It prints each failing rule with its impact, the number of elements and up to 3 of them. A rule
that is new on the branch, or fails on more elements, is a failed case. Problems that were there
before are not this ticket's, but the report lists them.

### Screen compare

UI changes only. The QA agent finds every screen that uses what the change touches: changed
components (by their selectors in templates), shared styles and services. Up to 10 screens, most
used first. On each, it takes a full-page screenshot on the base and on the branch, with the same
window size, account, data and scroll, in light and dark theme, and compares them:

```bash
<skill folder>/screen-diff.py before.png after.png diff.png
```

The script prints how many pixels changed and the box around them, and writes a diff image with
the changed pixels in red. A change on a screen, or a part of a screen, that the ticket does not
mean to change is a failed case. The diff images stay in the evidence folder (`compare/`).

## Code review

Only after QA passes.

- **Full level:** the aikit `code-review` skill, all review areas, on the full diff against the
  base. It gets the ticket, the plan, the repo's review patterns file and its "missed by QA"
  list, and is told to report every finding, style and minor ones included, against every
  pattern.
- **Light level:** one fresh reviewer that checks the diff against every pattern of every kind and
  the "missed by QA" list.

- **Second reviewer, Gemini:** when the Antigravity provider is on in T3 Code, a Gemini model
  (Gemini 3.8 Flash) reviews the same diff at the same time, read only, with the same ticket, plan,
  patterns and QA misses. A different model misses different things. The coding agent checks each
  Gemini finding against the code first: real ones are fixed, wrong ones are listed as not changed
  with the reason. Gemini never blocks a ticket. The review goes on without it, and the report says why, when
  the provider is off or signed out, T3 Code is not in use, the call fails or hits a rate limit or
  quota (one retry at most), it gives no usable findings, or it is still running 15 minutes after
  the rest of the review is done.

Every finding is fixed. `review.md` lists each one as `fixed`, `not changed` (only with a reason
you would accept, never "minor") or `asked user`. A fix that changes behavior or a screen sends the
touched cases back to QA.

## Final check

After the last fix:

1. The gates again, and the test proof again when specs changed after it ran.
2. A production build. moonbeam: `npx ng build --configuration=prod`. It catches template, type
   and size-limit errors that the dev server misses.
3. One fresh QA run of the acceptance-criteria cases and every case that failed in an earlier
   round. The final "after" screenshots come from this run.

## Levels

Full is the default. Light is only for one or two files with no new logic (copy, a style value, a
config value, a rename) and no change to an API, a database, permissions or a shared component.

| Step | Full | Light |
|---|---|---|
| Test plan | Adversarial plan, all categories | Happy path plus the 2 riskiest cases |
| Review | `code-review` skill, all areas | One reviewer, every pattern and the QA misses list |
| Test proof, new console errors, production build | Yes | Yes |
| Screen compare, accessibility scan | Yes, for UI changes | Only the screens the change touches |
| Screenshots in the report | One pair per visual change, cropped | Usually one, cropped |

## Evidence folder

Everything for a ticket is in `<worktree>/.aikit/ticket-verify/<KEY>/` (gitignored):

```
ticket.md            the ticket text, acceptance criteria and linked pages
plan.md              the test plan
before/  after/      screenshots, same names in both
proof/               test proof backup
compare/             screen compare diff images
runs/round-<n>.md    each QA run
review.md            review findings and what was done with each
report.json          the facts for the report
<KEY>-verify-<date>.pdf, comment.json, <KEY>-verify-<date>-logs.txt
```

## What goes to Jira

Nothing until you say yes. First the skill shows you, in the thread: the result, the QA rounds, the
review counts, a link to the PDF, every before and after screenshot, and the exact comment text.
Then it asks one question: commit, post to Jira and open the PR?

On a yes, the ticket gets **one comment from you** (posted with your aikit Jira login) with a short
summary and the PDF in it. The PDF (`build-report.py`) holds the result, what was found and fixed,
what is still open, review findings not changed with the reason, the full test plan as one table
(final result per case, with its result in each round), and one cropped before and after pair
per visual change. Long text (logs, full API bodies) goes to a separate `-logs.txt` file. Secrets and customer
data are removed first.

## Where the lessons come from

| File | What it holds | Written by |
|---|---|---|
| `references/review-patterns/<repo>.md` | Patterns from past human review comments in the repo. Each has a kind: breaks, theme, quality or style. `ticket-verify` uses all four | `refresh-patterns` (every 90 days, or on request), and `fix` for new review comments |
| `references/qa-misses/<repo>.md` | Bugs QA found after `ticket-verify` passed, each with the test that finds it | `fix`, for each QA bug |

## Scripts

| Script | What it does |
|---|---|
| `build-report.py` | Builds the PDF, the logs file and the Jira comment from `report.json`, and embeds the uploaded files in the comment |
| `a11y_scan.py` | Runs axe-core on the current page inside browser-harness. Downloads axe-core 4.10.2 once to `~/.cache/ticket-verify/` |
| `screen-diff.py` | Compares two screenshots and writes a diff image |
| `test-proof.sh` | Swaps in the base versions of changed source files for the test proof, and puts them back |

## Requirements

- The aikit CLI (Jira) and the aikit `code-review` skill.
- For the Gemini reviewer: T3 Code with the Antigravity provider on and signed in (the company's
  Gemini Enterprise plan covers it).
- For UI QA in moonbeam: [agent-dev-setup](https://github.com/jackmparker/agent-dev-setup), which
  gives each agent its own dev server (`moonbeam-dev`) and its own window in the headless agent
  Chrome.
- Python 3 with Pillow (for `screen-diff.py`), and Google Chrome (for the PDF).
