# www-marketing-site and www-edge-marketing-site review patterns

This file covers two repos: `observepoint/www-marketing-site` (the WordPress theme for www.observepoint.com) and `observepoint/www-edge-marketing-site` (the Edge site theme). Built on 2026-11-05 from human review comments on PRs opened from 2025-11-01 that are now merged or closed. The source was 84 PRs that were not from Dependabot (59 and 25). After the filter, 21 comments were left, and only 9 of them ask for a change (8 in www-marketing-site, 1 in www-edge-marketing-site). The filter removed bots, Dependabot PRs, authors replying on their own PR, and approval-only or praise-only text. Refresh this file each quarter, or when `CLAUDE.md` or `includes/shared/` changes.

**There are too few review comments for recurring patterns.** Most PRs are by jackmparker and get an approval with no comment from GutzC. No item below reached 3 comments. Each item is one real finding, listed so a review agent knows what reviewers look for. Treat them as low-confidence checks. Items are from www-marketing-site unless marked "edge only".

How to use it: check the diff against each item. Report a hit only when the diff adds or changes the code in question. Do not report old code near the change. Also read `CLAUDE.md` in www-marketing-site. It holds the rules reviewers rely on (content migrations, ACF image fields, partials, admin screens), and most of them are not repeated here.

## Patterns

### 1. A content migration must not half-write content that marketing may have changed on prod.
Marketing edits production directly. A migration that keeps one field because prod changed it, but still writes the fields that go with it, leaves the page in a mixed state (old paragraph, new list repeated under it).
Check: for each migration in `migrations/`, find each field it writes only on a condition. Confirm that the fields that depend on it use the same condition. Confirm that the migration writes only the fields it names (`--fields=<a,b,c>` on scaffolds).
Seen: 1 comment, 1 PR. https://github.com/observepoint/www-marketing-site/pull/148#discussion_r4471268125
Raised by: GutzC
In docs: yes (`CLAUDE.md` "Migrations must touch only what they explicitly name")

### 2. Do not ship placeholder content to production as an indexable page.
A migration switched a live page onto a new template with Lorem ipsum panels, "[Copy TBD]" answers, and CTA buttons with `href=""` and `target="_blank"`. Staging edits do not flow to prod.
Check: grep new migrations and templates for `Lorem`, `TBD`, `href=""` and empty CTA fields. If the page must ship before marketing fills it, set `noindex, nofollow` until it is done, and add a `todo` to the migration `notes`.
Seen: 1 comment, 1 PR. https://github.com/observepoint/www-marketing-site/pull/130#discussion_r4146064917
Raised by: GutzC
In docs: partly (README describes the `notes` `todo` checklist for marketing)

### 3. Keep file-header comments true to what the code and migration do.
A template header said the template was not the live page, while the migration in the same PR made it the live page.
Check: read each header comment in a changed template or migration. Compare it with what the migrations in the diff do.
Seen: 1 comment, 1 PR. https://github.com/observepoint/www-marketing-site/pull/130#discussion_r4146064904
Raised by: GutzC
In docs: partly (`CLAUDE.md` "File-header comments explain WHY")

### 4. Form validation scripts must keep Gravity Forms' own markup and messages correct.
Two findings in one script. A blur handler returned early when a "This field is required." message was already shown, so the real domain error never replaced it. The handler also overwrote `aria-describedby` (Gravity Forms sets `gfield_description_<id>`), and the clear step removed the attribute, so the field lost its description link.
Check: in new form scripts under `assets/js/`, confirm that each error state replaces the text of an existing message. Confirm that `aria-describedby` is appended to and restored, never set or removed outright.
Seen: 2 comments, 1 PR. https://github.com/observepoint/www-marketing-site/pull/135#discussion_r4223934114, https://github.com/observepoint/www-marketing-site/pull/135#discussion_r4223934124
Raised by: GutzC
In docs: no

### 5. Remove CSS rules that do nothing.
A `flex: 0 0 304px` sat on an element whose parent was not a flex container, and a breakpoint reset undid that dead rule.
Check: for each new `flex`, `flex-basis`, `grid-*` or `order` rule, confirm that the parent is a flex or grid container at that breakpoint.
Seen: 1 comment, 1 PR. https://github.com/observepoint/www-marketing-site/pull/131#discussion_r4146063735
Raised by: GutzC
In docs: no

### 6. Do not commit empty asset files.
A new background SVG had no content.
Check: each new file under `assets/images/` or `migration-assets/` has a non-zero size, and each SVG contains drawable elements.
Seen: 1 comment, 1 PR. https://github.com/observepoint/www-marketing-site/pull/64#discussion_r3012329447
Raised by: GutzC
In docs: no

### 7. Do not add `rel="noopener"` to links to our own pages.
Reviewers want referrers on links between ObservePoint sites. The same request came up on the same ticket in `pricing-calculator`.
Check: flag `rel="noopener"` or `rel="noreferrer"` on a link to an `observepoint.com` page or help doc.
Seen: 1 comment here, 1 in pricing-calculator. https://github.com/observepoint/www-marketing-site/pull/73#discussion_r3149970063, https://github.com/observepoint/pricing-calculator/pull/22#discussion_r3150284400
Raised by: djsmith42, jackmparker
In docs: no

### 8. Do not commit merge conflict markers. (edge only)
A helper file kept `<<<<<<<` and `>>>>>>>` lines after a merge.
Check: grep the diff for lines that start with `<<<<<<<`, `=======` or `>>>>>>>`.
Seen: 1 comment, 1 PR. https://github.com/observepoint/www-edge-marketing-site/pull/4#discussion_r2561628791
Raised by: GutzC
In docs: no

Housekeeping note: jackmparker closes Dependabot PRs when a combined dependency PR already applies the bump, with a comment that names the PR or commit. For a dependency ticket, put all bumps in one PR and run the production build.

Browser QA note: most review in these repos happens in the browser, not in comments. Check a changed page at desktop and mobile widths against the Figma frame, and check that each CTA has a real link.

## Lint rule candidates

- Conflict markers (item 8): run `git diff --check` in CI, or add a Vitest test that scans tracked files.
- Placeholder content in migrations (item 2): a Vitest test that fails on `Lorem`, `TBD` or `href=""` in `migrations/` unless the page is `noindex`.
- Empty assets (item 6): a Vitest test that fails on a zero-byte or path-less SVG in `assets/images/`.
- No linter exists in either repo. Adding ESLint for `assets/js/` and Stylelint for `assets/css/` would catch dead rules and empty blocks.

## Lint already catches

- No ESLint, Stylelint or PHP linter runs in either repo.
- www-marketing-site CI runs `npm run typecheck` (TypeScript errors in `assets/js/`) and `npm test` (Vitest).
- `tests/acf-image-fields.test.ts` enforces the ACF image field rules: a 2 MB `max_size`, minimum sizes, and no `'full'` size or raw `$field['url']` in templates.
- www-edge-marketing-site has no test or typecheck script.
