# Review patterns: observepoint/api

Built on 2026-11-05 from 102 pull requests (PRs) closed or merged between 2025-11-03 and 2026-11-04 (84 merged). Source: inline review comments, review bodies and PR conversation comments from `gh api` (`pulls/N/comments`, `pulls/N/reviews`, `issues/N/comments`). Bots and PR authors are removed. That leaves 81 reviewer comments on 28 PRs, about 70 after short praise is removed. The patterns were grouped by hand.
Refresh this file after about 40 more merged PRs, or when a new reviewer starts to review often.

**Thin data.** Most PRs here merge with no human comment. Each pattern below rests on 3 to 8 comments, often from 2 or 3 PRs. Treat them as strong hints, not settled team rules. Most comments come from robbimount, yevhen-shumeiko-op and yurii-nesteruk-op.

Stack: Scala 2.11, Akka HTTP, spray-json, jOOQ (type-safe SQL), sbt, Terraform. Config is a Typesafe config file built from `api/src/main/resources/application.ctmpl`. The database schema comes from the `observepoint/schema` repo as a published version in `project/Dependencies.scala`.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Wire every new setting from Parameter Store through `application.ctmpl`
Kind: breaks
A new setting must reach the code. Put the value in SSM (AWS Systems Manager) Parameter Store, pass its ARN (Amazon Resource Name) into the task secrets in `terraform/api.tf`, map the environment variable into the `op { ... }` block of `application.ctmpl`, and read it with the config key. Reuse an existing variable when one holds the same value (for example `ENVIRONMENT`, lowercased) instead of adding a new one. A value that needs a rebuild to change anyway can be a constant in code.
Check: the diff reads a new key with `config.getString("op....")` or similar, but `application.ctmpl` has no matching entry, or `terraform/api.tf` has no matching secret. The diff adds an environment variable whose value equals one that already exists.
Seen: 8 comments on 3 PRs by one author, 3 of them replies in the same threads. https://github.com/observepoint/api/pull/1884#discussion_r3012050398 , https://github.com/observepoint/api/pull/1884#discussion_r3018732212
Raised by: robbimount (7), yurii-nesteruk-op
In docs: no (the README only says to copy `application.ctmpl` for local runs)

### 2. Remove dead code and needless layers
Kind: quality
Reviewers flag unused constructor parameters, unused values, helper files and dependencies that are no longer needed, and traits or objects that only forward to one implementation.
Check: a class takes a constructor parameter that its body never uses. A new trait has one implementation and adds nothing. A `Dependencies.scala` entry or a file has no remaining user.
Seen: 7 comments on 5 PRs. https://github.com/observepoint/api/pull/1878#discussion_r3309991335 , https://github.com/observepoint/api/pull/1890#discussion_r3184383157
Raised by: yevhen-shumeiko-op, oleksandr-nalyvaiko, robbimount, yurii-nesteruk-op
In docs: no

### 3. Batch database work and pace bulk loops
Kind: breaks
Delete or insert a list of rows in one statement, not one per row. Replace a correlated subquery in a `SELECT` list with one grouped `LEFT JOIN`. Add a delay between retries (for example deadlock retries). Scripts that call AWS in a loop pause about 100 ms per iteration.
Check: a loop runs a jOOQ `delete`, `insert` or `update` per element. A `SELECT` list contains `(SELECT COUNT(*) ...)` per row. A retry loop has no sleep or backoff. A script loops over AWS calls with no `sleep`.
Seen: 5 comments on 3 PRs. https://github.com/observepoint/api/pull/1904#discussion_r3365495403 , https://github.com/observepoint/api/pull/1918#discussion_r3418596091
Raised by: robbimount, yevhen-tymoshenko-op
In docs: no

### 4. Write short comments that say why
Kind: style
Keep comments short and clear. Remove comments that state the obvious or read like AI output; the PR description is the place for long explanations. When code exists for a non-obvious reason, add one short line that says why.
Check: a new comment block is longer than 3 lines, or repeats what the next line of code says. A new workaround or special case has no comment at all.
Seen: 5 comments on 4 PRs. https://github.com/observepoint/api/pull/1943#discussion_r4218102614 , https://github.com/observepoint/api/pull/1852#discussion_r2419117022
Raised by: yevhen-shumeiko-op (4), oleksandr-nalyvaiko
In docs: no

