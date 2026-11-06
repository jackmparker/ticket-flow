# authentication review patterns

Built on 2026-11-05 from human review comments on `observepoint/authentication` PRs merged or closed from 2025-11-01 to 2026-11-05. The source was 129 PRs. After the filter, 268 comments on 67 PRs were left. The filter removed bots (including Copilot), authors replying on their own PR, and approval-only text. About 130 of the 268 are praise, follow-up replies or one-off domain questions, so they fit no pattern. Counts come from hand labels on each comment. Refresh this file every six months, or when `CLAUDE.md`, the Spotless config or the OpenAPI workflow changes.

How to use it: check the diff against each pattern. Report a hit only when the diff adds or changes the code in question. Patterns marked "In docs: yes" stay here because reviewers still catch them. Most comments come from one reviewer (robbimount), so these patterns show his standards most of all.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Define new endpoints in `AUTHENTICATION-API.openapi.yaml` and implement the generated interface.
Kind: quality
Reviewers ask that every new endpoint and its DTOs live in `AUTHENTICATION-API.openapi.yaml`, and that the controller implements the interface that codegen makes from the `operationId`. They ask to remove new entries from the legacy `swagger.yaml`, and to not hand-write DTOs that codegen makes. A spec entry for an endpoint that a hand-written controller also serves makes a generated stub that returns NOT_IMPLEMENTED and can shadow the real one.
Check: a new `@RestController` or `@GetMapping`/`@PostMapping` that does not implement a generated `*Api` interface; any added line in `swagger.yaml`; a new hand-written request or response DTO for an endpoint that is in the OpenAPI spec; a spec path that a manual controller also maps.
Seen: 13 comments, 8 PRs. https://github.com/observepoint/authentication/pull/311#discussion_r3668845089, https://github.com/observepoint/authentication/pull/344#discussion_r3926972247
Raised by: robbimount, bdon-miller
In docs: partly (CLAUDE.md names the spec file and bans new `swagger.yaml` entries. It does not mention the generated interface or the stub shadowing.)

### 2. Reuse an existing helper or pattern. Do not write a second copy.
Kind: quality
Reviewers point to helpers that already exist: `CryptoUtils.generateUrlSafeToken`, `Role.isObservepointAdmin()`, `MetadataUrlValidator`, the certificate validator, `UserCredentials` and its status checks, and the pagination helper DTO that DC-API and Reporting API use. They also flag a copy of query-string building or a constant that another class or test already has. Copies drift apart.
Check: for each new private helper, token generator, URL or query builder, role check or validator, grep the repo for one with the same job. Flag a literal role comparison where a `Role` method exists, and a test constant that another test file already defines.
Seen: 12 comments, 7 PRs. https://github.com/observepoint/authentication/pull/344#discussion_r3926944499, https://github.com/observepoint/authentication/pull/325#discussion_r3768074114
Raised by: robbimount, bdon-miller, preston-ilities
In docs: no

### 3. Log rejections with a fixed prefix and the ids, and set New Relic context at the start.
Kind: quality
Reviewers ask for a log line at each place a request is rejected, with the reason and ids (`userId`, `accountId`, username), behind a standard prefix that is easy to search, such as `job=oauth-validation validation-result=... userId=...`. They ask to keep log lines that can show abuse, such as user enumeration. They also ask that `NewRelicContext.setAccountId()`/`setUserId()` run at the start of a request, not at its end. They push back on log levels that raise prod volume a lot.
Check: a new early `return`, `throw` or rejection branch in an auth flow with no log line; a removed log line on a failure path; a log message without ids or a searchable prefix; a `NewRelicContext` call placed at the end of a method; a new DEBUG level in a config that ships to prod.
Seen: 11 comments, 7 PRs. https://github.com/observepoint/authentication/pull/322#pullrequestreview-4901175089, https://github.com/observepoint/authentication/pull/286#discussion_r3096877120
Raised by: robbimount, bdon-miller, taylor1791
In docs: no

### 4. Follow the naming rules for paths, fields and enums.
Kind: style
Reviewers ask for kebab-case path segments (`email-suppression`, not `email_suppression`), `/admin/...` paths for admin-only endpoints, no version segment in paths of this service (it is served through `app.`, `api.` and `auth.`), field names that match the shared models (`emailAddress`, which `UserContext` expects), SCREAMING_SNAKE_CASE enum members, and descriptive method names and bean qualifiers. Request names describe the purpose (`OAuthLoginRequest`), not a version (`V2`).
Check: a new path with `_` or a `/v2/` segment; an admin-only route that does not start with `/admin`; a new field named `email` in a payload that other services read; an enum member in camelCase; a class or DTO with `V2` in its name.
Seen: 10 comments, 6 PRs. https://github.com/observepoint/authentication/pull/291#discussion_r3156222171, https://github.com/observepoint/authentication/pull/319#discussion_r3715741431
Raised by: robbimount, bdon-miller
In docs: no

