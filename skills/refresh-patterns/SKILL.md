---
name: refresh-patterns
description: Use to bring a repo's review-patterns file up to date with the review comments left since it was built. Examples - "refresh the review patterns for moonbeam", "update the patterns files", "refresh-patterns authentication". ticket-verify starts it in the background when a file is older than 90 days. It fetches only the comments since the file's "Built on" date, merges them into the existing patterns (counts, links, new patterns), groups the "New, not yet grouped" entries, commits and pushes ticket-flow, and updates the installed plugin. Takes one or more repo names, or "all".
---

# Refresh the review-patterns files

The files are `skills/ticket-verify/references/review-patterns/<repo>.md`, one per repo. Each
starts with a "Built on <date>" line. A refresh adds what reviewers said since that date. It never
rebuilds a file from nothing unless the user asks.

Run this from start to end without stopping. It changes only files in the ticket-flow repo.

## 1. Clone

Edit a git clone, never the installed plugin copy under `~/.claude/plugins/`:

```bash
[ -d ~/ObservePoint/ticket-flow/.git ] || git clone https://github.com/jackmparker/ticket-flow.git ~/ObservePoint/ticket-flow
cd ~/ObservePoint/ticket-flow && git pull --ff-only
```

If the pull fails because of local changes, stop and tell the user. Do not stash or reset.

## 2. Pick the repos

- Named repos: those files. A repo with no file yet: build a new one (step 4, from one year ago).
- `all`: every file in the folder.
- From `ticket-verify`: the one repo it names.

## 3. Fetch

For each repo, take `<since>` from the file's "Built on" date, then:

```bash
python3 skills/refresh-patterns/mine-review-comments.py <repo> --since <since> \
  --out <scratchpad>/review-mining
```

The script keeps human comments on closed or merged PRs, created on or after `<since>`, and drops
bots, authors on their own PR, and approval-only text. If it keeps no comments, only update the
"Built on" date (step 5).

## 4. Merge into the file

Use one subagent per repo when there are several. Each reads the repo's file, the fetched JSON, and
the repo's guidance (README, CONTRIBUTING, AGENTS.md or CLAUDE.md, lint config) on the default
branch, then:

1. Puts each new comment under the pattern it fits. Raise that pattern's "Seen" count, add the
   reviewer to "Raised by", and keep at most 2 example links (prefer the newest).
2. Makes a new pattern from comments that fit none, when at least 3 comments, ideally from more
   than one PR, say the same thing. Others go to `## New, not yet grouped`.
3. Groups the entries already in `## New, not yet grouped` the same way, and removes the ones it
   used. An entry older than a year that never grew into a pattern is deleted.
4. Moves a pattern to `## Lint already catches` when lint now enforces it, and deletes one that the
   repo's guidance or tooling made out of date. Note a reviewer who now asks for the opposite.
5. Keeps the order by frequency and the file's format: numbered instruction headings with the
   lines Check:, Seen:, Raised by:, In docs:. Keep it under about 250 lines.
6. Updates the intro: "Built on <today>", and the totals.

Writing style for the files: short sentences, simple words, active voice, no em dashes.

## 5. Commit and update the plugin

```bash
cd ~/ObservePoint/ticket-flow
git add skills/ticket-verify/references/review-patterns/
git commit -m "Refresh review patterns: <repos>"
```

Raise the patch number of `version` in `.claude-plugin/plugin.json` in the same commit, so the
installed plugin sees an update. Then:

```bash
git push
claude plugin marketplace update ticket-flow && claude plugin update ticket-flow@ticket-flow
```

The updated files apply to new sessions. Report per repo: comments added, patterns changed or
added, and anything that limited the refresh.