### 5. Change the database schema in the schema repo, then bump its version
Kind: breaks
Do not add a Flyway migration or a test-only table patch in this repo for a schema change. Merge the change in `observepoint/schema`, publish it, and bump `schema` (and `commons` when models change) in `project/Dependencies.scala`. Do not ship code that depends on a schema version that is not published yet.
Check: the diff adds a file under `api/src/main/resources/db/mysql/migrations/` or edits `api/src/test/scala/.../MysqlDatastore.scala` to create columns, and `project/Dependencies.scala` has no new `schema` version.
Seen: 4 comments on 3 PRs. https://github.com/observepoint/api/pull/1956#discussion_r4485841025 , https://github.com/observepoint/api/pull/1943#discussion_r4218217200
Raised by: yevhen-shumeiko-op (3), robbimount
In docs: partly (README "Updating Schema Version" covers the bump, but the README also still describes local Flyway migrations)

### 6. Fix every call site and every sibling endpoint
Kind: breaks
When a PR fixes one path, reviewers ask about the same code elsewhere: the `update` endpoint next to `create`, the V2 and V3 routes, and other callers of the changed helper (for example `parseAuthHeader` in `LoggingDirectives`). Fix them in the PR or name the follow-up ticket.
Check: search the repo for the changed function or the copied block. If other callers or a sibling route (`create`/`update`, V2/V3) keep the old behavior, the diff is incomplete.
Seen: 4 comments on 2 PRs. https://github.com/observepoint/api/pull/1931#discussion_r3865872628 , https://github.com/observepoint/api/pull/1927#discussion_r3765409162
Raised by: bdon-miller, roman-pasichnyk-op
In docs: no

### 7. Keep the public API backward compatible
Kind: breaks
This service is the public API. A change must not break existing scripts: a body that was ignored before must still be accepted (for example `curl -d '{}'` or `null`), and bad input must fail clearly rather than silently fall back. Do not expose internal or admin-only parameters to public API users. Think about every access path (external load balancer, `app./api`, `api./v2`) before you return a redirect.
Check: a route that ignored its body now unmarshals it. A new request field or query parameter is accepted for all users, not only admins or login-as sessions. An unmarshal failure is turned into a default value. A route returns a 3xx with a fixed `Location`.
Seen: 4 comments on 2 PRs. https://github.com/observepoint/api/pull/1943#discussion_r4138246353 , https://github.com/observepoint/api/pull/1943#discussion_r4218315084
Raised by: yevhen-shumeiko-op, jackmparker, robbimount
In docs: no

### 8. Write idiomatic Scala
Kind: style
Use `Option` chains (`Option(x).orElse(...).map(_.trim).filter(_.nonEmpty)`) instead of nested `if` checks on null. Return a case class instead of a large tuple. Put imports at the top of the file, except implicit conversions. Use a `LoadingCache` instead of hand-written get, check, put.
Check: a new method returns a tuple of 3 or more values. The diff adds `import` inside a class or method that is not an implicit. A cache is read with `get`, then `if`, then `put`.
Seen: 4 comments on 3 PRs. https://github.com/observepoint/api/pull/1898#discussion_r3190460437 , https://github.com/observepoint/api/pull/1888#discussion_r3076101534
Raised by: robbimount, yurii-nesteruk-op
In docs: no

### 9. Cover the change with tests and a staging check
Kind: quality
Reviewers ask for tests on new logic, and for extra regression testing where audits are split between V2 and V3. For data migration scripts, they ask for a written test sequence on staging.
Check: new logic in `*Ops.scala`, `*Service.scala` or a route has no new test under `api/src/test`. A one-off script has no test plan in the PR description.
Seen: 3 comments on 3 PRs. https://github.com/observepoint/api/pull/1852#issuecomment-3389111842 , https://github.com/observepoint/api/pull/1886#discussion_r3029605094
Raised by: oleksandr-nalyvaiko, robbimount
In docs: yes (README "Tests": "make sure that you covered it with tests")

## Lint rule candidates
- Run Scalastyle in CI. `scalastyle-config.xml` and the sbt plugin exist, but no CI step runs them and every check is a warning. Its checks already target `println`, magic numbers, `null`, `return`, method length and cyclomatic complexity (maximum 10).
- Add a check that fails when a new file appears under `db/mysql/migrations/` without a `schema` version change in `project/Dependencies.scala`.
- Add a check that every `op.*` config key read in code exists in `application.ctmpl`.
- Enable the scalac unused warnings (`-Ywarn-unused`, `-Ywarn-unused-import`) for pattern 2.
- Add a Scalastyle `RegexChecker` for `import` lines that are indented (imports inside a class or method).

## Lint already catches
- Deprecated API use: scalac `-deprecation` (warnings only, not fatal).
- Nothing else runs in CI. There is no scalafmt; Scalastyle is configured but not run.