### 5. Return the right HTTP status for each failure.
Kind: breaks
Reviewers ask that token and auth failures return 401, not a 500 from an NPE or a broad `catch`. Catch only the expected exception types (`JwtException`, `IllegalArgumentException`) and let others become a 500. A missing resource in the path returns 404, so the response does not show the state of the database. A delete that finds nothing still succeeds, since the wanted state is reached. A DB constraint violation must not surface as a 500. An `@ExceptionHandler` parameter type must match its exception, or the handler never runs. Best-effort steps such as logout must not fail the request.
Check: a `catch (Exception)` or `catch (e: Exception)` that returns 401 or 400; a nullable value dereferenced (`!!`, `.name`) on an auth path; a delete that throws when zero rows change; a unique insert with no handling for the constraint violation; a new `@ExceptionHandler` whose parameter type differs from the class in its annotation.
Seen: 9 comments, 5 PRs. https://github.com/observepoint/authentication/pull/322#discussion_r3751796589, https://github.com/observepoint/authentication/pull/245#discussion_r2504557550
Raised by: robbimount, bdon-miller, preston-ilities
In docs: no

### 6. Check authorization again in the service, not only in the controller.
Kind: breaks
Reviewers ask for a second check in the service layer: a user may not impersonate a user with a higher role, an API key query excludes deleted users, an OpAdmin or OpSysAdmin gate on new admin endpoints, a refresh token is bound to the client that asks, and a guard stops anyone from disabling the built-in `observepoint-web` OAuth client. They reject fallback values that are not real roles, and they ask to strip `\t`, `\r` and `\n` from redirect or RelayState values before checks.
Check: a new service method that acts for another user with no role comparison; a new query on users or keys with no `deleted` condition; a new admin endpoint with no role gate; a redirect target used before control characters are removed; a default role or a placeholder value in a token claim.
Seen: 9 comments, 7 PRs. https://github.com/observepoint/authentication/pull/286#discussion_r3096886054, https://github.com/observepoint/authentication/pull/328#discussion_r3804382265
Raised by: robbimount, preston-ilities, bdon-miller, taylor1791
In docs: no

### 7. Keep the flow simple. Remove extra queries and steps.
Kind: quality
Reviewers ask to drop a second DB query when the caller already has the object, to return the saved object instead of a fresh fetch, to drop a parameter that has one call site, to hold jOOQ update steps in variables instead of copying the chain, and to arrange a method around a type that is known up front. Deep nested conditionals with repeated empty returns get a request to invert or flatten them.
Check: a method that reloads an entity its caller passed in; a boolean flag parameter with one caller; the same jOOQ chain copied in two branches; more than three levels of nested `if` in a new method.
Seen: 9 comments, 8 PRs. https://github.com/observepoint/authentication/pull/245#discussion_r2504637445, https://github.com/observepoint/authentication/pull/300#discussion_r3326225040
Raised by: robbimount, Vorelli, dathegreat, bdon-miller
In docs: no

### 8. Delete what the change makes dead.
Kind: quality
Reviewers ask to delete classes, methods, DTO fields and exceptions that have no remaining references in `src/main` after the PR, methods that only tests call, commented-out code, validation for fields that product made optional (`logoutUrl`), and duplicate entries in lists.
Check: for each removed call, grep for other uses of the callee; flag a class or method left with zero non-test references; flag commented-out code blocks; flag a duplicate class in an `@ExceptionHandler` list.
Seen: 9 comments, 6 PRs. https://github.com/observepoint/authentication/pull/303#discussion_r3364652270, https://github.com/observepoint/authentication/pull/314#discussion_r3686506125
Raised by: robbimount, taylor1791, bdon-miller
In docs: no

### 9. Order side effects so a failure leaves a good state.
Kind: breaks
Reviewers ask that an email or other outside effect is the last step, after the DB work that it depends on. Write Redis after the DB commit, not before. Validate before you rotate a token, so a failed sign leaves the old token valid. Do not swallow a failed send that the user depends on, such as the only email that holds a password. When a non-critical step fails (a password hash migration), let the main action succeed and log it.
Check: an email, SQS or SNS send inside a transaction before the last DB write; a Redis write before the DB commit in the same method; a token rotation before a step that can throw; a `catch` that drops an exception from a user-critical send; a non-critical step that can block login.
Seen: 7 comments, 4 PRs. https://github.com/observepoint/authentication/pull/278#discussion_r2941089481, https://github.com/observepoint/authentication/pull/326#discussion_r3799248188
Raised by: robbimount, preston-ilities
In docs: no

