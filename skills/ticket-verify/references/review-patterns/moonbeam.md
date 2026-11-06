# moonbeam review patterns

Built on 2026-11-05 from human review comments on `observepoint/moonbeam` PRs that were opened from 2026-03-01 and are now merged or closed. The source was 945 PRs. After the filter, 946 comments on 290 PRs were left. The filter removed bots, authors replying on their own PR, and approval-only or praise-only text. Counts are approximate ("~"), because one comment can fit more than one pattern. Refresh this file each quarter, or when the lint config or `docs/code-conventions.md` changes.

How to use it: check the diff against each pattern. Report a hit only when the diff adds or changes the code in question. Do not report old code near the change. Patterns marked "In docs: yes" are here because reviewers still catch them often.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Reuse what exists. Do not write a second copy.
Kind: quality
Reviewers ask the author to extract repeated logic into one helper, or to call a helper, mapping or service that already exists. Copies drift apart when someone changes only one of them.
Check: for each new function, mapping, constant or SCSS block, search the repo for one with the same body or the same purpose (`grep` the key identifiers). Flag two near-identical methods in one file, and a new helper that repeats one in `*.helpers.ts`, `components/utilities/` or `StringUtils`.
Seen: ~35 comments, ~28 PRs. https://github.com/observepoint/moonbeam/pull/8427#discussion_r2924625910, https://github.com/observepoint/moonbeam/pull/9020#issuecomment-5617970833
Raised by: yurii-fishchuk-op, tetiana-husieva-op, dnesterenko-op, drewjex, amozh-op, VitaliiMartyniak
In docs: partly (code-conventions "Use existing utilities")

### 2. Give names that say what the thing is, and use one term per concept.
Kind: style
Reviewers ask for a rename when a name is vague (`selected`, `V2`, `permission`), tied to one entity when the code is generic (`cookieName` for cookies and tags), or different from its twin elsewhere (`undoRedo` and `history` for one feature, `isPreview` and `isPreviewTier`).
Check: for each new identifier, ask whether a reader can tell its type and job without opening the code. Flag one concept with two names in the diff, a name that contains `And` (the method does two jobs), and an entity name in code that serves several entity types.
Seen: ~22 comments, ~16 PRs. https://github.com/observepoint/moonbeam/pull/8730#discussion_r3371932438, https://github.com/observepoint/moonbeam/pull/8419#discussion_r2894292241
Raised by: tetiana-husieva-op, amozh-op, dnesterenko-op, yurii-fishchuk-op, andrii-korutchak-op
In docs: no

### 3. Put repeated literals in an enum or a constant.
Kind: quality
Reviewers flag string literals compared in logic (`'match_criteria'`, `'pill'`, `'desc'`), numbers that set a limit (`1000`, `120`), and hard-coded paths (`/reports`). They also flag a literal when an enum or a URL builder for it already exists (`ESortDirection`, `EAccountReportPathNames`, `AccountReportsUrlBuilder`). A value that the API returns must not be hard-coded (`isEditable`).
Check: flag a new string literal used in `===`, `switch` or a template comparison, a number that is not 0 or 1, a route path in a string, and a literal value where the API response has a field for it.
Seen: ~21 comments, ~16 PRs. https://github.com/observepoint/moonbeam/pull/8439#discussion_r2930555358, https://github.com/observepoint/moonbeam/pull/8792#discussion_r3482193073
Raised by: tetiana-husieva-op, dnesterenko-op, yevhen-shumeiko-op, jackmparker, drewjex
In docs: partly (Constants section covers large data, not single literals)

