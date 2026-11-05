# Review patterns: observepoint/observepoint-mcp

Built on 2026-11-05 from all 353 closed or merged PRs since the repo's first PR (2026-05-18). Refresh it when the repo has about 100 more reviewed PRs, or every 3 months.

**Read this first: there is too little human review data for real patterns.** Only 29 of 303 merged PRs have a review from someone other than the author. Those reviews hold 18 human comments. 14 of them are approvals ("LGTM", "Nice work") or notes about broken CI. Only 4 comments ask for a code change, each on a different PR. One theme below has 3 of them. It is a weak signal, not a proven pattern.

Most quality control in this repo is mechanical. `npm run check` runs about 120 rules (84 repo checks, 27 local ESLint rules, type rules and tests). `AGENTS.md` names the rule that enforces each invariant. Rules marked "Judgement" there are the ones only review catches, so read them before you review.

## Patterns

### 1. Make every policy table and gate cover every name and method the change adds

Reviewers check that a new tool, method or name spelling reaches every policy that keys on it: the role check, the method-class table, the tool annotations. A gap means a client or a customer gets past a gate that should stop them.

- Check: for each new or changed tool name, method value or name form (for example a `observepoint.` namespace prefix), find every structure keyed by tool or method name (`ADMIN_ONLY_TOOLS`, `SPENDING_METHODS` in `src/server/policy/method-classes.ts`, `canCall` and `findForbiddenToolCall` in `src/http-server.ts`, annotations). Confirm each one sees the same name in the same form. A `create` or `start` method that starts a scan or crawl by default is `spends`, not `write`.
- Seen: 3 comments on 3 PRs.
  - https://github.com/observepoint/observepoint-mcp/pull/334#discussion_r4296593613 (role check ran on the raw namespaced name, so `observepoint.login_as_account` passed it)
  - https://github.com/observepoint/observepoint-mcp/pull/332#discussion_r4319551102 (`audit_write` `create` starts a scan but was published as `write`)
  - https://github.com/observepoint/observepoint-mcp/pull/198#pullrequestreview-5182269759 (tools need all safety annotations; add a check so new tools cannot skip them)
- Raised by: jackmparker (2), drewjex (1).
- In docs: partly. `AGENTS.md` invariants 4, 5, 4.8 and 4.8a cover annotations and method classes, and `name-keyed-structures`, `tool-metadata` and `admin-tool-roles` check parts of it. No rule checks that a method that spends by default is in `SPENDING_METHODS`, and no rule checks the role check against every name spelling. The fix in PR 334 added a test for that (`test/dispatch-near-match.test.ts`).

## Single comments (not yet patterns)

Each of these came up once. Check for them, but give them less weight.

- **Keep a script working on data that already exists.** A change to how the spec-sync script matches Jira tickets dropped the old token. Existing tickets held only the old token, so the first run would file duplicates. Check: when a change renames a key, token, cache entry or stored format, look for a fallback to the old form, or a migration. https://github.com/observepoint/observepoint-mcp/pull/337#discussion_r4316333106 (jackmparker). In docs: no.
- **Add a check when you fix a class of bug.** The reviewer asked for a new rule in `scripts/check-tool-metadata.mjs` so the same gap cannot come back. Check: if the diff fixes a gap that a future tool could repeat, look for a new check rule or test, with a planted-defect test (`planted-defect-tests` requires one). Same URL as PR 198 above (drewjex). In docs: yes, `AGENTS.md` 4.17 ("a check for its mechanical part").
- **Raise a budget on purpose, with a reason.** Tool description size has a budget. The reviewer agreed to raise it only because the new text could not be shorter, and asked for short descriptions over long ones. Check: a changed budget number in `scripts/check/budget-record.json` comes with a changed reason. https://github.com/observepoint/observepoint-mcp/pull/198#pullrequestreview-5182269759 (drewjex). In docs: yes, `budget-reasons` and `tool-budget` enforce it.

## Lint rule candidates

- A method whose implementation starts a scan, crawl or run unless a flag turns it off must be in `SPENDING_METHODS`.
- Every `ADMIN_ONLY_TOOLS` entry must be refused by both `canCall` and `findForbiddenToolCall` under every accepted name prefix (today a test covers this, not a general rule).
- A change that removes a token or key a script writes to Jira, a file or a cache must keep a read of the old form.

## Lint already catches

Do not report these in review. `npm run check` and the CI report fail on them.

- Formatting (Prettier: 120 columns, double quotes, trailing commas, semicolons).
- ESLint with zero warnings, including local `op/*` rules: no em dash or emoji in comments, no wire call outside `*.api.ts`, no single-letter names, no copied helpers, no direct `registerTool` outside a tool definition.
- Type check for `src` and tests.
- Missing `readOnlyHint`, `destructiveHint` or `openWorldHint`, and a write without `dryRun` (`tool-metadata`, `destructive-hint`, `open-world-hint`).
- Thick tool handlers (`thin-handlers`) and wrong module imports between layers (`module-placement`).
- Tool naming, titles and description text that disagrees with the schema (`tool-naming`, `tool-titles`, `description-integrity`, `description-freshness`, `description-language`).
- Tool surface and description size budgets (`tool-budget`, `surface-baseline`).
- Endpoints not in a vendored spec, hand-written pagers, and repeated wire functions (`endpoint-integrity`, `one-pager`, `one-wire-function`).
- Non-tenant-keyed module caches (`tenant-keyed-caches`).
- Missing eval fixtures, method-selection fixtures and find-tool phrasings for new tools (`method-fixtures`, `find-tool-coverage`, `write-coverage`, `contract-coverage`).
- Environment variables not documented in `CONFIGURATION.md` (`env-documented`) and paths in docs that do not exist (`doc-paths`).
- A new check rule without a test that watches it fail (`planted-defect-tests`).
