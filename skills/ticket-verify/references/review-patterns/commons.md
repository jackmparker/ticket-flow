# commons review patterns

**Too few comments for many patterns.** Built on 2026-11-05 from human review comments on `observepoint/commons` PRs merged or closed from 2025-11-01 to 2026-11-05. The source was 35 PRs. After the filter, 18 comments on 10 PRs were left. The filter removed bots, authors replying on their own PR, and approval-only text. Only one item below spans several PRs. The rest are hints. Refresh this file when the repo has about 20 more reviewed PRs.

How to use it: check the diff against each item. Report a hit only when the diff adds or changes the code in question.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Keep OpenAPI schemas tight: required fields, no duplicates, no unused fields.
Kind: quality
Reviewers ask for a `required` list on each new schema, for no field that repeats one on the base type (for example `emailAddress` next to the base `emailAddresses`, or `accountHasSsoEnabled` next to `accountSsoSubdomain`), and for removal of fields that nothing uses. When a value can be null in the DB but never is in practice, pick a default and drop the extra field. Date patterns use `yyyy` (calendar year), not `YYYY` (week year).
Check: a new object schema in `*.openapi.yml` or `*.openapi.yaml` with no `required`; a property on a concrete type with a name close to one on its `allOf` base; a property no Java class or consumer reads; `YYYY` in a date format string.
Seen: 5 comments, 4 PRs. https://github.com/observepoint/commons/pull/130#discussion_r3076054787, https://github.com/observepoint/commons/pull/132#discussion_r3336697161
Raised by: robbimount, Vorelli, oleksandr-nalyvaiko, preston-ilities
In docs: no

### 2. Map each timezone to the closest AWS region with explicit rules first.
Kind: breaks
On `StandardTimezones`, reviewers asked to support every IANA timezone that Java knows, not only the enum members. They asked to map named cities to the nearest supported region first (for example Denver, Boise and Phoenix to `us-west-2`, New York to the eastern region, Sydney to `australia`), then fall back to offset buckets. Watch for conflicts with helper methods such as `isAustraliaTimezone`.
Check: a change to timezone or region mapping that assigns by UTC offset alone; a mapping that contradicts an existing `is*Timezone` helper.
Seen: 7 comments, 2 PRs (#111 and #127, one feature). https://github.com/observepoint/commons/pull/111#discussion_r2550836258, https://github.com/observepoint/commons/pull/127#discussion_r2874215118
Raised by: robbimount, taylor1791
In docs: no

### 3. Check the consumers of a shared class.
Kind: breaks
This library is used by other services. A reviewer asked whether a changed class also had a copy in `data-collection-api` that needs the same update. Another noted that a change did not enforce which event types can go with which event item types.
Check: for a changed public class or enum, search other ObservePoint repos for a copy or a caller (`gh search code "<ClassName>" --owner observepoint`), and say which ones need a matching change.
Seen: 2 comments, 2 PRs. https://github.com/observepoint/commons/pull/133#discussion_r3348928355, https://github.com/observepoint/commons/pull/139#issuecomment-6298363010
Raised by: kostiantyn-dementiev-op, robbimount
In docs: partly (`java/README.md` asks for architect approval of a new library and its dependencies, not for changes to an existing one)

## Lint rule candidates

- `YYYY` in a date format pattern in an OpenAPI file or Java code (pattern 1).
- An OpenAPI object schema with `properties` and no `required` (pattern 1).

## Lint already catches

- Java formatting: Spotless runs on compile, but only in the `cryptography-utils` and `scheduling` modules. Other modules have no formatter.
- No OpenAPI linter (such as Redocly or Spectral) runs in this repo.
