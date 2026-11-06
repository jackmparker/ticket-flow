# op-component-library review patterns

Built on 2026-11-05 from human review comments on `observepoint/op-component-library` PRs that were merged or closed from 2025-11-01. The source was 306 PRs (215 merged, 154 approved). 46 of them were Dependabot PRs, and most approvals carried no text. The PRs held 602 non-empty comments. After the filter, 114 comments on 45 PRs were left. The filter removed bots, authors replying on their own PR, Dependabot commands, closing notes, and approval-only or praise-only text. Counts are approximate ("~"), because one comment can fit more than one pattern. Refresh this file each quarter, or when `STYLING.md`, `.stylelintrc.json`, `eslint.config.mjs` or `AGENTS.md` changes. The library is moving into moonbeam (`packages/ui-components`). After that move, its reviews happen on moonbeam PRs, and this file needs a new source.

How to use it: check the diff against each pattern. Report a hit only when the diff adds or changes the code in question. Do not report old code near the change. Patterns marked "In docs: yes" are here because reviewers still catch them often.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Do not change what every consumer already sees. Scope the change, or call it breaking.
Kind: breaks
Reviewers find changes to a base SCSS block, a default input value, a `:root` token or a shared overlay selector that repaint every existing use of a component. Examples are banner padding and layout changed for all variants to fit one new variant, `op-table` `surface` defaulting to `card`, `--op-table-bg` moved at `:root`, and a new menu wrapper that broke an `:has()` selector in `_op-overlay.scss`.
Check: for each SCSS change outside a `&--<variant>` or opt-in class, each changed `input(...)` default, and each changed name in `_theming.scss` or `_op-overlay.scss`, ask which existing stories and moonbeam pages change. Grep moonbeam for the component selector and the token. If the change is meant for everyone, the changeset is `major` or names the visible change (see pattern 7). Otherwise scope it to the new variant or input.
Seen: ~9 comments, ~7 PRs. https://github.com/observepoint/op-component-library/pull/85#discussion_r3289468588, https://github.com/observepoint/op-component-library/pull/252#discussion_r4223381397
Raised by: dnesterenko-op, jackmparker, amozh-op, yurii-fishchuk-op, drewjex
In docs: partly (AGENTS.md "grep moonbeam before removing a name"; pr-and-changesets.mdx "major: breaking change")

### 2. Remove comments that repeat the code. Keep JSDoc short.
Kind: style
Reviewers ask to delete or shorten long JSDoc blocks, HTML usage examples inside component comments, "keyboard info" notes in stories, and comments in SCSS files. Keep a comment only when it says why.
Check: flag a new comment that restates the next line or the name, a JSDoc longer than the code it documents, an HTML example in a `.ts` comment, and a comment in a `.scss` file that does not explain a non-obvious choice.
Seen: ~17 comments, ~6 PRs. https://github.com/observepoint/op-component-library/pull/232#discussion_r4105122930, https://github.com/observepoint/op-component-library/pull/215#discussion_r3967863871
Raised by: yevhen-shumeiko-op, tetiana-husieva-op
In docs: no

### 3. Build from the components and roles the library already has.
Kind: theme
Reviewers flag a `mat-icon` where `op-icon` exists, a hand-built chip where `op-chip` exists, a new badge that `op-pill-badge` already draws, a component that `op-chip-field` now replaces, a search box that looks different from the one in `op-select`, and hint and error text in a control that `op-form-field` should own. They also flag the wrong role for the job, for example `--op-primary` (a yellow fill) for a line that `--op-accent-interactive` covers.
Check: list each element the diff builds (button, icon, chip, input, badge, search field, footer). Search `src/lib/` for a component that does it. For each new `var(--op-*)`, compare its job with the role table in `STYLING.md` and the Color Roles story (`theme-roles.data.ts`). If a needed piece does not exist, the PR says so.
Seen: ~9 comments, ~7 PRs. https://github.com/observepoint/op-component-library/pull/302#discussion_r4457171123, https://github.com/observepoint/op-component-library/pull/281#discussion_r4353139994
Raised by: yurii-fishchuk-op, jackmparker, tetiana-husieva-op, drewjex
In docs: yes (CLAUDE.md "Build from what the design system already has"; `STYLING.md` rule 2)

