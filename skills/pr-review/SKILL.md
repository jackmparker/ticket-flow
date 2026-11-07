---
name: pr-review
description: Use to review a teammate's GitHub PR and post review comments as the user - when given a PR link and asked to review it, comment on it, leave or post comments, or approve it ("comment on this PR", "review 9301"). With no arguments or no PR link, or when asked to review everything waiting on the user ("needs my review", "review my queue"), it reviews the whole queue. It comments on what breaks, documented theme rules and a few real code quality costs, never on style. It uses what the repo's reviewers and QA caught before (ticket-verify's review patterns and QA misses lists), checks the PR against its Jira ticket, skips what other reviewers already said, learns from the comments the user cuts, and shows the full draft before anything is posted.
---

# Review a teammate's PR

## Overview

Review a GitHub PR and post review comments on specific lines under the user's identity. The output is a
short set of high-value comments, shown to the user before anything is posted.

These comments land on a teammate's work, signed as the user. Volume and confidence both cost
the user credibility. Fewer, verified, friendly comments beat thorough ones.

A PR link means review that one PR. No arguments, or no PR link, means *Batch mode* (at the
end): review every PR waiting on the user. Do not ask for a link. Every rule below still
applies to each PR in the batch.

## Gather

```bash
gh pr view <url> --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles
gh pr diff <url>
gh pr view <url> --json headRefOid --jq '.headRefOid'   # commit_id for the review
```

Read surrounding code, not just the diff, a local checkout (`git fetch origin <headRefName>`,
then `git show origin/<headRefName>:<path>`) or `gh api repos/<owner>/<repo>/contents/<path>?ref=<branch>`.
Read the spec file when there is one, it's for checking your claims, not for auditing coverage.

**What others already said.** Read the review threads and comments already on the PR, from people
and from bots such as CodeRabbit (an automated reviewer):

```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments --jq '.[] | "\(.user.login) \(.path):\(.line) \(.body[0:200])"'
gh pr view <url> --json reviews,comments
```

Do not post a finding that someone already raised on the same code, even in other words. When the
user reviewed this PR before, read the author's replies to the user's earlier comments: a comment
the author did not fix and did not answer goes in chat, not in a new comment.

**The Jira ticket.** Take the key from the PR title or branch (`WORK-41083`) and read the ticket:
`aikit jira issues get <KEY> --fields summary,description`. Compare the diff with the ticket and
the PR description. A change that neither explains is a question for the author when it can
break something (a swapped component, a changed default, a removed check). See *Component swaps*.

**What the repo has caught before.** Read these files in the ticket-flow plugin, next to this
skill (`<this skill folder>/../ticket-verify/references/`):

1. `review-patterns/<repo>.md`: patterns from past review comments in this repo. Each has a
   `Kind:` line. Use **breaks** and **theme** patterns as checks. Use **quality** patterns only
   under *The quality tier*. Ignore **style** patterns: they are for the user's own code.
2. `qa-misses/<repo>.md`, when it exists: bugs QA found after the code passed review. Check
   whether this diff can cause the same kind of bug. A hit is a **breaks** finding. Run the
   grouping check at the top of the file each time you read it.

And `<this skill folder>/references/my-bar.md`: comments the user cut or changed in past reviews.
Do not draft a comment like one the user cut.

**Read the repo's styling rules when the PR touches anything visual** (stylesheets, templates,
theme files, design-system components). See *The styling hard line* below for which docs.

## What earns a comment

One test: **would this break something for a real user, or lose real data?** A wrong value, a
silent failure, a security hole, a crash on input a caller actually produces. If you can't name
the concrete thing that goes wrong, it doesn't clear the bar.

Below the bar, leave these out entirely:

- Naming, formatting, import order, comment wording, type-annotation style.
- "Consider extracting", "could be simplified", duplication, structure and architecture
  preferences, a different way to write working code is not a finding.
- Missing tests, unless the untested thing is the defect itself.
- Hypothetical inputs no caller produces; edge cases the code already handles downstream.
- Defensive guards against things that can't happen.
- Anything you'd phrase as "might be worth" or "just a thought".

