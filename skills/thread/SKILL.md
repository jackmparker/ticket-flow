---
name: thread
description: Use when the user makes this thread their Ticketflow Tasks thread - a long-lived thread (in T3 Code, often with no project) where they give one command after another (review a PR, sync Jira, fix a ticket, deploy) and want each command run by a fresh agent, so earlier commands never pollute its context. Examples - "/ticket-flow:thread", "this is my ticket-flow thread", "use this thread for ticket-flow tasks", "run every command in a fresh subagent". It renames the thread to "Ticketflow Tasks" and pins it in T3 Code. After it is invoked, it applies to every later message in the thread.
---

# Ticketflow Tasks thread

## What this thread is

From now on this is the Ticketflow Tasks thread. The user gives a command, an agent with fresh
context does it, this thread reports the result and waits for the next command. The thread lives
long, so it keeps its own context small: it sends work out and keeps only short results.

**Set up the thread** (T3 Code only; load the tools with ToolSearch, and go on if one is missing
or fails):

1. Rename this thread: `mcp__t3-code__t3_thread_update` with `action: "rename"` and
   `title: "Ticketflow Tasks"`. Omit `threadId`.
2. Pin it: `mcp__t3-code__t3_thread_organize` with `action: "pin"`. Omit `threadId`.
3. Unpin the older Ticketflow Tasks threads, so only the current one stays pinned: find threads titled
   "Ticketflow Tasks" with `mcp__t3-code__t3_thread_list` (`allProjects: true`,
   `titleContains: "Ticketflow"`, and compare titles without regard to case), and for each one
   that is not this thread, call
   `t3_thread_organize` with `action: "unpin"` and its `threadId`. Do not archive or settle them:
   a task in one may still run.

Tell the user in one line that the Ticketflow Tasks thread is ready, then wait for the first command.

## Every command goes to a fresh agent

For each command that needs a tool (reading GitHub, Jira, CircleCI or code, editing, deploying),
start a new agent. Do not do the work in this thread, even when it looks small: the point is that each
command starts clean.

**In T3 Code** (the `mcp__t3-code__delegate_task` tool exists; load it with ToolSearch): call
`delegate_task` with `mode: "async"`, a short `title` (for example "Review #9301" or "Fix 41060"),
and the brief below. Each child is its own thread in T3, so the user can open it and watch.
Call `orchestrator_capabilities` once per Ticketflow Tasks thread, before the first `delegate_task`.

**Elsewhere**: use the Agent tool (`general-purpose`), in the background for long work (deploys,
watches, a review queue), in the foreground for short work.

Several commands in one message, or a new command while others run: start one agent per command,
in parallel. Never wait for one to finish before starting the next, unless the second needs the
first's result (then say so and start it when the first ends).

## The brief

The agent knows only what the brief says. Write it like this:

```
The user's command, word for word: "<command>"

Do it as the user's rules in ~/.claude/CLAUDE.md say. If a ticket-flow skill fits, invoke it
with the Skill tool (for example ticket-flow:pr-review, ticket-flow:jira-sync, ticket-flow:fix,
ticket-flow:deploy-staging, ticket-flow:deploy-prod, ticket-flow:merge). Work in the repo's own
worktrees under ~/ObservePoint/<repo>, never in this thread's folder.

<only the facts from earlier results that this command needs, for example "#9301 is the PR the
user reviewed an hour ago; its draft was posted">

When a step needs the user's decision (a draft to post, a commit, a PR, a question), stop there
and return the draft or the question. Do not act on it.

End with a short report for the user: the result first, then links. No logs.
```

Add earlier facts only when the command depends on them ("post it", "do the same for 41064").
Never paste a whole earlier report.

## Questions, drafts and follow-ups

A child that stops for the user's decision (for example the `pr-review` draft, or a commit question)
returns the draft or question. Show it to the user as the child wrote it, and name the task it
belongs to.

The user's answer belongs to that child, which still has the context. In T3 Code, send the answer
to the child's thread with `t3_thread_send`, word for word. Elsewhere, use SendMessage to the same
agent. Do not start a new agent for an answer to a running task's question.

A new command about finished work (for example "fix the comment Cam left on 9301" after the review
ended) is a new command: new agent, new brief, with the facts it needs.

## What this thread does itself

Only this, without tools or with one quick read:

- Report results and relay questions.
- Answer "what is running?" from the task list below (`task_status` only when the user asks).
- Answer a question about the conversation itself ("which PR did we review first?").
- Cancel a task the user stops (`task_cancel` in T3 Code).

Anything else is a command.

## Keep the user oriented

After each report, list the tasks that still run, one line each:

```
Running: Review queue (3 of 5 drafts ready) · Deploy 9442 to prod (waiting for Tami)
```

Keep reports short: the child's result, its links, and the one decision the user must make, if
any. When the thread grows long, the user starts a new one; the new thread thread knows nothing of
this one, so name any task that still runs when the user says they are moving.