### 4. Remove comments that repeat the code.
Kind: style
Reviewers ask to delete or shorten comments that restate a clear name, describe the whole flow, name the call sites, or tell ticket history. Many of these comments come from AI tools, and they cost tokens in every later AI session. Keep a comment only when it says why.
Check: flag a new comment that only restates the next line or the name, a JSDoc longer than the function it documents, a comment that lists where the code is used, and a comment that names a ticket or "today's" state.
Seen: ~26 comments, ~15 PRs. https://github.com/observepoint/moonbeam/pull/9019#discussion_r3978112496, https://github.com/observepoint/moonbeam/pull/8730#discussion_r3380065351
Raised by: yevhen-shumeiko-op, tetiana-husieva-op, yurii-fishchuk-op, amozh-op, andrii-korutchak-op
In docs: no

### 5. Add tests for new helpers and new logic, and make each test able to fail.
Kind: quality
Reviewers ask for a spec for each new `*.helpers.ts` function and for changed validators. They also reject tests that compute the expected value with the function under test, and assertions that can only prove absence.
Check: every new or changed exported function in `*.helpers.ts`, `*.utils.ts` or a validator has a case in a `.spec.ts` in the diff. Flag `expect(x).toBe(sameFn(...))`, and a "not visible" assertion with no positive check.
Seen: ~16 comments, ~14 PRs. https://github.com/observepoint/moonbeam/pull/8514#discussion_r3014406078, https://github.com/observepoint/moonbeam/pull/9175#discussion_r4166608789
Raised by: dnesterenko-op, yurii-fishchuk-op, VitaliiMartyniak, yevhen-shumeiko-op, andrii-korutchak-op, AlexKokhanchuk
In docs: yes (Coverage Priority says helpers must be fully covered)

### 6. Delete what the change leaves unused.
Kind: quality
Reviewers find constants, exports, injected services, model fields, SCSS variables, demo components and `@else` branches that nothing uses after the change. Lint catches unused imports and locals only.
Check: for each symbol the diff stops using, search for other users. For each new exported constant, field or injected service, confirm that something reads it.
Seen: ~18 comments, ~14 PRs. https://github.com/observepoint/moonbeam/pull/8855#discussion_r3629058926, https://github.com/observepoint/moonbeam/pull/8462#pullrequestreview-3954287687
Raised by: tetiana-husieva-op, dnesterenko-op, jackmparker, GutzC, drewjex
In docs: no

### 7. Fix the type. Do not cast around it.
Kind: quality
Reviewers reject `as X` casts that hide a mismatch between two interfaces, an SDK type and a local copy, or a nullable value and a required field. They want the model fixed, the SDK type used, or a `?? ''` fallback.
Check: flag every new `as SomeType` in app code (`as const` is fine). Ask whether the source type is wrong, and whether a local interface duplicates an `@observepoint/api-sdk` type.
Seen: ~20 comments, ~14 PRs. https://github.com/observepoint/moonbeam/pull/8562#discussion_r3093355883, https://github.com/observepoint/moonbeam/pull/8458#discussion_r2952574023
Raised by: tetiana-husieva-op, yevhen-shumeiko-op, amozh-op, dnesterenko-op
In docs: partly (Type Safety bans `as any` and prefers SDK types; reviewers go further and question any cast)

### 8. Update every doc, comment and description that the change makes wrong.
Kind: quality
Reviewers find READMEs, `docs/*.md`, code comments and the PR description that still name deleted files, old behavior, or a count that changed. Stale agent docs are worse, because agents follow them.
Check: grep the repo for each renamed or deleted file, function, env var and constant. Read each comment within the changed lines and confirm it still matches the code. Compare the PR description with the final diff.
Seen: ~20 comments, ~12 PRs. https://github.com/observepoint/moonbeam/pull/8986#discussion_r3882174510, https://github.com/observepoint/moonbeam/pull/9352#discussion_r4399539042
Raised by: jackmparker, andrii-korutchak-op, AlexKokhanchuk, amozh-op, VitaliiMartyniak
In docs: yes (AGENTS.md "check whether the docs need an update")