Most PRs produce zero comments, and zero is a complete review. One or two is a busy PR. If you
have four, the bar slipped, re-check each one against the test above and cut what fails. Never
pad toward a number to look thorough.

## The quality tier

Code quality still matters, so a few quality comments clear the bar. A quality finding needs all
of these:

- **A cost you can name.** Not "cleaner": what goes wrong later. A second copy of a helper that
  exists at `<path>` and will drift from it. Dead code the PR leaves behind that the next reader
  will think is used. Logic in a template or controller that the repo keeps in a service. A cast
  that hides a wrong type. A comment or doc the PR made false.
- **A small, exact fix.** Name the helper, the file or the type. Not "consider refactoring".
- **The repo cares about it.** It matches a `Kind: quality` pattern in the repo's patterns file,
  or the repo's own docs (`CLAUDE.md`, `AGENTS.md`, `docs/`) state it.

At most **2 quality comments per PR**: pick the ones with the highest cost. Start each with
"Not blocking:". They never hold approval, and they do not count toward the "four means the bar
slipped" check.

Still below the bar: naming, formatting, import order, comment wording, idiom preferences, a
different way to write working code, and anything that only a `Kind: style` pattern covers.

## The styling hard line

One exception to the test above. Some repos document a theme or design system: tokens or roles
that every color, radius and shadow must read, a rule that no style keys on light or dark mode,
a rule that UI belongs in a shared component library. **A change that breaks one of those
documented rules always earns a comment**, even when the page looks fine today. The rule exists
because the drift is invisible until someone audits it, and a review is that audit.

**Find the rules.** Read them fresh on every review, at the PR's base branch, because they change:

1. Check `references/` next to this skill for a file that covers the repo. If one does, read
   every doc it lists, in full, and use its checklist. For ObservePoint (`observepoint/moonbeam`,
   `observepoint/op-component-library`) that is `references/observepoint-theming.md`.
2. Otherwise read the styling docs the repo points to itself: `CLAUDE.md`, `AGENTS.md`,
   `CONTRIBUTING.md`, and any `docs/` file about theming, tokens, design system or styling.
3. No documented rules means no hard line. Fall back to the normal bar.

**What it covers.** Only lines the PR adds or changes, and only rules a doc states. Old
violations the PR does not touch are not this PR's problem. Check the docs' own list of
deliberate exceptions before commenting (pages kept off the theme on purpose, fixed hues).

**How to write it.** Same format as any comment: what is wrong, then the fix, under 50 words.
Name the token or component to use and the doc that states the rule. When one file repeats the
same violation, write one comment on the first line and list the other lines in it.

> `#333` is a raw color, so this text stays dark gray in dark mode. Use
> `var(--op-text-primary)`? (Theming section of `docs/code-conventions.md`)

**What it does not change.** Styling comments do not count toward the "four means the bar
slipped" check. Code style (naming, formatting, import order) is still below the bar; this
covers theme and design-system rules only. Styling findings alone are approve-with-comments,
not a reason to hold approval.

## Component swaps

In every PR that changes templates, list each place where one component replaces another (for
example `op-button` for `button`, `mat-select` for `op-select`, a library component for an app
one). A swap changes behavior, styles and accessibility on every screen that uses it. Check each
swap: same inputs and outputs, same events, same look in light and dark theme. A swap that the
ticket and the PR description do not mention always earns a comment that asks about it.

**PRs by David Delphenich (GitHub `daviddelphenich-OP`)**: review extra thoroughly. Look hard for
swapped components and for changes the description does not mention, and tell the user in chat
about every swap you find, even when it looks right. For his PRs the quality tier has no limit,
and style findings may go in too (mark them "Nit:"). A missed swap in one of his PRs once caused
more than 200 bugs.

## The verdict

Two independent decisions: what to say, and whether to approve. Having findings does not
withhold approval, around here the normal outcome is review, comment, **and** approve, in good
faith that the author addresses the comments before merging.

