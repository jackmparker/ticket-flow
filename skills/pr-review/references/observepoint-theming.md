# ObservePoint theming and design system

Applies to PRs in `observepoint/moonbeam` and `observepoint/op-component-library` that touch
anything visual: `.scss`, `.css`, component templates, theme files, design-system components or
stories. Read with *The styling hard line* in `SKILL.md`.

The two repos share one theme. The library defines every `--op-*` name; moonbeam reads them.
A rule in either repo's docs applies to both unless the doc says otherwise.

## Docs to read, every review

Read each one in full from the default branch (`master` for moonbeam, `main` for the library).
They change often, so never review from this file's summary alone. Use a local checkout
(`git fetch origin <branch>`, then `git show origin/<branch>:<path>`) or
`gh api repos/observepoint/<repo>/contents/<path>?ref=<branch> --jq .content | base64 -d`.
If a path is gone, look for the replacement in the repo's `CLAUDE.md` and `AGENTS.md`.

**op-component-library** (read for PRs in either repo):

| Path | What it holds |
|---|---|
| `CLAUDE.md`, `AGENTS.md` | Build from DS components and tokens only; the theme in five lines |
| `projects/observepoint/ui-components/src/styles/STYLING.md` | The engineer rulebook: roles, new names, fallbacks, disabled, overlays, gates |
| `docs/guides/styling-and-theming.mdx` | Short form of STYLING.md, with the role table |
| `docs/guides/design-tokens.mdx` | Palette pipeline; never add a color by hand |
| `docs/contributing/changing-the-design-system.md` | Theme, component, story and Figma must all agree; changesets |
| `docs/theme/changing-colors.mdx` | One partner per job; one-screen color overrides need a reason |
| `docs/theme/ds-coverage-gaps.mdx` | Controls and values the app builds that the DS should own |
| `docs/patterns/page-header.mdx` | Page header rules: no rebuilt title row, no margin under it |
| `docs/guides/migrating-from-moonbeam.mdx` | Old moonbeam component to library component map |

**moonbeam** (read for moonbeam PRs):

| Path | What it holds |
|---|---|
| `CLAUDE.md` | UI work belongs in the design system, not in the app |
| `docs/code-conventions.md` | Theming, tables, corner radius, component choice table, SCSS conventions |
| `docs/design-system-workflow.md` | Component or token, not page; known CSS traps |
| `docs/corner-radius.md` | Radius scale; never a literal |
| `scripts/theme/README.md` | Stylelint gates, overrides lists, deliberate exceptions |

## What to look for

Check every added or changed line against the docs. These are the violations the docs name
most often. The docs win when they disagree with this list.

**Color and mode**
- A hex, `rgb()`, `hsl()`, named color or legacy `$Name` palette variable where a
  `var(--op-*)` role belongs. Importing `styles/variables/colors.scss` (moonbeam) or
  `_colors.scss` / `_colors.generated.scss` in a component (library).
- A style keyed on the mode: `.dark-theme`, `.light-theme`, `:host-context(.dark-theme)`,
  a theme mixin included twice, or `themeService.isDarkTheme` used only to pick a color.
- A `:host-context(.light-theme)` wrapper left around rules, which silently turns them off
  in dark mode.
- A new private `--op-*` name that holds the same pair as a role, is declared in one theme
  scope only, has no reason comment, or does not follow `--op-{component}-{variant}-{property}`.
- A fallback that is a raw value, such as `var(--op-radius, 4px)`.

**Sizes and surfaces**
- A literal `px` border radius, a raw `box-shadow`, or hand-written motion or control height
  where a `_dimensions.scss` token exists. Spacing and font sizes may be literal.
- A disabled control faded with `opacity` instead of the `op-disabled` mixin.
- Background or border set on a table selector in a moonbeam component stylesheet.
- An overlay panel that paints its own background, border, radius or shadow instead of using
  `.op-overlay-surface`; an overlay rule scoped under `.op-theme`; a `panelClass` rule nested
  under `:host` or doing more than sizing.

**Design system placement**
- A generic control (button, input, select, tabs, menu, switch, search field, modal, page
  header) hand-built or restyled in moonbeam, or in a library story, when a DS component exists
  or should. A Material component restyled to look like a DS one.
- A per-page override of a DS component where a variant or input belongs in the library.
- A legacy moonbeam component used where the code-conventions table names a library one.
- A margin added under `op-page-header`, or a title row rebuilt by hand.

**Known traps**
- `op-button.some-class` or other rules that target classes on `<op-button>`: they match nothing
  at runtime. Style through `.op-btn`.
- A second rule added for an element that already has a selector in the same file.

**Gates and process**
- A file added to a Stylelint `overrides` list (`stylelint.config.mjs` in moonbeam,
  `.stylelintrc.json` in the library). The lists only shrink.
- Library: a token renamed or removed without checking moonbeam, a hand edit to a generated
  file (`_colors.generated.scss`, `theme.css`, `devtools-extension/*.js`,
  `role-panel.snippet.js`), a role change without `theme-roles.data.ts` and the What Changes
  story, or a user-visible change with no changeset.
- moonbeam: a committed yalc link, or `package.json` and `package-lock.json` pinning different
  library versions.

## Deliberate exceptions

Do not comment on these unless the PR changes the exception itself. The docs hold the current
list (`scripts/theme/README.md`, `docs/corner-radius.md`, `docs/theme/changing-colors.mdx`):

- Sign-up and login pages stay black in both modes.
- Tag category hues (`styles/global/chart.scss`), `prismjs.scss`, Material palettes and
  `third-party.scss` keep literal colors.
- Static pages under `src/main/web/static/` keep literal radii; they never load the theme.
- Deliberate `0` radii, and circles (`50%`).
- A mode-keyed block that is listed in an `overrides` list with a reason.
