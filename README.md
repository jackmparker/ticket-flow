# ticket-flow

Take a Jira ticket from start to Accepted: write and verify the code, review teammates' PRs, fix
what reviewers and QA find, deploy to staging and prod, and merge. Each step moves the Jira
tickets for you, and the skills learn from every review comment and QA bug.

A [Claude Code](https://claude.com/claude-code) plugin with thirteen skills. Ask in plain words,
or run a skill directly, for example `/ticket-flow:deploy-staging 41083`.

## The life of a ticket

```
start ──> ticket-verify ──> PR ──> fix (review comments) ──> deploy-staging ──> fix (QA bugs)
                                                                  │
            Accepted <── merge <── Ready for Merge <── prod-handoff <── deploy-prod
```

1. `start 41083` writes the code in its own worktree, verifies it, and asks you about the commit
   and PR.
2. `fix` answers review comments. `pr-review` reviews your teammates' PRs.
3. `deploy-staging 41083` deploys to US2 and moves the ticket to On Stage.
4. QA sends a ticket back to Waiting for Fix: `fix 41083` fixes it and redeploys when needed.
5. `deploy-prod 41083` deploys, moves the ticket to On Prod, tells QA, then waits for Ready for
   Merge and merges.

A combined PR (several tickets' branches merged into one PR) and a stack of PRs work at every step.

## Skills

### Your daily thread

| Skill | What it does | Say something like |
|---|---|---|
| `thread` | Makes this thread your "Ticketflow Tasks" thread: renames it, pins it in T3 Code, and unpins and settles the older one. Every later command runs in a fresh agent (a child thread in T3 Code), so earlier commands never fill its context. It shows you drafts and questions, sends your answers to the right agent, and lists what still runs. | "/ticket-flow:thread" |

### Do a ticket

| Skill | What it does | Say something like |
|---|---|---|
| `start` | Does a ticket end to end: creates a worktree, runs the aikit `jira-start` skill, has `ticket-verify` write the test plan, writes the code, runs `ticket-verify` again, shows you the report and screenshots, and asks about the commit and PR. It renames the T3 Code thread to the ticket key and summary. For a backend ticket it stops once before the code to show you the design decisions. | "Start 40393" |
| `ticket-verify` | Run twice per ticket. First, a QA agent writes an adversarial test plan (with the repo's "missed by QA" cases) and records the "before" state. Then it runs the fast checks, has QA try to break the change in the browser or against the API, reviews the code against the repo's review patterns, fixes the findings, and shows you a short PDF report. Jira gets the PDF in one comment, only after your yes. | "Verify this ticket" |

### Review and fix

| Skill | What it does | Say something like |
|---|---|---|
| `pr-review` | Reviews a teammate's PR, or every PR waiting on you, and posts comments as you only after you see the full draft. It comments on what breaks, on documented theme rules, and on at most 2 code quality problems with a real cost, never on style. It uses the repo's review patterns and "missed by QA" list, checks the PR against its Jira ticket and for swapped components, skips what other reviewers already said, and learns from the comments you cut. | "Review 9301", "Review my queue" |
| `fix` | Fixes review comments on your PRs and bugs QA reported in Jira (tickets in Waiting for Fix). It skips a bug that is already fixed and on its way, reproduces a QA bug first, fixes it in the ticket's own branch, checks it, and carries the fix into combined branches and up stacks. Then it decides what comes next: push only, or redeploy to the staging environment that still runs the ticket. It replies on GitHub or with a short Jira comment, and records what reviewers and QA caught. | "Fix 41060", "Address the review comments" |

### Deploy and finish

| Skill | What it does | Say something like |
|---|---|---|
| `deploy-staging` | moonbeam only. Merges master into the branch, deploys to US2 (or another environment you name) without waiting for the pull request checks, and when the deploy lands sets the Environment field and moves the tickets to On Stage - Ready for Test. A ticket in Waiting for Fix moves only when named as fixed. It fixes a failed check and deploys again. For an environment other than US2, it first stops if QA tests someone else's tickets there. | "Deploy 41083 to staging", "Send 9442 to us8" |
| `deploy-prod` | moonbeam only. Checks that the branch does not pin an unreleased component library build, runs `catch-up`, deploys to prod with the aikit `deploy` skill, and runs `prod-handoff`. | "Deploy 40393 to prod" |
| `prod-handoff` | Waits for a prod deploy. When it lands, moves every ticket to On Prod, sends QA (Tami by default) one Slack message to smoke test, and starts `merge` in watch mode. | "I started the prod deploy for 40393, watch it and tell Tami" |
| `merge` | Merges one ticket's PR, a combined PR, or the top PR of a stack. Checks that every smaller PR is inside it, closes those PRs with a comment, deletes their branches and local worktrees, and moves every ticket to Accepted. In watch mode it checks Jira once a minute and merges as soon as QA has moved every ticket to Ready for Merge. | "Merge 9442", "Watch 41048 for ready for merge, then merge it" |
| `catch-up` | Merges master into a branch in a worktree and pushes. Never rebases or force-pushes. Stops on conflicts. | "Catch 40350 up with master" |
| `jira-sync` | Moves each ticket forward to match its PR: approved to Ready for Staging, merged to Accepted. Never moves a ticket backward or out of a column that QA owns. | "Are my tickets in the right columns" |
| `mcp-merge` | observepoint-mcp only. Makes the checks of your approved PRs pass, squash-merges them one at a time, moves each ticket to Accepted, and catches the next PR up with main. | "Merge my reviewed MCP tickets" |

### Keep the lessons current

| Skill | What it does | Say something like |
|---|---|---|
| `refresh-patterns` | Brings a repo's review patterns file up to date with the review comments since its "Built on" date, groups the new entries that `fix` added, and gives each pattern its kind. `ticket-verify` starts it in the background when a file is over 90 days old. | "Refresh the review patterns for moonbeam" |

## What the skills learn

Three kinds of files grow as you work. Commits to them go straight to `main`.

| File | Written by | Read by |
|---|---|---|
| `skills/ticket-verify/references/review-patterns/<repo>.md`: patterns from past review comments. Each has a kind: **breaks**, **theme**, **quality** or **style** | `refresh-patterns`, and `fix` (new review comments) | `ticket-verify` (all kinds, on your code), `pr-review` (breaks and theme; quality within its limit; never style) |
| `skills/ticket-verify/references/qa-misses/<repo>.md`: bugs QA found after `ticket-verify` passed, each with the test that finds it | `fix` (QA bugs) | `ticket-verify` (as test cases), `pr-review` (as checks) |
| `skills/pr-review/references/my-bar.md`: review comments you cut or changed, and authors' pushback | `pr-review` | `pr-review` |

## Requirements

- [`gh`](https://cli.github.com), authenticated (`gh auth login`), and [`jq`](https://jqlang.github.io/jq/).
- The ObservePoint `aikit` CLI, authenticated (`aikit status`). Jira, CircleCI, Slack, worktrees
  and notifications go through it: `aikit jira`, `aikit circleci`, `aikit slack`,
  `aikit repo worktrees`, `aikit notify`.
- The aikit skills `jira-start` (`start`), `code-review` (`ticket-verify`) and `deploy`
  (`deploy-staging`, `deploy-prod`).
- For browser QA in moonbeam (`ticket-verify`, `fix`, `pr-review`): the setup in
  [agent-dev-setup](https://github.com/jackmparker/agent-dev-setup), which gives each agent its own
  dev server (`moonbeam-dev`) and its own window in a headless agent Chrome (`claim_tab()`).
- `thread`, and the thread title in `start`, use T3 Code's tools when they exist, and work
  without them.
- `mcp-merge` needs a local clone of observepoint-mcp at `~/ObservePoint/observepoint-mcp`.

## Install

This repo is its own plugin marketplace. Inside Claude Code:

```
/plugin marketplace add jackmparker/ticket-flow
/plugin install ticket-flow@ticket-flow
```

To update after a change: `claude plugin marketplace update ticket-flow && claude plugin update ticket-flow@ticket-flow`.
New threads load the new version.

## Jira workflow

The skills follow the forward order of the WORK project:

To Do, In Progress, To Be Reviewed, Ready for Staging, On Stage - Ready for Test,
On Stage - In Test, Ready for Prod, On Prod, Ready for Merge, Accepted.

QA sends a ticket back to Waiting for Fix. `fix` and `deploy-staging` move it to On Stage again.

The skills move tickets by transition ID, because two transitions lead to Accepted and
`--to "Accepted"` fails as ambiguous. The IDs apply to the WORK project only:

| ID | Transition |
|---|---|
| 41 | In Progress to To Be Reviewed ("Ready for Review") |
| 51 | To Be Reviewed to Ready for Staging |
| 91 | Ready for Staging to On Stage - Ready for Test ("Deploy to Staging") |
| 371 | Waiting for Fix to On Stage - Ready for Test |
| 131 | Ready for Prod to On Prod ("Deployed") |
| 351 | Ready for Merge to Accepted ("Code Merged, Set as Accepted") |
| 431 | Ready for Merge to Accepted ("Accepted"), used by `mcp-merge` |

In another project, the skills fall back to `aikit jira issues transitions list` and pick the
forward transition by name.

## License

MIT
