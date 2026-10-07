# ticket-flow

Keep Jira tickets in step with their GitHub pull requests.

A [Claude Code](https://claude.com/claude-code) plugin with three skills:

| Skill | What it does | Say something like |
|---|---|---|
| `jira-sync` | Compares each ticket with its PR and moves the ticket forward. An approved PR moves the ticket to Ready for Staging. A merged PR moves it to Accepted. It never moves a ticket backward, and it does not move tickets in the columns that QA owns. | "Move any approved tickets into ready for staging", "See if any of the zoneless tickets need to be moved" |
| `stack-cleanup` | After you merge the top PR of a stack, it checks that the merged PR holds every lower PR. Then it closes the lower PRs with a comment, deletes their branches, and moves every ticket to Accepted. | "I just merged the top ticket in the stack for OP Agent" |
| `catch-up` | Merges master into a branch in a git worktree and pushes. It never rebases or force-pushes. It stops on conflicts. | "Catch 40350 up with master" |

## Requirements

- [`gh`](https://cli.github.com), authenticated (`gh auth login`)
- [`jq`](https://jqlang.github.io/jq/)
- The ObservePoint `aikit` CLI, authenticated for Jira (`aikit status`). All Jira reads and
  moves go through `aikit jira`.
- `catch-up` also uses `aikit git backmerge`.

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
