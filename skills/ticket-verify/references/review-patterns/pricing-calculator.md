# pricing-calculator review patterns

Built on 2026-11-05 from human review comments on `observepoint/pricing-calculator` PRs that were opened from 2025-11-01 and are now merged or closed. The source was 79 PRs that were not from Dependabot. After the filter, 63 comments were left, and about 35 of them ask for a change, on 22 PRs. The filter removed bots, Dependabot PRs, authors replying on their own PR, and approval-only or praise-only text. Counts are approximate ("~"), because one comment can fit more than one pattern. Volume is low, so patterns with 2 or 3 comments are included. Most comments are jackmparker reviewing GutzC's Pricing Advisor (PA) 2.0 work. Refresh this file each quarter, or when `eslint.config.js` or the README changes.

How to use it: check the diff against each pattern. Report a hit only when the diff adds or changes the code in question. Do not report old code near the change. Most findings here are logic bugs that a reviewer found by tracing two functions. Trace the state flow for each change. Do not only read the changed lines.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Keep every displayed value in step with the state it explains.
Kind: breaks
The advisor has two views that write one estimate (the chat and the worksheet), plus a manual calculator. Reviewers find a price that shows one source while its breakdown popover shows another, a manual slider value that never reaches the service, a checkbox that stays ticked while the total drops it, a removed domain that dependents still point at, a re-ticked row that comes back at 0 pages, and a `linkedSignal` that resets on each round trip through the host.
Check: for each new or changed displayed number, find the state it reads and every path that writes that state (chat turn, worksheet edit, manual slider, restore, share link). Confirm that each path updates it. For each remove, untick or reset, confirm that dependent fields (for example `smokeTestOf`) are cleared or re-seeded. For each `linkedSignal`, confirm that its source does not change on an ordinary edit.
Seen: ~9 comments, ~7 PRs. https://github.com/observepoint/pricing-calculator/pull/97#discussion_r3874071925, https://github.com/observepoint/pricing-calculator/pull/92#discussion_r3759115401, https://github.com/observepoint/pricing-calculator/pull/108#discussion_r3917642435, https://github.com/observepoint/pricing-calculator/pull/104#discussion_r3917653192
Raised by: jackmparker, GutzC
In docs: partly (README "one estimate written by two views, last write wins")

### 2. Give feedback when input is rejected. Do not drop it in silence.
Kind: breaks
Reviewers find an invalid edit that returns early while the field still shows the typed value, a paste that does nothing after `preventDefault()`, a chip that commits a turn without letting the user type the number, a mode flag that stays on and rejects every later answer, and a length error that shows only after submit.
Check: for each new validation branch that returns early, confirm that it either writes the old value back, shows a message, or blocks the commit. For each mode or flag a turn sets, confirm that every exit path (chip, typed answer, cancel) clears it. Prefer cleaning a paste (strip `$`, `,`, words) over rejecting it.
Seen: ~6 comments, ~5 PRs. https://github.com/observepoint/pricing-calculator/pull/110#discussion_r3917619875, https://github.com/observepoint/pricing-calculator/pull/110#discussion_r3917619863, https://github.com/observepoint/pricing-calculator/pull/88#discussion_r3722344975, https://github.com/observepoint/pricing-calculator/pull/105#discussion_r3917660154, https://github.com/observepoint/pricing-calculator/pull/54#discussion_r3455005231
Raised by: jackmparker, GutzC
In docs: no (README says lookup failures are silent by contract; that applies to page-count and subdomain lookups, not to user input)

### 3. Keep one copy of each rule, number and template block.
Kind: quality
Reviewers flag a parse, clamp and format chain repeated in five handlers, a template block repeated in three places, and price breakpoints typed in the system prompt while `priceJourney` keeps its own copy (so a tier change leaves the prompt quoting old limits).
Check: search for the key identifiers of each new helper, threshold table or markup block. Flag a second copy. Pricing numbers that the prompt or the UI quote must come from `@op/shared`.
Seen: 3 comments, 3 PRs. https://github.com/observepoint/pricing-calculator/pull/88#discussion_r3722344982, https://github.com/observepoint/pricing-calculator/pull/35#discussion_r3336648909, https://github.com/observepoint/pricing-calculator/pull/112#discussion_r3928731600
Raised by: jackmparker
In docs: partly (README names `@op/shared` as the home of `recompute()` math)

### 4. Format money and counts exactly.
Kind: breaks
Reviewers flag a price that renders `$59,934.4/yr` (no second decimal), a compact format that turns a 1,550,100 rate break into "1.6M" (so a buyer sizes past it), and an id slug ("new-york") shown where a name ("New York") belongs.
Check: each new currency format uses 2 minimum fraction digits. A compact number that marks a price break keeps enough digits to be exact. Each id shown to a user goes through a display formatter. Update spec assertions with the format.
Seen: 3 comments, 3 PRs. https://github.com/observepoint/pricing-calculator/pull/109#discussion_r3917633908, https://github.com/observepoint/pricing-calculator/pull/97#discussion_r3874071920, https://github.com/observepoint/pricing-calculator/pull/107#discussion_r3917642566
Raised by: jackmparker
In docs: no