### 4. Follow the styling rules that Stylelint does not check.
Kind: theme
Reviewers flag `opacity` on a disabled state (use the `op-disabled` mixin), `:host-context(.dark-theme)` blocks, a raw value as a `var()` fallback (`#fff`, `4px`), a fixed control height instead of `--op-control-height`, raw rgb shadows, hex values in `*.stories.ts`, and a `var(--op-*)` name that `_theming.scss` never declares (so the rule does nothing). Hard-coded spacing and font sizes are allowed (`STYLING.md` rule 6). Do not flag them.
Check: in changed SCSS, flag `opacity` in a disabled rule, `:host-context(`, a `var(--op-x, <raw value>)` fallback, a raw `px` on `border-radius`, `box-shadow` or a control `height`, and any hex, `rgb(` or palette `$Name` in a file on the `.stylelintrc.json` override list. In changed `.ts` stories, flag hex values. For each new `var(--op-*)` read, confirm the name exists in both scopes of `_theming.scss` or in `_dimensions.scss`.
Seen: ~11 comments, ~8 PRs. https://github.com/observepoint/op-component-library/pull/252#discussion_r4223381416, https://github.com/observepoint/op-component-library/pull/187#discussion_r3772476107
Raised by: jackmparker, drewjex, GutzC, tetiana-husieva-op
In docs: yes (`STYLING.md` rules 1, 4, 5 and "A control you cannot use is gray"; AGENTS.md theme lines 2 and 4)

### 5. Give inputs and values exact types.
Kind: quality
Reviewers ask for `input<boolean>()` instead of a bare `input()`, a string union instead of `string` for a fixed set (`target`, `'sort-up' | 'sort-down'`, or an enum when the strings repeat in the template), a type guard instead of a fragile check, no double cast to reach `globalThis`, and an `I` prefix on new interfaces. The `I` prefix is not in the library's ESLint config, and existing code is mixed (about 43 with it and 75 without). Ask for it on new interfaces only.
Check: flag `input(` and `model(` with no type argument unless the default is a plain literal, a `string` input or field that takes only a few known values, a repeated string literal in `===` or a template, `as unknown as`, and a new `interface` without the `I` prefix.
Seen: ~8 comments, ~6 PRs. https://github.com/observepoint/op-component-library/pull/106#discussion_r3441738547, https://github.com/observepoint/op-component-library/pull/189#discussion_r3774608238
Raised by: tetiana-husieva-op, jackmparker
In docs: no

### 6. Test every state the change touches, and assert exact values.
Kind: quality
Reviewers find edge states the change breaks: a paginator on page 3 after a filter drops the length to 8 or 0, a table with `showHeader=false` and edge columns, a split button with the default (not rounded) variant, a selector that matches only the icon-only button. They also reject story tests that check only the first rendered instance, or assert "not 0px" where the PR measured 8, 12 and 16px.
Check: for each changed condition or selector, list the states and variants it covers (empty, last page, header off, each size and fill) and confirm a spec or story case for each. Flag a story `play` test that uses `querySelector` on a story that renders several instances, and an assertion that passes for any value.
Seen: ~7 comments, ~5 PRs. https://github.com/observepoint/op-component-library/pull/263#discussion_r4287425027, https://github.com/observepoint/op-component-library/pull/253#discussion_r4231961915
Raised by: GutzC, seojungood, jackmparker, yevhen-shumeiko-op
In docs: partly (changing-the-design-system.md "Cover the states the component actually has")

### 7. Make the changeset and the docs match the diff.
Kind: quality
Reviewers flag a changeset that names only part of the visible change (an outlined-button color change left out), a `minor` or `patch` bump for a change that repaints existing uses, released changesets brought back by a merge from main (they would bump a major and repeat the CHANGELOG), and Storybook docs or JSDoc that still describe the old behavior.
Check: the changeset bump fits pattern 1, and its text names each visible change. No changeset in the diff matches one already in `CHANGELOG.md`. Grep `docs/` and JSDoc for each changed input, slot or class name.
Seen: ~6 comments, ~6 PRs. https://github.com/observepoint/op-component-library/pull/180#discussion_r3722770415, https://github.com/observepoint/op-component-library/pull/262#discussion_r4298422469
Raised by: jackmparker, drewjex, dnesterenko-op, yurii-fishchuk-op
In docs: yes (AGENTS.md "Every user-visible change gets a changeset" and "Keep the docs true"; pr-and-changesets.mdx)

