---
name: dev-workflow
description: Use for any step of the ObservePoint ticket workflow in moonbeam or op-component-library - starting a ticket, getting code onto a staging environment (us1-us8, ua1-ua6, app), getting work ready for a pull request, merging master into a branch, or moving a component library change into moonbeam. Examples - "get my code on us7", "deploy this to staging", "is this ready for a PR", "make a PR", "merge from master", "catch up with master", "start WORK-40500", "use my library change in moonbeam", "bump the component library". Read this skill BEFORE you do any of these steps, and follow it exactly. Do not invent steps.
---

# ObservePoint dev workflow

## Why this skill exists

The user is a designer who writes code. They need the same steps every time.
Follow the steps in this file exactly. Do not add steps. Do not skip steps.
If a step fails, stop and report the exact error. Do not improvise a different route.

Speak in plain words. Before each command, say in one short sentence what it does.

## Rules that always apply

1. Never push to `master` or `main`. Work only on a feature branch.
2. Never rebase. Never force-push. Other people review these branches.
3. Never run `git add .` or `git add -A`. Add files by name.
4. Commit only after the user approves the list of files. This applies in every workflow.
5. When there is a merge conflict, stop. Show the files. Ask the user before you change anything.
6. Report what happened, not what should have happened. If a check failed, say so.

## Which workflow?

