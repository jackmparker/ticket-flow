# ticket-flow

Keep Jira tickets in step with their GitHub pull requests.

A [Claude Code](https://claude.com/claude-code) plugin with thirteen skills:

| Skill | What it does | Say something like |
|---|---|---|
| `jira-sync` | Compares each ticket with its PR and moves the ticket forward. An approved PR moves the ticket to Ready for Staging. A merged PR moves it to Accepted. It never moves a ticket backward, and it does not move tickets in the columns that QA owns. | "Move any approved tickets into ready for staging", "See if any of the zoneless tickets need to be moved" |
| `thread` | Makes this thread your Ticketflow Tasks thread: it renames the thread to "Ticketflow Tasks", pins it in T3 Code (and unpins the older one), then sends every later command to a fresh agent (a child thread in T3 Code) so earlier commands never fill its context. It relays drafts and questions to you and your answers back to the right agent, and lists what still runs. | "/ticket-flow:thread", "This is my ticket-flow thread" |
| `merge` | Merges a ticket's PR and finishes its tickets, for one ticket's PR, a combined PR that holds several tickets' PRs, or the top PR of a stack. It checks that every smaller PR is inside the merged PR, closes those PRs with a comment, deletes their branches, and moves every ticket to Accepted. In watch mode (started by `prod-handoff`) it checks Jira once a minute and merges as soon as QA has moved every ticket to Ready for Merge. | "Merge 9442", "Merge the OP Agent stack and clean it up", "Watch for Tami to move 41048 to ready for merge, then merge it" |
| `catch-up` | Merges master into a branch in a git worktree and pushes. It never rebases or force-pushes. It stops on conflicts. | "Catch 40350 up with master" |
| `fix` | Fixes feedback on your tickets: review comments on your open PRs, and bugs QA reported in Jira (tickets in Waiting for Fix). It reproduces a QA bug first, fixes it in the ticket's own branch, runs lint, specs and (for a QA bug) a QA run in the browser, then carries the fix into combined branches and up stacks. It decides by itself what comes next: push only, or redeploy to the staging environment that still runs the ticket and move it back to On Stage. It replies on the GitHub thread or with a short Jira comment for QA, and adds what reviewers and QA caught to the files that `ticket-verify` reads. | "Fix what Tami found in 41060", "Address the review comments", "Cam left comments on 9208, fix them" |
| `pr-review` | Reviews a teammate's PR, or every PR waiting on your review, and posts comments as you after you see the full draft. It comments on what breaks, on documented theme rules, and on at most 2 code quality problems with a real cost, never on style. It uses the repo's review patterns (each now has a kind: breaks, theme, quality or style) and the "missed by QA" list, checks the PR against its Jira ticket and for swapped components, skips what other reviewers already said, and learns from the comments you cut (`references/my-bar.md`). Moved from the `comment-on-pr` plugin. | "Review 9301", "Comment on this PR", "Review my queue" |
| `prod-handoff` | Waits for a production deploy you started. When it succeeds, it moves the ticket (or every ticket of a combined PR) to On Prod, sends the QA person a Slack message to smoke test, and starts `merge` in watch mode. When it fails, it does none of these and reports the failed job. | "I just kicked off the prod deploy, watch it, move the ticket to on prod and message Tami" |
| `deploy-staging` | For moonbeam only. Deploys to US2 (your own FE staging environment), or to another environment you name, such as US8. It merges master into the branch and pushes, deploys at once without waiting for DefaultPR, and when the deploy lands sets each ticket's Environment field and moves every ticket to On Stage - Ready for Test. It watches DefaultPR meanwhile: on a failure it fixes the cause, pushes after the deploy ends and deploys again. For an environment other than US2, it first stops if QA tests someone else's tickets there. | "Deploy 41083 to staging", "Send 9442 to us8" |
| `deploy-prod` | For moonbeam only. First checks that the branch does not pin a component library snapshot: it stops when the library PR or its release is not merged yet, and pins moonbeam to the release when one exists. Then runs three skills in order: `catch-up` merges master into the branch and pushes, the aikit `deploy` skill deploys it to prod and waits, and `prod-handoff` runs while the deploy runs. When the deploy succeeds, the tickets move to On Prod, QA (Tami by default) gets a Slack message to smoke test, and `merge` merges the PR as soon as QA moves the tickets to Ready for Merge. | "Deploy 40393 to prod" |
| `mcp-merge` | For the observepoint-mcp repo only. Finds your approved MCP PRs and makes every required check pass. It fixes failed checks and conflicts itself, with a limit of 3 fix rounds per PR. It squash-merges one PR at a time, moves its ticket to Accepted, waits for the deploy to production, and catches the next PR up with main. | "Merge my reviewed MCP tickets" |
| `start` | Does a ticket end to end with no pauses: creates a git worktree, runs the aikit `jira-start` skill in it, runs `ticket-verify` for the test plan, writes the code, runs `ticket-verify` again, and stops only to ask whether to commit and open the PR. Questions wait until research is done, and come all together. | "Start 40393", "Work on WORK-40393" |
| `ticket-verify` | Run twice per ticket. After `jira-start`, a QA agent writes an adversarial test plan from the ticket and records the "before" state. When the code is written, it runs the gates, has the QA agent try to break the change in the browser (or against the API for backend repos), runs a code review that also checks the repo's past PR comments (`skills/ticket-verify/references/review-patterns/`), fixes the findings, runs a final check, shows you the report and before/after screenshots, and asks before the commit and PR. On your yes, Jira gets one short PDF (result, found and fixed, the full test plan as one table with each case's round history, at most 3 cropped before/after pairs; built by `build-report.py`), a separate text file only for long logs, all inside one comment from you: the summary of what was found and fixed, with the files shown in it. | "Verify this ticket", "Is 40393 ready for a PR" |
| `refresh-patterns` | Brings a repo's review-patterns file up to date: fetches only the human review comments since the file's "Built on" date (`mine-review-comments.py`), merges them into the patterns, groups the "New, not yet grouped" entries that `fix` adds, commits, pushes, and updates the installed plugin. `ticket-verify` starts it in the background when a file is over 90 days old. | "Refresh the review patterns for moonbeam", "refresh-patterns all" |