### 8. Make CI green and clear the bot criticals before review.
Kind: quality
Reviewers send PRs back for failed checks, Claude or CodeRabbit "critical" findings the author did not answer, and a console error in Storybook.
Check: run the AGENTS.md "Before you finish" list in order. Read each bot "critical" or "warning" comment and fix it or reply to it. Open the changed stories and check the browser console.
Seen: ~5 comments, ~5 PRs. https://github.com/observepoint/op-component-library/pull/215#pullrequestreview-5153567703, https://github.com/observepoint/op-component-library/pull/182#pullrequestreview-4870587260
Raised by: tetiana-husieva-op, drewjex, dnesterenko-op
In docs: yes (AGENTS.md "Before you finish")

### 9. Check the accessibility that the a11y gate cannot see.
Kind: breaks
The gate runs axe on each story at rest. Reviewers find what it misses: clickable `div`s with no keyboard path, a CDK dialog with no accessible name because `open()` drops `ariaLabel`, a toggle whose `aria-label` and `aria-pressed` both flip (one signal is enough), visible text that differs from the text a screen reader gets, and contrast that fails only on hover in dark mode.
Check: each new click handler sits on a `button` or link. Each dialog, menu or popover the diff opens gets an accessible name. A toggle uses a static label with `aria-pressed`, or a changing label with no `aria-pressed`. For each changed hover or focus color, compute the contrast in both themes (4.5:1 for words).
Seen: ~5 comments, ~3 PRs. https://github.com/observepoint/op-component-library/pull/180#discussion_r3722770422, https://github.com/observepoint/op-component-library/pull/90#discussion_r3356931055
Raised by: jackmparker, dnesterenko-op
In docs: partly (`STYLING.md` "Words for a screen reader only"; `contrast:check` covers resting states)

### 10. Put each kind of code in its own file.
Kind: style
Reviewers ask for a separate `.html` template instead of an inline `template:`, a folder per sub-component, constants, types and interfaces out of the component file, and helper functions out of `*.models.ts`. About 95 components use `templateUrl` and 9 use inline templates.
Check: flag a new inline `template:` in a component (stories and specs are fine), a sub-component declared in another component's file, an `interface`, `type` or constant block in a component file, and a function in a `*.models.ts` file. Pure functions shared across components go under `src/shared/<area>/`.
Seen: ~6 comments, ~4 PRs. https://github.com/observepoint/op-component-library/pull/215#discussion_r3968908333, https://github.com/observepoint/op-component-library/pull/90#discussion_r3356190975
Raised by: tetiana-husieva-op, yevhen-shumeiko-op, GutzC
In docs: partly (creating-components.mdx uses `templateUrl` and names `src/shared/`)

### 11. Delete what nothing uses.
Kind: quality
Reviewers find signal inputs that no template or code reads, inputs bound by a parent but never read, a component that a newer one fully replaces, and a `console.log`. Lint does not see an unused signal input.
Check: for each new `input(`, `output(` or `model(`, confirm the component reads or emits it. For each component the diff makes redundant, say whether it is removed or kept on purpose. Flag `console.` calls in `src/lib/`.
Seen: ~5 comments, ~4 PRs. https://github.com/observepoint/op-component-library/pull/90#discussion_r3356917348, https://github.com/observepoint/op-component-library/pull/106#discussion_r3441832582
Raised by: tetiana-husieva-op, dnesterenko-op, yurii-fishchuk-op
In docs: no

### 12. Bind templates to signals or `computed()`, not to methods.
Kind: quality
A method or getter in a binding runs on every change detection. Reviewers ask for `computed()` for derived values such as `fieldDisplayType()`, `rowLinkUrl` and `rowLinkAriaLabel`.
Check: in changed templates, flag a call to a non-signal method, or a `get` accessor that maps, filters or builds a string or URL.
Seen: ~3 comments, ~3 PRs. https://github.com/observepoint/op-component-library/pull/90#discussion_r3355993823, https://github.com/observepoint/op-component-library/pull/189#discussion_r3774736612
Raised by: tetiana-husieva-op, yevhen-shumeiko-op
In docs: no

