# debugger-extension review patterns

Built on 2026-11-05 from human review comments on `observepoint/debugger-extension` PRs that were opened from 2025-11-01 and are now merged or closed. The source was 43 PRs that were not from Dependabot. After the filter, 28 comments were left, and 24 of them ask for a change, on 13 PRs. The filter removed bots, Dependabot PRs, authors replying on their own PR, and approval-only or praise-only text. Counts are approximate ("~"), because one comment can fit more than one pattern. Volume is low, so patterns with 2 or 3 comments are included. Most comments are jackmparker reviewing GutzC's accessibility feature work from December 2025 to March 2026. Refresh this file each quarter, or when `extension/eslint.config.mjs` or the README changes.

How to use it: check the diff against each pattern. Report a hit only when the diff adds or changes the code in question. Do not report old code near the change. CI does not run `npm run lint` or the extension's Jest tests (it runs only the `api/tag-matching` tests). Run both in `extension/` yourself.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Remove what the change leaves behind.
Kind: quality
Reviewers find unused functions, unused SCSS variables, empty rulesets, leftover comments, debug logging, and a spec that no longer tests anything. Lint reports unused TypeScript variables only as a warning, and nothing checks SCSS.
Check: for each symbol the diff stops using, search for other users. In changed `.scss` files, flag a `$variable` that nothing reads and a selector with an empty body. Flag `console.log`, commented-out code, and comments that describe a past state. Flag a spec whose cases were all removed or skipped.
Seen: ~9 comments, ~5 PRs. https://github.com/observepoint/debugger-extension/pull/201#discussion_r2976285824, https://github.com/observepoint/debugger-extension/pull/161#discussion_r2695249403, https://github.com/observepoint/debugger-extension/pull/152#discussion_r2643617727, https://github.com/observepoint/debugger-extension/pull/150#discussion_r2628651491, https://github.com/observepoint/debugger-extension/pull/220#discussion_r3572071865
Raised by: jackmparker, GutzC
In docs: no

### 2. Simplify conditions and keep chains readable.
Kind: style
Reviewers ask for `if (this._selectors?.length)` in place of a longer null and length check, for line breaks in a long `map().concat().map()` chain, and for removal of guards against a value the type says cannot occur (`startTimeStamp` is required on `IRequest`, so a `0` branch is dead and breaks sorting if it ever runs).
Check: flag `x && x.length > 0` and similar where `x?.length` does the job. Flag a chain of more than two calls on one line. For each new guard on a field, check the interface. If the field is required, ask why the guard exists.
Seen: 4 comments, 3 PRs. https://github.com/observepoint/debugger-extension/pull/159#discussion_r2683683144, https://github.com/observepoint/debugger-extension/pull/157#discussion_r2684004799, https://github.com/observepoint/debugger-extension/pull/154#discussion_r2663356612
Raised by: jackmparker, taylor1791
In docs: no

### 3. Put shared SCSS colors in the shared mixin.
Kind: theme
Components copied from moonbeam kept color values in each component file. The reviewer asked for them in the mixin the components already include.
Check: in changed `.scss` files under `apps/devtools-panel/`, flag a color value that repeats in two or more component files, or that sits next to an `@include` of a mixin that holds related colors.
Seen: 3 comments, 1 PR. https://github.com/observepoint/debugger-extension/pull/152#discussion_r2643606570, https://github.com/observepoint/debugger-extension/pull/152#discussion_r2643610305
Raised by: jackmparker
In docs: no

### 4. Do not write what current Angular does by default.
Kind: style
Reviewers ask to delete `standalone: true`, the default since Angular 19. The extension is on Angular 21. (A third comment asked for `@if` in place of `*ngIf`. Lint now catches that, so it is listed under "Lint already catches".)
Check: flag `standalone: true` in a new or changed `@Component`, `@Directive` or `@Pipe`.
Seen: 2 comments, 2 PRs. https://github.com/observepoint/debugger-extension/pull/161#discussion_r2695218470, https://github.com/observepoint/debugger-extension/pull/149#discussion_r2620798524
Raised by: jackmparker
In docs: no

**Seen once, worth checking:**

- Do not hand-edit the version line in `extension/extension/manifest.json`. CircleCI reads major.minor from it and stamps the patch number from the pipeline number. Change it only for a planned major or minor release. https://github.com/observepoint/debugger-extension/pull/242#discussion_r3936616506
- Use an enum, not a magic number, for values such as a login type. Copy the enum from moonbeam if the extension has none. https://github.com/observepoint/debugger-extension/pull/146#discussion_r2521001874
- Use a `Set` for selector lookups that run per element, and expose it from the service as `BehaviorSubject<Set<string>>`. https://github.com/observepoint/debugger-extension/pull/159#discussion_r2683732048
- Long template attribute lists should wrap onto several lines. No formatter is set up for the package. https://github.com/observepoint/debugger-extension/pull/174#discussion_r2805890669

Housekeeping note: GutzC closes Dependabot PRs that bump only a transitive dependency in `package-lock.json`, and combines direct bumps in one PR. For a dependency ticket, bump only packages listed in `package.json`, and put them in one PR.

Browser QA note: load the unpacked build from `extension/extension` in Chrome after `npm run build:dev`. Check the devtools panel and the popup, because CI does not build or test them on a PR.

## Lint rule candidates

- Run `npm run lint` and `npm test` in `extension/` on every PR in CI (all patterns).
- Raise `unused-imports/no-unused-vars` from `warn` to `error` (pattern 1).
- `no-console` with `warn` and `error` allowed (pattern 1).
- Stylelint with `block-no-empty` for empty rulesets (pattern 1). Unused SCSS variables need a custom check.
- `@typescript-eslint/prefer-optional-chain` (pattern 2).
- `standalone: true` (pattern 4): `no-restricted-syntax` on a `Property` named `standalone` with the value `true` inside a decorator.
- A formatter such as Prettier for templates (seen-once list).

## Lint already catches

These run only when someone runs `npm run lint` in `extension/`. CI does not run it.

- Unused imports (`unused-imports/no-unused-imports`, error). Unused variables are only a warning.
- `*ngIf`, `*ngFor` and `*ngSwitch` (`template/prefer-control-flow`, in angular-eslint 21 `templateRecommended`).
- `standalone: false` (`@angular-eslint/prefer-standalone`). It does not flag `standalone: true`.
- Component and directive selector prefixes (`popup`, `devtoolsPanel`).
- `any` and constructor injection are reported only as warnings (`no-explicit-any`, `prefer-inject`).