## Requirements

- [`gh`](https://cli.github.com), authenticated (`gh auth login`)
- [`jq`](https://jqlang.github.io/jq/)
- The ObservePoint `aikit` CLI, authenticated for Jira (`aikit status`). All Jira reads and
  moves go through `aikit jira`.
- `catch-up` also uses `aikit git backmerge`.
- `prod-handoff` also uses `aikit circleci` and `aikit slack`.
- `deploy-prod` also uses the aikit `deploy` skill.
- `start` also uses the aikit `jira-start` skill and `aikit repo worktrees`.
- `ticket-verify` also uses the aikit `code-review` skill, `aikit jira attachments`, and for moonbeam the browser setup in [agent-dev-setup](https://github.com/jackmparker/agent-dev-setup) (`moonbeam-dev`, `claim_tab()`).
- `mcp-merge` also uses `aikit circleci` and `aikit git backmerge`, and a local clone of
  observepoint-mcp at `~/ObservePoint/observepoint-mcp`.

## Install

This repo is its own plugin marketplace. Inside Claude Code:

```
/plugin marketplace add jackmparker/ticket-flow
/plugin install ticket-flow@ticket-flow
```

Then ask in plain words, or run a skill directly, for example `/ticket-flow:jira-sync zoneless`.

## Jira workflow

The skills follow the forward order of the WORK project:

To Do, In Progress, To Be Reviewed, Ready for Staging, On Stage - Ready for Test,
On Stage - In Test, Ready for Prod, On Prod, Ready for Merge, Accepted.

The skills move tickets by transition ID, because two transitions lead to Accepted and
`--to "Accepted"` fails as ambiguous. The IDs (41, 51, 91, 131, 351) apply to the WORK project
only. In another project, the skills fall back to `aikit jira issues transitions list` and pick
the forward transition by name.

## License

MIT