**Every draft you show the user carries an approval recommendation.** One of:

- **Nothing cleared the bar**, propose `APPROVE` alone with a one-line body (see *The approval
  body* below). Good enough is a real verdict and the most common one on healthy work; a clean
  PR gets approved, not searched until something turns up. Below-bar observations stay off the
  PR entirely, mention them in chat if they're worth anything.
- **Findings cleared the bar**, propose the comment review *and* recommend approving alongside
  it. This is the default. Ask the user; don't decide for them.
- **A finding would ship a real defect**, recommend holding approval and name the finding that
  is the reason. `REQUEST_CHANGES` blocks a colleague's PR and is the user's call alone; never
  put it in a payload unasked.

Never leave approval unmentioned. Silence reads as "not approvable" and strands the author on a
ticket they can't move. If you're not recommending approval, say which finding is the reason.

## The approval body

A review has exactly two kinds of text: the line comments, and one short approval line. There
is no summary paragraph. The line comments carry the substance; the approval body is a
thumbs-up, not a recap.

Short and casual. One line, usually under 12 words.

- **Clean PR**, "LGTM", "Looks good 👍", "Nice, LGTM", "All looks good to me", "LGTM, thanks!"
- **Approving alongside comments**, acknowledge them in passing and approve anyway: "Just a
  couple of small things but otherwise looks good!", "Left a few notes, nothing blocking, LGTM",
  "A couple of suggestions, but happy with this", "Small comments, otherwise LGTM".

Vary it. The user leaves these across many PRs and the same string every time reads like a bot.
Pick a different phrasing than the last approval; the lists above are examples of the register,
not a rotation to cycle through.

No em dashes anywhere in posted text (body or comments). Use a comma, colon, or period instead.

Do not say "inline" in the body (or in the comments). The reader is looking at the comments; say
"left a few notes" or "a couple of comments", not "inline".

Never in an approval body: a recap of what the PR does, a restatement of the findings, a
list of what you checked, praise paragraphs, or "these are just suggestions" caveats. If it
needs more than a line, it belongs in a line comment.

When the user holds approval, the `COMMENT` review still needs a body (the API requires one for
`COMMENT` and `REQUEST_CHANGES`). Same register, one line, "Left a few notes", "Couple of
things worth a look before this goes in". Still not a summary.

## What each comment is

**Two or three sentences. Under 50 words.** What breaks, then the fix. That's the whole comment.

> This throws when `items` is empty, the dashboard 500s on a new account. Guard before the
> `reduce`?

> `retryCount` never resets after a success, so the fourth failure in a session gives up
> immediately. Reset it in the success branch?

Plain language, no jargon, no build-up. Don't restate what the code does, don't explain your
reasoning, don't list what else you checked, don't hedge with "I might be missing something".
Ending the fix as a question ("Guard before the reduce?") keeps it collegial without padding.

No code blocks unless the fix genuinely can't be said in a sentence. No preamble, no sign-off.

No summary body. Whatever you would have put there either clears the bar and belongs on a line
of code, or doesn't and belongs nowhere.

## Confidence

Every behavioral claim is verified or marked as unverified.

- Verify pure functions by running them (`node -e`, the existing spec file).
- Verify surrounding behavior by reading the actual file at the head commit.
- **Never write numbered repro steps you have not executed.** Reasoning from source is fine:
  say so in the comment: "I haven't run this, but `handleBlur` at :31 suggests…".

A confident repro that turns out wrong, posted publicly under the user's name, costs more than
the finding was worth.

## The post gate

**Show the complete draft in chat. Wait for an explicit yes. Then post.**

"Review it and comment for me" authorizes posting. It does not authorize posting text the user
has not read.

No exceptions:
- Not when the user said "and comment on it" or "leave comments", that is the authorization to
  post, not permission to skip the draft.
- Not when the findings are obviously correct.
- Not when showing the draft feels like stalling or wasting a turn.
- Not by posting and showing the draft in the same message.