### 13. Name things for their job, and keep names searchable.
Kind: style
Reviewers ask to use the variant name the ticket gives (`promo`, not `ai-style`), to write a full BEM class name instead of composing it with `&--` (so a search finds it), to merge two inputs that serve one goal (`rowLink` and `rowLinkLabel`), and to give variables names a reader can follow.
Check: compare each new public name (input, variant, class) with the Jira ticket. Flag a class built with `&-` or `&--` when the full name is not written anywhere, two new inputs that only make sense together, and one-letter or vague variable names outside short lambdas.
Seen: ~4 comments, ~4 PRs. https://github.com/observepoint/op-component-library/pull/85#discussion_r3289468584, https://github.com/observepoint/op-component-library/pull/166#discussion_r3704563984
Raised by: dnesterenko-op, GutzC, tetiana-husieva-op, yevhen-shumeiko-op
In docs: partly (`STYLING.md` token naming only)

### 14. Keep the diff to the task.
Kind: quality
Reviewers find leftover merge conflict text, edits to files the task does not need ("Revert. Why do you need it?"), and changesets that a merge from main brought back.
Check: grep the diff for `<<<<<<<`, `=======` and `>>>>>>>`. For each changed file, name the ticket requirement it serves. After a merge from main, diff `.changeset/` against main.
Seen: ~3 comments, ~3 PRs. https://github.com/observepoint/op-component-library/pull/25#discussion_r3011336341, https://github.com/observepoint/op-component-library/pull/230#discussion_r4047055193
Raised by: jackmparker, yurii-fishchuk-op
In docs: no

Storybook QA note: about 8 review comments are screenshots or "this affects moonbeam" notes. Examples are a menu that moved, a sort state that does not show, a feature missing from the visual editor, and a console error. A diff check cannot find these. The QA step must open each changed story in light and dark mode, check hover and focus, and open one moonbeam page that uses the changed component.

## Lint rule candidates

- `console.` calls in `src/lib/**` (pattern 11): turn on `no-console` for library code. It is not set today.
- Method calls in template bindings (pattern 12): `@angular-eslint/template/no-call-expression` with signal reads allowed.
- `@Input()` and `@Output()` decorators: `@angular-eslint/prefer-signals`. Two files still use decorators.
- `input()` with no type argument (pattern 5): a small custom rule.
- `I` prefix on interfaces (pattern 5): `@typescript-eslint/naming-convention`, after the team decides, because existing code is mixed.
- Raw `px` on `border-radius`, `box-shadow` and control `height` (pattern 4): extend the Stylelint `declaration-property-value-disallowed-list` rule from the overlay folders to all of `src/lib`.
- `opacity` in a disabled rule and `:host-context(.dark-theme)` (pattern 4): a Stylelint rule.
- Hex values in `*.stories.ts` (pattern 4): a custom ESLint rule or a grep in CI.
- A `src/lib` component with no story: a CI check (drewjex cites WORK-38972).
- Formatting: `npm run format` runs Prettier, but CI does not check it. Add a `prettier --check` step.
- Inline `template:` in components (pattern 10): `@angular-eslint/component-max-inline-declarations` with `template: 0`.

## Lint already catches

- Hex, named colors and `rgb()` or `hsl()` in component SCSS (Stylelint `color-no-hex`, `color-named`, `function-disallowed-list`). It skips `src/styles/**` and the files on the `.stylelintrc.json` override list.
- Raw `px` `border-radius` and `box-shadow` in `_op-overlay.scss` and the dropdown folders (Stylelint `declaration-property-value-disallowed-list`).
- A theme name that copies a role, is a pure alias, is set in one scope only, is read nowhere, or is read with no fallback and defined nowhere (`npm run theme:prune:check`).
- Words under 4.5:1 and lines under 3:1 in resting states (`npm run contrast:check`).
- axe findings in each story at rest (a11y gate workflow).
- A user-visible PR with no changeset (`changeset-check.yml`).
- A `src/lib` folder with no component or directive (`npm run check:lib-structure`).
- `==` and `!=` (`eqeqeq`).
- `standalone: false` (`@angular-eslint/prefer-standalone`). A leftover `standalone: true` is harmless, because Angular makes components standalone by default. Do not report it.
- Component and directive selectors without the `op` prefix (`component-selector`, `directive-selector`).
- Unused imports and unused local variables (`@typescript-eslint/no-unused-vars`).
- `any` (`@typescript-eslint/no-explicit-any`, outside stories and specs).