| The user says | Go to |
|---|---|
| "start WORK-123", "work on this ticket" | [A. Start a ticket](#a-start-a-ticket) |
| "get it on us7", "deploy", "put it on staging" | [B. Deploy to a staging environment](#b-deploy-to-a-staging-environment) |
| "ready for a PR", "make a PR", "open a PR" | [C. Get it ready for a PR](#c-get-it-ready-for-a-pr) |
| "merge from master", "catch up", "update my branch" | [D. Merge master into the branch](#d-merge-master-into-the-branch) |
| "use my library change in moonbeam", "bump the library" | [E. Component library change into moonbeam](#e-component-library-change-into-moonbeam) |

Do the [setup check](#0-setup-check) once per session, before the first workflow.

## 0. Setup check

Run these. Fix each problem before you continue.

| Check | Command | If it fails |
|---|---|---|
| aikit is ready | `aikit status` | Run `aikit onboarding`. Stop until Jira and CircleCI show as ready. |
| GitHub CLI is logged in | `gh auth status` | Tell the user to run `! gh auth login`. |
| ticket-flow is installed | the skill `ticket-flow:catch-up` is in your skill list | Tell the user to run `/plugin marketplace add jackmparker/ticket-flow`, then `/plugin install ticket-flow@ticket-flow`. |
| Node version (moonbeam) | `node -v` shows 22.22.3 or higher | Tell the user to install Node 22 (for example `nvm install 22 && nvm use 22`). |
| Library package auth | `echo ${NODE_AUTH_TOKEN:+set}` prints `set` | Tell the user to follow the Authentication page in the component library Storybook docs. |

Find out which repo you are in: `git remote get-url origin`.

- `moonbeam`: the default branch is `master`.
- `op-component-library`: the default branch is `main`.

## A. Start a ticket

1. Run `/jira-start WORK-<number>`. It reads the ticket and makes the branch.
   In its checkpoint, check that the base is `master` (moonbeam) or `main` (library). If not, run it again with `--base master` or `--base main`.
2. Check the branch name. It must be lowercase kebab-case, based on the default branch:
   - `feature/work-12345-short-description` for a change
   - `bug/work-12345-short-description` for a fix
3. Read the repo's `CLAUDE.md` before you change code. In moonbeam, also read `docs/design-system-workflow.md`.
4. Visual change? Decide where it belongs first:
   - It does not know about audits, consent categories or data sources (a button, modal, tabs, a field): change it in `op-component-library`. Then do workflow E.
   - It knows about ObservePoint data: change it in moonbeam.
   - Not sure: ask the user.

Commit messages always start with the ticket key: `WORK-12345: Short description`.

## B. Deploy to a staging environment

Use this when the user wants to see the branch on `us1`-`us8`, `ua1`-`ua6` or `app`.
Only moonbeam deploys. The component library does not.

1. Did the branch change the component library? If yes, do workflow E first.
   A moonbeam deploy without the library version bump does not fail. It ships the wrong UI with no error.
2. Check that `package.json` does not point at yalc: `npm run lint:pkg`. If it fails, do E step 8.
3. Check for uncommitted work: `git status --short`. If there is any, ask the user to commit it or leave it out. Only pushed code deploys.
4. Push the branch: `git push -u origin <branch>`.
5. Run `/deploy <env> --wait`. Example: `/deploy us7 --wait`.
   This deploys through CircleCI and waits for the result. It does not change Jira.
   Add `--jira` only when the user asks to move the ticket. `--jira` sets the Environment field
   and moves the ticket to "On Stage - Ready for test".
6. Report the result and the test link: `https://<env>.observepointstaging.com` (for example `https://us7.observepointstaging.com`).

If `/deploy` fails, report the CircleCI link and the error. Do not retry with another method.

## C. Get it ready for a PR

Open a PR only when the work is done and ready for review. If the work is not done, tell the user and stop.

1. Run every gate. Fix each failure, then run that gate again.

   **moonbeam:**
   ```bash
   npm run lint:js
   npm run lint:styles
   npm run lint:theme
   npm run lint:pkg
   npm run typecheck:strict
   npm run test:unit:aiagent
   ```

   **op-component-library:**
   ```bash
   npm run build:theme
   npm run theme:prune:check
   npm run roles:snippet:check
   npm run contrast:check
   npm run lint
   npm run lint:styles
   npm run test:run
   ```
   A library change also needs a story in Storybook and a changeset (`npx changeset`).

2. Show the user the list of changed files (`git status --short`). Ask which ones to commit.
3. Commit the files the user approves: `WORK-12345: Short description`.
4. Run `/pr-create`. Do not pass `--jira`. It merges master in and pushes for you. If it reports a conflict, stop and ask the user. The PR title is `WORK-12345: Short description`.
5. `/pr-create` makes a draft. Mark it ready: `gh pr ready <number>`.
6. Add Jack as reviewer: `gh pr edit <number> --add-reviewer jackmparker`.
7. Give the user the PR link.

Do not move the Jira ticket in this workflow unless the user asks.

## D. Merge master into the branch

1. The branch must be committed and pushed. Check with `git status -sb`.
   If there are uncommitted files, do workflow C steps 2 and 3, then `git push`.
2. Run `/ticket-flow:catch-up <ticket or branch>`.
   It merges the default branch in a separate worktree and pushes. It never rebases and never force-pushes.
3. If it reports a conflict, stop. Show the files to the user. Ask before you resolve anything.
4. After the merge, run the gates from workflow C step 1 if the user wants to deploy or open a PR.

## E. Component library change into moonbeam

The library change comes first. Moonbeam uses it second. Do the steps in this order.

1. In `op-component-library`, branch from `main` (workflow A).
2. Change the component and the theme (`_theming.scss`, `_dimensions.scss`). Use only `var(--op-*)` tokens. No raw hex, no raw px.
3. Add or update the Storybook story.
4. Tell the user to update Figma (the component, variant or variable). You cannot do this step.
5. To see the change in moonbeam on this computer: in the library, run `npm run yalc:push`.
   SCSS and TypeScript changes need the moonbeam dev server restarted. Ask the user to restart it.
6. Add a changeset (`npx changeset`). Show the user the changed files and commit the ones they approve. Push the library branch.
   GitHub Actions publishes a snapshot version, for example `0.0.0-dev-20260414171923`.
   Find it in the PR comment or in the Snapshot Release workflow output.
7. In the library, remove the local link: `npm run yalc:cleanup`.
8. In moonbeam, install the exact version:
   ```bash
   npm install --save-exact @observepoint/ui-components@<version>
   ```
   Always use `--save-exact`. `npm run lint:pkg` fails on a range or a yalc link.
9. Run `npm run lint:pkg` and `npm run lint:theme` in moonbeam. Both must pass.
10. Ask the user, then commit `package.json` and `package-lock.json` together, with the moonbeam ticket key.

Never commit a yalc link. CI rejects it.

## Verify visual changes by measuring

"It looks right" is not a check. In the browser, read the real values:
`getBoundingClientRect()` for size and position, `getComputedStyle()` for colour.
Wait for the dev server to finish its rebuild before you measure. Check light and dark themes.