### 10. Keep comments, KDoc and test names true after the change.
Kind: style
Reviewers ask to update a comment or KDoc that the change made wrong, to rename a test whose name no longer matches what it checks, and to drop Jira ticket references from KDoc (the reason goes in the commit message). They also ask for a short comment where code looks important but is only ceremony.
Check: in each changed method, read its KDoc or Javadoc and the comments above it; flag one that describes old behavior. Flag `WORK-\d+` in a KDoc or code comment. Flag a test name that states behavior the test no longer checks.
Seen: 9 comments, 3 PRs (7 of them on #379). https://github.com/observepoint/authentication/pull/379#discussion_r4461459213, https://github.com/observepoint/authentication/pull/267#discussion_r2756127609
Raised by: robbimount
In docs: no

### 11. Declare secrets and IAM in Terraform, and add test values for new properties.
Kind: breaks
Reviewers ask to declare each new secret in `terraform/secrets.tf` with a correct description, and fill the value by hand after deploy. New staging secrets must be readable by `staging_backend_dev_role`. A new AWS call (for example KMS) needs the ECS task role permission, with the ARN passed as a Terraform variable. Each new `application.properties` key needs a dummy value in the integration test copy. New routes need an API Gateway entry, and staging-only settings may be needed on prod too.
Check: a new key in `application.properties` with no matching line in the integration test properties; a secret read with no `terraform/secrets.tf` entry; a new AWS SDK client call with no IAM change; a new controller path with no change in `terraform/api.gateway.tf`.
Seen: 8 comments, 5 PRs. https://github.com/observepoint/authentication/pull/247#discussion_r2547880866, https://github.com/observepoint/authentication/pull/283#discussion_r2967967901
Raised by: robbimount
In docs: no

### 12. Use constants and jOOQ schema types, not literals.
Kind: quality
Reviewers ask for constants for map keys and other repeated strings, a name for a magic number, column references from the schema library instead of `field("...")`, and no default for an argument that callers must think about.
Check: a string literal used as a map key more than once; a number other than 0 or 1 with no named constant; `DSL.field(` or `field("` where a generated jOOQ column exists; a new Kotlin default parameter on an error code or status.
Seen: 5 comments, 4 PRs. https://github.com/observepoint/authentication/pull/245#discussion_r2504736681, https://github.com/observepoint/authentication/pull/286#discussion_r3096987040
Raised by: robbimount
In docs: no

### 13. Validate input on purpose, and before any DB access.
Kind: breaks
Reviewers ask that nullability is handled on purpose (`@NotBlank` instead of `@NotNull` for strings, or an explicit check if `@Valid` is dropped), that bad requests fail before a DB call, and that validation collects all errors instead of throwing on the first one.
Check: a new request DTO string field with `@NotNull` only; a `@Valid` parameter whose DTO has no constraints; a validation step placed after a repository call; a chain of `throw` statements in one validation method.
Seen: 5 comments, 3 PRs. https://github.com/observepoint/authentication/pull/278#discussion_r2941688043, https://github.com/observepoint/authentication/pull/255#discussion_r2640381327
Raised by: robbimount, Vorelli
In docs: no

### 14. Keep old endpoints and response shapes working until callers move.
Kind: breaks
Reviewers ask to keep the old endpoint next to a new one, because the front end and support scripts still call it. A new flow must keep the old response for each case (for example 200 with `sub_domain` for SAML users, not a 403).
Check: a changed path, method or response schema for an existing operation in the OpenAPI spec; a new error status on a path that used to return 200.
Seen: 4 comments, 2 PRs. https://github.com/observepoint/authentication/pull/311#discussion_r3668863812, https://github.com/observepoint/authentication/pull/350#discussion_r3961750306
Raised by: robbimount, preston-ilities
In docs: no

### 15. Add an index for each new lookup column, and count queries per request.
Kind: breaks
Reviewers ask for an index on `user_id` or `account_id` when a new query filters on it, replace a global `ROW_NUMBER()` derived table with an indexed lookup, and fold several queries per request into one.
Check: a new `WHERE` or `JOIN` on a column with no index in the schema; a window function over a whole table in a joined subquery; more than two repository calls on a hot path such as token validation.
Seen: 4 comments, 3 PRs. https://github.com/observepoint/authentication/pull/311#discussion_r3669591783, https://github.com/observepoint/authentication/pull/372#discussion_r4220947062
Raised by: preston-ilities, robbimount, bdon-miller
In docs: no

### 16. Keep logic out of controllers, and let Spring inject mappers.
Kind: quality
Reviewers ask that controllers only take DTOs and pass them to a service. The service maps to response objects. A MapStruct mapper with the Spring component model is injected, not made with its static factory.
Check: a controller method with more than a service call and a return; `Mappers.getMapper(` in a class where the mapper is a Spring bean.
Seen: 3 comments, 2 PRs. https://github.com/observepoint/authentication/pull/286#discussion_r3096829545, https://github.com/observepoint/authentication/pull/278#discussion_r2941548537
Raised by: robbimount
In docs: no

### 17. Write new files in Kotlin, with annotation use-site targets.
Kind: style
Reviewers ask that new classes are Kotlin, not Java. In Kotlin, Spring annotations on constructor properties name their target (`@field:`, `@param:`) so Spring reads them the right way.
Check: a new `.java` file under `src/main`; a Spring or validation annotation on a Kotlin constructor property with no use-site target.
Seen: 3 comments, 3 PRs. https://github.com/observepoint/authentication/pull/245#discussion_r2505274697, https://github.com/observepoint/authentication/pull/334#pullrequestreview-5033479241
Raised by: robbimount, bdon-miller
In docs: no (CLAUDE.md says "Java 21 with Kotlin support")

### 18. Import types. Do not write fully qualified names.
Kind: style
Reviewers ask for an import instead of a fully qualified class name. When two types share a name (`javax` and `jakarta` servlet requests), use a Kotlin import alias.
Check: a fully qualified class name (`com.`, `java.`, `jakarta.`, `javax.`) inside a method body or signature.
Seen: 3 comments, 2 PRs. https://github.com/observepoint/authentication/pull/248#discussion_r2557227242, https://github.com/observepoint/authentication/pull/254#discussion_r2641089444
Raised by: robbimount
In docs: no

### 19. Keep a feature's columns out of shared, hot-path queries.
Kind: breaks
Reviewers ask why new columns were added to a query or row mapper that login, `/validate` and other callers share, when only the new feature reads them. Every caller then pays for data it never uses, and `/validate` runs on almost every API request. They ask for a separate read on the new feature's path instead, even when that adds one query there. An extra query on a rarely used path costs less than extra columns on a hot path.
Check: new columns in a `select` or in a shared mapper such as `toUserCredentials`; new fields on a shared model such as `UserCredentials` that only some queries fill, so the rest read a default (`null` or `false`) that looks like a real value.
Seen: 4 comments, 1 PR. https://github.com/observepoint/authentication/pull/378#discussion_r4427609314, https://github.com/observepoint/authentication/pull/378#discussion_r4448922311, https://github.com/observepoint/authentication/pull/378#discussion_r4448922298
Raised by: Vorelli, robbimount
In docs: no

### 20. Read a stored rule or flag in one place only.
Kind: quality
Reviewers flag a second copy of a validity check or a flag read, because the copies drift. A copied "is this token live" `WHERE` clause keeps accepting sessions after the original gets a new rule. A flag read as `!= 0` in one place and `== 1` (`isSet()`) in another gives two answers for an unexpected stored value. They ask to extract one shared condition or to read through the repository that already owns the data. This is pattern 2 applied to queries and stored values.
Check: a new query that repeats the `WHERE` of an existing token or user check; a flag or enum column mapped in a new place when a repository already maps it; `!= 0` on a column that other code reads with `== 1`.
Seen: 2 comments, 1 PR. https://github.com/observepoint/authentication/pull/378#discussion_r4448922326, https://github.com/observepoint/authentication/pull/378#discussion_r4448922332
Raised by: robbimount
In docs: no

## Lint rule candidates

- New `.java` file under `src/main` (pattern 17).
- Fully qualified class names in code bodies (pattern 18).
- New lines added to `src/main/resources/swagger.yaml` (pattern 1).
- `WORK-\d+` inside KDoc or code comments (pattern 10).
- Path segments with `_` or `/v\d+/` in `AUTHENTICATION-API.openapi.yaml` (pattern 4).
- Enum members not in SCREAMING_SNAKE_CASE (pattern 4).
- `catch (e: Exception)` or `catch (Exception e)` that returns 401 (pattern 5).
- `Mappers.getMapper(` for a mapper with `componentModel = "spring"` (pattern 16).
- New `application.properties` key with no integration test counterpart (pattern 11).

## Lint already catches

- Java formatting: Spotless with google-java-format, applied on every `compileJava`.
- Kotlin formatting: Spotless with ktfmt, applied on every `compileJava`.
- Unused imports in Java: Spotless `removeUnusedImports`.
- Editor basics from `.editorconfig`: 2-space indent, 100-column lines, final newline, no trailing spaces.
- Use of deprecated APIs: `-Xlint` and `options.deprecation` print warnings only. They do not fail the build, so reviewers still flag deprecated constructors and `URL` over `URI`.