| Rationalization | Reality |
|---|---|
| "They already told me to post, asking is stalling" | They authorized the action, not the wording. One turn is cheap; a bad comment on a colleague's PR is not. |
| "It's reversible, I can delete the comments" | Deleting review comments leaves the email notifications. Not reversible. |
| "I'll post and mention they can edit after" | The author has already read it by then. |
| "The draft is in my summary, that counts" | Shown after posting is not shown before posting. |

### Red flags, stop, show the draft

- About to call `gh api ... --method POST`, `gh pr review`, or `gh pr comment` in the same
  message that first states the findings
- Thinking "they clearly want this posted"
- A comment in the payload you could not defend against the bar
- A draft with findings that says nothing either way about approving
- Any numbered repro step you did not execute

## Learn the user's bar

After the post gate, compare what was posted with your draft. For each comment the user cut, or
changed in meaning, add one line to `<this skill folder>/references/my-bar.md` (create it with a
`# Comments the user cut or changed` heading). Use the ticket-flow clone at
`~/ObservePoint/ticket-flow`, `git pull --ff-only` first:

```
- <YYYY-MM-DD> <repo>#<n> cut: <the finding, one sentence>. Kind: <breaks|theme|quality|style>. <the user's reason, if they gave one>
- <YYYY-MM-DD> <repo>#<n> changed: <the finding>. Draft said <x>, user made it <y>.
```

Also add a line when an author pushed back on one of the user's earlier comments (see *What others
already said*) and the user did not insist: `pushback: <finding>. Author: <reason>.`

Commit on `main` with `pr-review: the user's bar, from <repo>#<n>` and push. Do not update the
installed plugin for this. Skip the step when the user posted the draft as it was.

## Posting

Write the payload to a file, then POST it.

`line` is the line number **in the file at the head commit**, not a diff position. Every line
must fall inside a diff hunk or the API rejects it.

Re-read `headRefOid` immediately before posting. Some branches get force-pushed between review
and post (release-bot branches especially), and a stale `commit_id` describes code that is no
longer what merging would ship.

**Approve with no comments**, one call, `event: "APPROVE"`, a `body` with the approval line,
and no `comments` key at all.

**Approve with comments**, one review, not two. Create it pending (omit `event`), then submit
it as the approval so the line comments and the approval line ship together in a single
notification:

```jsonc
// payload.json, no "event" key: this creates a PENDING review
{
  "commit_id": "<headRefOid>",
  "comments": [
    { "path": "src/foo.ts", "line": 73, "side": "RIGHT", "body": "<comment>" }
  ]
}
```

```bash
REVIEW_ID=$(gh api repos/<owner>/<repo>/pulls/<n>/reviews --method POST \
  --input payload.json --jq '.id')
gh api repos/<owner>/<repo>/pulls/<n>/reviews/$REVIEW_ID/events --method POST \
  -f event=APPROVE -f body='<approval line>' --jq '{id, state, html_url}'
```

**Comments without approval** (the user held approval), same pending review, submitted with
`event=COMMENT` and the one-line body from *The approval body*.

Verify after posting:

```bash
gh api repos/<owner>/<repo>/pulls/<n>/comments --jq '.[] | "\(.path):\(.line)"'
```

A pending review that never gets submitted is invisible to the author, if the submit call
fails, say so rather than reporting the review as posted.

Report the review URL and the state back to the user.

## Batch mode

For a run with no arguments or no PR link. Same bar, same gate, many PRs.

**Find the queue:**

```bash
gh search prs --review-requested=@me --state=open --limit 50 \
  --json url,number,title,repository,author,isDraft
```

This matches the GitHub "Needs your review" filter, team requests included. Skip drafts. Then
size each PR so you know which diffs are large:

```bash
gh pr view <url> --json additions,deletions,changedFiles,headRefName,headRefOid
```

Tell the user the list (number, title, author, file count) in one short table, then start. A
read-only review needs no go-ahead.