### 9. Put each thing in the file its kind belongs in.
Kind: style
Interfaces go in `*.models.ts`, enums and constants in `*.constants.ts`, logic in `*.helpers.ts`, and each component in its own folder under the feature that uses it. Reviewers move items that land in the wrong file or folder.
Check: flag an `interface` declared in a helpers, service or component file, an enum or constant in `*.models.ts`, a sub-component in another component's file, and a component folder outside its parent feature.
Seen: ~20 comments, ~12 PRs. https://github.com/observepoint/moonbeam/pull/8897#discussion_r3705029301, https://github.com/observepoint/moonbeam/pull/8458#discussion_r2945357737
Raised by: tetiana-husieva-op, yurii-fishchuk-op, jackmparker, amozh-op
In docs: partly (Constants section only)

### 10. For new UI, use the library component. Do not restyle a shared component on one page.
Kind: theme
Reviewers flag hand-built cards, banners, dialogs and toggles that `op-card`, `op-info-banner`, `op-modal` or `op-toggle` already draw. They also flag `::ng-deep` or `!important` overrides of a shared component for one page, and the wrong `--op-*` role for the job (`--op-surface-sunken` on a panel). A new shared component belongs in the component library. `CLAUDE.md` limits swaps of existing controls to the ones the task changes.
Check: in new or changed markup, look for a frame, banner, modal or switch built from `div` and SCSS. Flag `::ng-deep` or `!important` aimed at a library component, and a role whose name does not match the element's job.
Seen: ~20 comments, ~11 PRs. https://github.com/observepoint/moonbeam/pull/9297#discussion_r4298273844, https://github.com/observepoint/moonbeam/pull/9302#discussion_r4330238711
Raised by: jackmparker, tetiana-husieva-op, yurii-fishchuk-op
In docs: yes (`docs/design-system-workflow.md`, Theming rule 5)

### 11. Make CI green and clear the bot criticals before review.
Kind: quality
Reviewers send PRs back for a failed DefaultPR workflow, failed tests, build warnings, and CodeRabbit or Claude criticals that the author did not read.
Check: run lint, `tsc --noEmit --isolatedModules`, the development build (no warning), and the affected specs. Read each bot "critical" or "warning" comment and fix it or reply to it.
Seen: ~12 comments, ~11 PRs. https://github.com/observepoint/moonbeam/pull/8419#pullrequestreview-3922261581, https://github.com/observepoint/moonbeam/pull/9232#discussion_r4246886718
Raised by: tetiana-husieva-op, jackmparker, VitaliiMartyniak, seojungood
In docs: yes (CONTRIBUTING "Before submitting a PR")

### 12. Do not call getters or methods from a template. Use `computed()` or a field.
Kind: quality
A getter or method in a binding runs on each render. Reviewers want `computed()`, a value set once when the data arrives, or a property on the row model (`[routerLink]="getReportLink(report)"`, `getColumnDisplayName()`).
Check: in changed templates, flag bindings that call a non-signal method or read a `get` accessor that filters, maps or builds an object or URL.
Seen: ~12 comments, ~10 PRs. https://github.com/observepoint/moonbeam/pull/8458#discussion_r2946259441, https://github.com/observepoint/moonbeam/pull/8940#discussion_r3813310601
Raised by: tetiana-husieva-op, yurii-fishchuk-op, drewjex, jackmparker
In docs: no

### 13. Cancel stale requests and guard against overlapping async work.
Kind: breaks
Reviewers find a page change or filter change that starts a new request without cancelling the last (so an old response wins), two triggers that fire two API calls, two polling timers, and actions left enabled while a save or stream runs.
Check: for each new `subscribe` driven by user input or a signal, confirm `switchMap` (not `mergeMap` or a nested subscribe) or another cancel. Flag a button that starts async work with no busy guard.
Seen: ~11 comments, ~10 PRs. https://github.com/observepoint/moonbeam/pull/8918#discussion_r3738179739, https://github.com/observepoint/moonbeam/pull/8491#discussion_r2988413954
Raised by: drewjex, jackmparker, GutzC, yurii-fishchuk-op, yevhen-shumeiko-op
In docs: no