### 5. Treat 0 as a real answer.
Kind: breaks
`Math.round(0 * 100) || 10` turns a 0% share into 10%, and a bridge turns an answered 0 journey runs into `null`. Both change the price with no sign to the user.
Check: flag `|| <default>` on a numeric value and a truthy check (`if (x)`) on a count or share. Use `??` with a finite check. For each new bridge or mapper, confirm that 0, `'staging'` and other non-default answers round-trip.
Seen: ~2 comments, 2 PRs (the first names a second copy of the same line). https://github.com/observepoint/pricing-calculator/pull/133#discussion_r4028438709, https://github.com/observepoint/pricing-calculator/pull/103#discussion_r3915134099
Raised by: jackmparker
In docs: no

### 6. Check the order of async work, effects and commits.
Kind: breaks
Reviewers flag effects that replaced input setters (an effect runs later, so a consumer that reads the service on the next line sees a stale value, and a default URL can flash on load), and follow-up chat lines appended after the commit that already pushed the next turn's bubble.
Check: when a setter becomes an `effect()`, list who reads the value right after the input is set. When a turn appends messages, confirm that they go in before `engine.answer` commits.
Seen: 3 comments, 2 PRs. https://github.com/observepoint/pricing-calculator/pull/24#discussion_r3237188279, https://github.com/observepoint/pricing-calculator/pull/24#discussion_r3237188283, https://github.com/observepoint/pricing-calculator/pull/111#discussion_r3928726930
Raised by: drewjex, jackmparker
In docs: no

### 7. Add or update tests for pure helpers and changed numbers.
Kind: quality
Reviewers ask for cases on a new pure validator (`"1,234 pages"`, `"$1,000"`, `"1.5M"`, `"."`, `""`), and send back PRs whose unit tests still assert the old values.
Check: each new or changed pure function in a service or `@op/shared` has spec cases for its edge inputs. Run `npm test` and the `shared` and `proxy` workspace suites. Search the specs for each constant the diff changes.
Seen: 3 comments, 3 PRs. https://github.com/observepoint/pricing-calculator/pull/88#discussion_r3722344969, https://github.com/observepoint/pricing-calculator/pull/97#pullrequestreview-4965801595
Raised by: jackmparker, seojungood
In docs: partly (README "Running unit tests")

### 8. In Terraform, order dependent resources and scope access.
Kind: breaks
Reviewers flag an SNS subscription with no `depends_on` on the topic policy (the first apply fails), service statements with no `aws:SourceAccount` condition (any account could publish to the topic), and a Lambda permission with no `qualifier` for the `live` alias (all traffic gets 403).
Check: in `packages/proxy/terraform/`, each resource that needs a policy or grant first has `depends_on`. Each service principal statement has an `aws:SourceAccount` or `aws:SourceArn` condition. Each permission for an aliased Lambda names the alias.
Seen: 3 comments, 2 PRs. https://github.com/observepoint/pricing-calculator/pull/98#discussion_r3815135393, https://github.com/observepoint/pricing-calculator/pull/98#discussion_r3853944946, https://github.com/observepoint/pricing-calculator/pull/69#discussion_r3626003665
Raised by: jackmparker, drewjex
In docs: no

**Seen once or twice, worth checking:**

- Show the model's `assistantMessage`, not the raw JSON stream, and wire the fields the model extracts (`extractedDelta`). Reuse `parsePartialJson` from v1. https://github.com/observepoint/pricing-calculator/pull/105#discussion_r3917660144, https://github.com/observepoint/pricing-calculator/pull/112#discussion_r3928731593
- Cap the decompressed size of a share link before `decode()` runs on page load. A crafted URL can hang the tab. https://github.com/observepoint/pricing-calculator/pull/133#discussion_r4028438717
- A search fallback ("add as a new place") must run only when nothing known matches, so "Cal" does not become a new place. https://github.com/observepoint/pricing-calculator/pull/107#discussion_r3917642558
- The PR description must match the diff, and must name an environment flag flip such as `environment.production.ts`. https://github.com/observepoint/pricing-calculator/pull/134#issuecomment-5721916703
- Do not add `rel="noopener"` to links to our own help docs. https://github.com/observepoint/pricing-calculator/pull/22#discussion_r3150284400

Browser QA note: reviewers often write "reasoned from source, not run". The QA step must run the flows they traced: edit a value, then edit it again; untick and re-tick a row; remove a domain that another row depends on; move a manual slider, then open the advisor breakdown; reload the tab to restore a parked session; open a share link. Compare the headline price with every breakdown after each step.

## Lint rule candidates

- `|| <number>` on numeric values (pattern 5): `@typescript-eslint/prefer-nullish-coalescing` with type information.
- Terraform scope and order (pattern 8): `tflint` plus `checkov` or `trivy config` in CI, which flag SNS and Lambda policies with no source condition.
- Currency format (pattern 4): a shared money formatter in `@op/shared`, and a `no-restricted-syntax` rule that bans `minimumFractionDigits: 0` in `src/`.
- A new pure function in `@op/shared` or a service with no spec change (pattern 7): a CI script, not ESLint.

## Lint already catches

CI runs `npm run lint`, `npm run typecheck`, and the app, `shared` and `proxy` test suites.

- `console.log` (`no-console`, `warn` and `error` allowed).
- `any` (`@typescript-eslint/no-explicit-any`) and non-null assertions `!` (`no-non-null-assertion`).
- Unused imports and variables (`@typescript-eslint/no-unused-vars`, `_` prefix allowed).
- `*ngIf`, `*ngFor` and `*ngSwitch` (`template/prefer-control-flow`).
- Constructor injection (`@angular-eslint/prefer-inject`).
- `async` with no `await` (`require-await`), and `eval`.
- Template accessibility rules (`angular.configs.templateAccessibility`).