**Review in parallel.** One subagent per PR, all launched in one message, in the background.
Each prompt carries the full bar from *What earns a comment*, the comment format from *What
each comment is*, and the *Confidence* rules. When the PR touches anything visual, the prompt
also carries *The styling hard line* in full, with the absolute path of the matching
`references/` file so the subagent reads every doc it lists. Every prompt also carries *The
quality tier*, *Component swaps*, and the absolute paths of the repo's patterns file, its QA misses
list and `my-bar.md`, with the rule for each kind. Tell each subagent:

- Do not post, approve, or comment on GitHub. Read-only.
- Do not check out branches or touch the user's working tree. Read code with `git show
  origin/<headRefName>:<path>` after a fetch, or with `gh api .../contents`.
- `gh pr diff` fails above 300 changed files. For those, build the diff locally from the merge
  base (`git diff $(git merge-base origin/<base> origin/<head>) origin/<head>`).
- Return: findings (path, head-commit line inside a hunk, comment body), an approval
  recommendation, the `headRefOid` it reviewed, and one line on what it checked.

Give each subagent the risks specific to its PR (for example, a lint-fix PR: what mechanical
change could alter runtime behavior). Generic prompts get generic reviews.

**Report as results arrive.** Show each PR's draft when its subagent returns, with a running
"N of M ready" line. Subagent reports are drafts for you to check, not text to post as is.
Apply the bar again; cut anything that fails it.

**Final draft.** When all are back, show one table: PR, title, line comments (verbatim), and
the approval body. Vary the approval body across PRs; eight identical "LGTM"s read as a bot.
List any caveat under the table (a PR the author plans to rebuild, two PRs that will conflict).

**Post gate.** One explicit yes can cover the whole table ("post all 8"), or the user names
PRs to skip or change. Post only the set the user approved.

**Before posting**, re-read every `headRefOid` and compare it with the commit each subagent
reviewed. If one changed, do not post that PR. Say so, and offer to review it again. Post the
rest as normal (see *Posting*), then report one table with each review URL and state.

## Common mistakes

| Mistake | Fix |
|---|---|
| Comments that don't clear the bar, added for coverage | Cut them. A zero-comment review is fine. |
| A "consider extracting / could be cleaner" comment | Not a finding. Cut it. |
| Four or more comments on one PR | The bar slipped. Re-test each against "what breaks?" (styling and quality comments do not count) |
| Skipping a raw color, a mode-keyed selector or a one-off control because "it looks fine" | Documented theme rules are a hard line. Comment, name the token or component and the doc. |
| Reviewing styling from memory | Read the repo's theme docs at the base branch on every review; they change |
| Flagging a styling violation the PR did not add | Only added or changed lines. Check the docs' list of deliberate exceptions first. |
| Withholding approval on a PR with nothing wrong | Propose `APPROVE`. Good enough is a verdict. |
| Showing a comment draft with no approval recommendation | Every draft says approve or names why not |
| Demoting a real finding to the summary to keep the list short | Comment on everything that clears the bar |
| Comments longer than a few sentences | What breaks, then the fix. Under 50 words. Cut the rest. |
| A paragraph in the approval body | One casual line, "LGTM", "Small comments, otherwise looks good!" |
| Writing a summary body for the review | There isn't one. Line comments + one approval line, nothing else. |
| The same approval wording as last time | Vary the phrasing; identical strings read as automated |
| Using diff position for `line` | File line at the head commit, `side: "RIGHT"` |
| Reviewing the diff alone | Read the file and its spec at the head commit |
| Asserting an unexecuted repro | Run it, or mark it as reasoned from source |
| Batch: posting a PR whose head moved after review | Re-check `headRefOid` for every PR right before posting |
| Batch: a subagent posts on its own | Every subagent prompt says read-only; only you post, after the yes |
| A comment from a `Kind: style` pattern, or a "cleaner" quality comment with no named cost | Cut it. Style is for the user's own code, not a teammate's PR |
| A third quality comment | Keep the 2 with the highest cost |
| Repeating what CodeRabbit or another reviewer already said | Read the existing threads first; skip it |
| Drafting a comment like one in `my-bar.md` | The user cut that kind before. Leave it out |