### 14. Give each `computed()` an explicit type.
Kind: style
One reviewer asks for `computed<string>(...)` and an explicit type on `signal<boolean>(...)` on almost every PR she reviews.
Check: flag `computed(` and `signal(` with no type argument in new or changed code, unless the initial value is a plain literal.
Seen: ~16 comments, ~10 PRs. https://github.com/observepoint/moonbeam/pull/8758#discussion_r3402609077, https://github.com/observepoint/moonbeam/pull/8855#discussion_r3628988155
Raised by: tetiana-husieva-op
In docs: partly ("explicit types at consumption boundaries"; the breadcrumb example uses `computed<T>`)

### 15. Show failures. Do not swallow or cache them.
Kind: breaks
Reviewers flag `catchError(() => of([]))` or `of(null)` that hides an API failure as "no data", a failed result kept in a cache so it never retries, a success snackbar after a request was dropped, and a failed export with no message.
Check: flag each new `catchError` that returns an empty value with no user message. Flag a cache write inside an error path, and a success message that runs whether or not the work happened.
Seen: ~10 comments, ~9 PRs. https://github.com/observepoint/moonbeam/pull/9011#discussion_r3959295860, https://github.com/observepoint/moonbeam/pull/9080#pullrequestreview-5269706992
Raised by: jackmparker, drewjex, yurii-fishchuk-op, GutzC, seojungood
In docs: no

### 16. Gate new actions for read-only users and by permission.
Kind: breaks
Reviewers find buttons, menu items and pencil icons that open an editor for read-only users, permission checks that fail open on `undefined`, and checks that read stale permissions. They also find gates that hide pages read-only users must keep.
Check: for each new button, menu item or route that changes data, confirm the same gate as its siblings (`canMutateAccountResources`, the feature's permission service). Flag `!field.flag` used as a permission check, because it opens when the value is missing.
Seen: ~10 comments, ~8 PRs. https://github.com/observepoint/moonbeam/pull/9093#discussion_r4085498970, https://github.com/observepoint/moonbeam/pull/8563#discussion_r3103228774
Raised by: jackmparker, yurii-fishchuk-op, drewjex
In docs: partly (Feature Flags section, sidebar hide lists)

### 17. Name every control for assistive tech, and keep keyboard focus sane.
Kind: breaks
Reviewers flag icon buttons with no `aria-label`, one label shared by every row ("User actions"), a focusable element inside a button, `aria-disabled` with no `[disabled]`, and focus lost after a send or close.
Check: new icon-only buttons have an `aria-label` that names the row or item. No `tabindex` inside a `button` or a link. After an action disables the focused control, focus moves somewhere useful.
Seen: ~8 comments, ~8 PRs. https://github.com/observepoint/moonbeam/pull/8419#discussion_r2918107360, https://github.com/observepoint/moonbeam/pull/9081#discussion_r4075019940
Raised by: dnesterenko-op, drewjex, GutzC, amozh-op
In docs: partly (CONTRIBUTING accessibility conventions)

### 18. Pin a published `@observepoint/ui-components` version.
Kind: breaks
Reviewers flag `^` ranges, snapshots built from unmerged library PRs (snapshots get pruned), and snapshots older than a library fix the branch needs.
Check: if `package.json` changes `@observepoint/ui-components`, the version is exact, comes from a merged library change, and includes every library fix the diff relies on.
Seen: ~7 comments, ~7 PRs. https://github.com/observepoint/moonbeam/pull/8606#discussion_r3156618931, https://github.com/observepoint/moonbeam/pull/9231#discussion_r4223380791
Raised by: jackmparker, drewjex, VitaliiMartyniak, daviddelphenich-OP
In docs: partly (design-system-workflow "How the two repos connect")

### 19. Tear down each subscription.
Kind: breaks
Reviewers ask for `takeUntilDestroyed(this.destroyRef)` on component subscriptions, and `take(1)` on dialog `afterClosed()`, so subscriptions do not pile up.
Check: each new `.subscribe(` in a component or service has `takeUntilDestroyed`, `take(1)`, `first()` or a finite source. Flag a new manual `destroy$` Subject.
Seen: ~9 comments, ~6 PRs. https://github.com/observepoint/moonbeam/pull/8458#discussion_r2946057031, https://github.com/observepoint/moonbeam/pull/8458#discussion_r2946200536
Raised by: yurii-fishchuk-op, tetiana-husieva-op, drewjex
In docs: yes (State Management, "Tear down subscriptions")

### 20. Tell Angular after each async state change.
Kind: breaks
In the zoneless app, reviewers find async writes with no `markForCheck()` (a `finalize`, a poll, a form event in an OnPush child), and also extra `markForCheck()` calls that do nothing.
Check: each async callback that sets a plain field read by a template calls `markForCheck()` once, or the field is a signal.
Seen: ~7 comments, ~6 PRs. https://github.com/observepoint/moonbeam/pull/9224#discussion_r4221353765, https://github.com/observepoint/moonbeam/pull/9233#discussion_r4231962403
Raised by: GutzC, amozh-op, drewjex
In docs: yes (Change detection)

### 21. Use signals the way they are meant to work.
Kind: quality
Reviewers flag writes to a signal inside `effect()` with no `untracked`, edits to a `computed()` result, `ngOnInit` plus `signal.set()` where `linkedSignal()` fits, and plain fields or service values read inside `computed()` (which then never updates).
Check: flag `.set(` or `.update(` inside `effect(`, an object returned by `computed()` that is mutated, and a `computed()` that reads a non-signal value that can change.
Seen: ~7 comments, ~6 PRs. https://github.com/observepoint/moonbeam/pull/8514#discussion_r3014422116, https://github.com/observepoint/moonbeam/pull/8510#discussion_r3016187923
Raised by: yurii-fishchuk-op, yevhen-shumeiko-op, amozh-op, tetiana-husieva-op, drewjex
In docs: partly (prefer signals; no rules on effects)

### 22. Handle a missing lookup result.
Kind: breaks
Reviewers flag `map.get(id)` results used as if always present (which gives `[ILabel, undefined]`), `findIndex` with no `-1` branch, and `''` versus `null` used for the same "none" value in sibling code.
Check: each new `.get(`, `.find(` or `findIndex(` result is checked before use. A "no value" input uses the same sentinel as its siblings.
Seen: ~6 comments, ~5 PRs. https://github.com/observepoint/moonbeam/pull/8501#discussion_r3015248974, https://github.com/observepoint/moonbeam/pull/9374#discussion_r4399180856
Raised by: dnesterenko-op, tetiana-husieva-op
In docs: partly ("Normalize before calling methods")

### 23. Do not mutate inputs or shared arrays.
Kind: breaks
Reviewers flag in-place edits of a config passed in, of a DTO held by other code, and `sort()` on an array that a cache hands to several callers.
Check: flag `.sort(`, `.push(`, `.splice(` or property writes on a parameter, an input, or a value from a cached service call. Copy first.
Seen: ~5 comments, ~5 PRs. https://github.com/observepoint/moonbeam/pull/8521#discussion_r3039071358, https://github.com/observepoint/moonbeam/pull/9290#discussion_r4292478996
Raised by: dnesterenko-op, drewjex, amozh-op, yevhen-shumeiko-op
In docs: no

### 24. After a master merge, check that nothing was reverted.
Kind: breaks
Reviewers find merges that dropped menu items, guards or fixes from master, and renamed outputs whose old bindings came back.
Check: after a merge commit, diff the touched files against master. Confirm that each master change in those files is still present.
Seen: ~7 comments, ~4 PRs. https://github.com/observepoint/moonbeam/pull/9231#discussion_r4238434501, https://github.com/observepoint/moonbeam/pull/9231#discussion_r4238434506
Raised by: jackmparker, VitaliiMartyniak
In docs: partly (code-conventions "Output bindings")

### 25. Do not commit local files.
Kind: quality
Reviewers flag design notes, local Claude permissions in `.claude/settings.json`, and stray READMEs added by accident.
Check: flag new files under `docs/` or the repo root that the ticket did not ask for, and any change to `.claude/settings.json`.
Seen: ~4 comments, ~3 PRs. https://github.com/observepoint/moonbeam/pull/8615#discussion_r3170762876, https://github.com/observepoint/moonbeam/pull/9152#discussion_r4158485061
Raised by: drewjex, jackmparker, yurii-fishchuk-op
In docs: no

Browser QA note: about 45 review comments are screenshots of visual problems. Examples are a design mismatch with Figma, a lost hover in dark mode, uneven spacing, and text cut off at narrower widths. A diff check cannot find these. The browser QA step must check dark mode, hover states and spacing against the design.

## Lint rule candidates

- `computed()` and `signal()` with no type argument (pattern 14): a small custom rule.
- `as` assertions in app code (pattern 7): `@typescript-eslint/consistent-type-assertions` with `assertionStyle: 'never'`, as a warning, allowing `as const`.
- Getters and method calls in template bindings (pattern 12): `@angular-eslint/template/no-call-expression` with signal reads allowed, or a custom rule that flags `get` accessors used in templates.
- `subscribe()` with no teardown in components (pattern 19): a custom rule, or `rxjs-x/no-ignored-subscription`.
- `catchError` that returns `of([])` or `of(null)` (pattern 15): a custom rule that requires a disable comment with a reason.
- `.set()` or `.update()` inside `effect()` with no `untracked` (pattern 21): a custom rule.
- A new `*.helpers.ts` export with no matching `.spec.ts` (pattern 5): a CI script, not ESLint.
- Interfaces outside `*.models.ts`, and enums outside `*.constants.ts` or `*.enums.ts` (pattern 9): a custom rule.
- An `@observepoint/ui-components` version with `^` or `~` (pattern 18): add it to `npm run lint:pkg`.
- Missing semicolons and double quotes (raised by tetiana-husieva-op): `@stylistic/semi` and `@stylistic/quotes`.

## Lint already catches

- `I` prefix on interfaces and `E` prefix on enums (`@typescript-eslint/naming-convention`).
- `==` and `!=` (`eqeqeq`, from the shared library config).
- Non-null assertions `!` (`@typescript-eslint/no-non-null-assertion`).
- `any` in TypeScript and `$any()` in templates (`no-explicit-any`, `template/no-any`).
- Raw hex, `rgb()` and `$Palette` names in SCSS, and selectors that key on `.dark-theme` (Stylelint theme rules).
- Colors on Material table selectors (Stylelint `rule-selector-property-disallowed-list`).
- A `var(--op-*)` name the library does not define (`npm run lint:theme`).
- Missing OnPush: `ChangeDetectionStrategy.Eager`, zone.js and `@NgModule` are banned (`no-restricted-syntax`); Angular 22 defaults to OnPush.
- `standalone: false` (`@angular-eslint/prefer-standalone`).
- `*ngIf`, `*ngFor` and `*ngSwitch` (`template/prefer-control-flow`).
- A property that renames an UPPER_CASE constant (`moonbeam-rules/keep-constant-name`).
- An `(event)` binding with no matching output, for example after a rename (`moonbeam-rules/no-unknown-output`).
- A button that navigates instead of a link (`moonbeam-rules/prefer-link-for-navigation`).
- Unused imports and unused local variables (`@typescript-eslint/no-unused-vars`).
- `takeUntilDestroyed()` with no `DestroyRef` outside an injection context (`no-implicit-take-until-destroyed`). It does not catch a missing teardown.
- A yalc link in `package.json` (`npm run lint:pkg`).
