# Review patterns: observepoint/data-collection-api

Built on 2026-11-05 from 196 pull requests (PRs) closed or merged between 2025-11-04 and 2026-11-05 (162 merged). Source: inline review comments, review bodies and PR conversation comments from `gh api` (`pulls/N/comments`, `pulls/N/reviews`, `issues/N/comments`). Bots and PR authors are removed. That leaves 433 reviewer comments on 83 PRs, about 400 after short praise is removed. The patterns were grouped by hand.
Refresh this file after about 50 more merged PRs, when a new reviewer starts to review often, or when `CLAUDE.md` or `CONTRIBUTING.md` changes.

Stack: Java and Kotlin, Spring Boot, jOOQ (type-safe SQL), Gradle modules `core`, `dc-api`, `dc-worker`, `dc-manager`, Terraform. Most reviews come from robbimount (repo owner), josephrichardson-op, Vorelli, bdon-miller, taylor1791 and kostiantyn-dementiev-op.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Keep comments and docstrings true to the current code
Kind: style
Reviewers ask that a comment describe what the code does now. Remove text that tells the PR history ("previously", "restored", "the original 30"), because squash merges remove that context. Fix comments that are wrong or inverted, and cut long AI-style paragraphs to one clear sentence. Put implementer notes in the method body, not in the caller-facing docstring.
Check: a new or changed comment contains "previously", "used to", "restored", "the original", "now that", "instead of the old", or it says the opposite of the code next to it (for example "if archived" over a `deletedAt == null` branch). A docstring is longer than the method it describes.
Seen: 24 comments on 8 PRs. https://github.com/observepoint/data-collection-api/pull/810#discussion_r3776808782 , https://github.com/observepoint/data-collection-api/pull/838#discussion_r4329841396
Raised by: josephrichardson-op (20), robbimount, bdon-miller
In docs: no

### 2. Add tests for every new branch, and use integration tests for jOOQ queries
Kind: quality
Reviewers ask for a test for each new logic path, error path and edge case. jOOQ queries need an integration test against a real database, because unit tests with mocks do not run the SQL. Assert the exact exception, not "any exception". Use parameterized tests instead of copies, and named constants instead of magic numbers in tests.
Check: a new public method, repository query or `if` branch has no new test in `src/test` or `src/integrationTest`. A new repository method has only mock-based tests. A test uses `assertThrows(Exception.class, ...)` or hard-codes a retry count that the code defines.
Seen: 19 comments on 13 PRs. https://github.com/observepoint/data-collection-api/pull/767#discussion_r3342794596 , https://github.com/observepoint/data-collection-api/pull/764#pullrequestreview-4340825476
Raised by: josephrichardson-op, robbimount, kostiantyn-dementiev-op, bdon-miller, taylor1791, Vorelli
In docs: partly (the PR template asks which tests cover the change)

### 3. Keep the OpenAPI spec consistent with the rest of the API
Kind: quality
Edit `dc-api/openapi/DATA-COLLECTION-API.openapi.yaml` the same way as existing endpoints. Bump the spec `version`. Mark internal endpoints (for example site census and the journey recorder) `x-internal: true`. Reuse `PageParam`, `PageSizeParam`, `SortDescendingParam` and `PaginationMetadata`, and the `SortingPagination` object in code. Never return a bare array at the root of a response; wrap it in an object. Enum values are snake_case and each one is described. `nullable` next to a `$ref` is ignored, so test that null values really pass. Put a new feature's controller, service and repository in one feature package (for example `sitecensus`, `customhttpheaders`).
Check: the spec changes but `info.version` does not. A new internal path lacks `x-internal: true`. A response schema has top-level `type: array`. New pagination parameters duplicate the shared ones, or page numbers start at 1. A new controller is added under `controllers/` instead of a feature package.
Seen: 13 comments on 7 PRs. https://github.com/observepoint/data-collection-api/pull/829#discussion_r4108277952 , https://github.com/observepoint/data-collection-api/pull/789#discussion_r3553153916
Raised by: robbimount, GutzC, yurii-nesteruk-op
In docs: partly (version bump and feature packages are in `CONTRIBUTING.md` and `CLAUDE.md`; `x-internal`, root arrays and shared pagination are not)

### 4. Follow the Terraform conventions of this repo
Kind: quality
Reviewers ask for least-privilege IAM (Identity and Access Management) policies with explicit resources, the resource types Terraform recommends (`aws_vpc_security_group_ingress_rule`, not inline `aws_security_group_rule`), and names that match the backing resource. Every new SQS (Simple Queue Service) queue needs OneLeet monitoring or the tag `oneleetIgnore=true`. S3 paths need a lifecycle policy. Values that never change per environment are `locals`, not variables. Revert test values in `variables.tf` before merge.
Check: a new `aws_sqs_queue` or queue module has no alarm and no `oneleetIgnore` tag. An IAM policy uses `*` in `resources`. A new S3 prefix has no lifecycle rule. A default in `variables.tf` or a `*.tfvars` value looks like a debug value. Two alarms share one name.
Seen: 13 comments on 8 PRs. https://github.com/observepoint/data-collection-api/pull/777#discussion_r3439257014 , https://github.com/observepoint/data-collection-api/pull/775#discussion_r3415389261
Raised by: robbimount, Vorelli, taylor1791, josephrichardson-op, bdon-miller
In docs: partly (`dc-api/terraform/CONTRIBUTING.md` covers file layout only)

### 5. Remove dead code and needless layers
Kind: quality
Reviewers flag unused variables, unused annotations, `try`/`catch` around code that throws no checked exception, extra transactions around one `UPDATE`, a pre-check that the `UPDATE` already does, nested `if` blocks that can merge, and private overloads used once.
Check: the diff adds a variable, parameter, data source or method that nothing reads. A `try` block catches an exception the body cannot throw. `transactionResult` wraps a single statement. A Kotlin class has both `@Slf4j` and a companion logger.
Seen: 12 comments on 10 PRs. https://github.com/observepoint/data-collection-api/pull/857#discussion_r4417742430 , https://github.com/observepoint/data-collection-api/pull/712#discussion_r2703540577
Raised by: robbimount, bdon-miller, kostiantyn-dementiev-op, vlad-yevdokymov-op, Vorelli, josephrichardson-op
In docs: no

### 6. Put configuration in SSM Parameter Store, not in environment variables
Kind: quality
New configuration goes into an SSM (AWS Systems Manager) Parameter Store entry in the service's `dc-*/terraform/params.tf`. Spring Cloud loads it at startup through the import in `application-*.properties`. Do not add task environment variables, do not also list the value in `application-*.properties`, and do not hard-code a value in `*.tfvars`. Lists that ops may change (for example blocked domains) belong in a parameter, so they change without a deploy. Do not add static credentials; integration tests already get dummy ones.
Check: the diff adds `environment` entries in `*.service.tf`, a new `${VAR}` in `application-*.properties`, or a new `@Value` key, and there is no matching `aws_ssm_parameter` in that service's `dc-*/terraform/params.tf`. A property is declared in both `params.tf` and a properties file. A constant list of domains or IDs is hard-coded in a service.
Seen: 11 comments on 7 PRs. https://github.com/observepoint/data-collection-api/pull/777#discussion_r3439243475 , https://github.com/observepoint/data-collection-api/pull/775#discussion_r3422794430
Raised by: robbimount (9), Vorelli
In docs: no

### 7. Decide on purpose whether a queue failure retries or ends
Kind: breaks
For SQS consumers, workers and Firehose writes, reviewers check each failure path. A misconfiguration, auth error, parse error or version mismatch must not mark the item as a terminal failure and acknowledge the message, because then nothing reaches the DLQ (dead-letter queue) to redrive. A logging-only field must not crash the consumer. One bad record must not drop the whole batch. Retry failed Firehose records. Do not sleep unless the message will retry. This applies to `dc-worker`, `dc-api` and the lambdas. `dc-manager` site-census consumers re-queue instead of using a DLQ, as its `CLAUDE.md` says.
Check: a `catch` turns `RestClientException`, any 4xx, or any S3 404 into a terminal status. A nullable message field reaches `LogContext` or `!!` without a guard. A loop over records stops on the first parse error. A batch insert catches an exception and drops the later chunks.
Seen: 11 comments on 7 PRs. https://github.com/observepoint/data-collection-api/pull/850#discussion_r4395116156 , https://github.com/observepoint/data-collection-api/pull/775#discussion_r3415638072
Raised by: taylor1791, robbimount, preston-ilities, bdon-miller, josephrichardson-op, Vorelli
In docs: partly (`dc-manager` `CLAUDE.md` says site-census messages re-queue instead of using a DLQ)

### 8. Scope every read and write to the account, and return the right status
Kind: breaks
Load an item with its account (and folder access) in the same query, for example `findByIdAndAccountId` or `findForWrite`, instead of fetch-then-check. Never update by ID alone. Do not echo IDs that failed an ownership check, because that lets a user list IDs across accounts. Use 403 for no permission, 404 for not found (pick one rule for audits and journeys), 409 when the item state blocks the action, and 500 for internal failure, never 400.
Check: a repository `update` or `delete` filters by ID or `lockSeq` only, with no account condition. An exception message lists the IDs that failed authorization. A new error maps an internal failure to `BAD_REQUEST`. Audit and journey versions of one endpoint return different codes for the same case.
Seen: 10 comments on 7 PRs. https://github.com/observepoint/data-collection-api/pull/838#discussion_r4315179204 , https://github.com/observepoint/data-collection-api/pull/762#discussion_r3477560087
Raised by: robbimount, vlad-yevdokymov-op, GutzC, kostiantyn-dementiev-op
In docs: no

### 9. Name things for what they do
Kind: style
Reviewers ask for renames when a name hides meaning: a function named like an event hook that returns a value, "counts" that are no longer counts, a boolean supplier called `getAsBoolean`, a noun-like name that reads as a verb, a test helper that only stubs. Give maps and lists a name that says their key and content.
Check: a new name starts with `on` but is a plain function. A variable keeps an old name after its meaning changed in the diff. A `Map` is named `map`, `result` or `data`.
Seen: 10 comments on 6 PRs. https://github.com/observepoint/data-collection-api/pull/810#discussion_r3771017116 , https://github.com/observepoint/data-collection-api/pull/744#discussion_r2980961347
Raised by: josephrichardson-op (8), vovsiichuk-op, SkyBlueObserver
In docs: no

### 10. Make concurrent work safe
Kind: breaks
Reviewers look for check-then-act races, missing `@Transactional` across steps that must succeed together, locks released between two halves of one job, row locks held across S3 or HTTP calls, opposite lock orders that can deadlock, and shared counters that are not atomic.
Check: a read decides whether an `UPDATE` runs, with no condition in the `UPDATE` itself. `SELECT ... FOR UPDATE` is followed by an S3 or HTTP call in the same transaction. Two code paths lock the same tables in different orders. A mutable field is written from several threads without `Atomic*` or `@Synchronized`.
Seen: 9 comments on 6 PRs. https://github.com/observepoint/data-collection-api/pull/853#discussion_r4406545554 , https://github.com/observepoint/data-collection-api/pull/770#discussion_r3376340205
Raised by: Vorelli, robbimount, josephrichardson-op, taylor1791, preston-ilities
In docs: no

### 11. Keep SQL bounded and set-based
Kind: breaks
Add a limit or pagination to search queries. Use one multi-row statement instead of one statement per row or per scope. Let SQL do type coercion (`.coerce(Long.class)`) and use the generated jOOQ constants instead of string table and field names. Protect large Postgres queries from bad plans as the existing site-census queries do. Convert or build expensive objects once, not per item.
Check: a repository method loops and runs a query or insert per element. A search query has no `LIMIT`. The diff uses `DSL.field("...")` or `DSL.table("...")` where a generated constant exists. A string ID is parsed to `Long` in Java after the fetch.
Seen: 9 comments on 6 PRs. https://github.com/observepoint/data-collection-api/pull/747#discussion_r3049874936 , https://github.com/observepoint/data-collection-api/pull/762#discussion_r3415429786
Raised by: robbimount, bdon-miller, kostiantyn-dementiev-op, preston-ilities, mdiachuk-op
In docs: partly (`CLAUDE.md` says repositories use jOOQ)

### 12. Extract repeated logic instead of copying it
Kind: quality
Reviewers ask to move repeated checks and message building into one method or service. This includes test setup that repeats in several tests, and guards that should be unit-tested on their own (for example a location-restriction check).
Check: the diff adds two or more blocks of 3 or more near-identical lines, in main code or tests. Logic that already exists in another service is copied instead of called.
Seen: 8 comments on 8 PRs. https://github.com/observepoint/data-collection-api/pull/768#discussion_r3344335318 , https://github.com/observepoint/data-collection-api/pull/686#discussion_r2527312231
Raised by: kostiantyn-dementiev-op, robbimount, bdon-miller, vlad-yevdokymov-op, Vorelli
In docs: no

### 13. Apply each change to every parallel path, including the user event
Kind: breaks
Audits and journeys, old and new endpoints, and sibling tables often share a flow. When one path gets a fix, a check, a notification or a column reset, reviewers ask for the same on the other. Each state change records one user event (for example `UNDELETED`), and a repeated request must not record a second one.
Check: the diff changes `WebAuditsServiceImpl` but not `WebJourneysServiceImpl`, or the reverse. A new endpoint replaces an old one but the old flow keeps the old behavior. A create, delete, archive or restore path has no `userEvent` call, or records it even when the update matched 0 rows.
Seen: 8 comments on 3 PRs. https://github.com/observepoint/data-collection-api/pull/762#discussion_r3494592988 , https://github.com/observepoint/data-collection-api/pull/857#discussion_r4417742425
Raised by: robbimount, kostiantyn-dementiev-op, bdon-miller
In docs: no

### 14. Do not edit CHANGELOG.md or bump the Gradle version
Kind: quality
robbimount retired both in mid 2026: nobody reads the `version` in `build.gradle`, it only causes merge conflicts, and `CHANGELOG.md` is no longer kept. Older reviews (January to February 2026) and `dc-api/terraform/CONTRIBUTING.md` step 3 still ask for a changelog entry. Follow the newer rule. The OpenAPI spec version is different, and it must still be bumped (pattern 3).
Check: the diff changes `version` in `build.gradle`, or adds a `CHANGELOG.md` file (master has none now).
Seen: 7 comments on 7 PRs (4 that retire the rule, 3 older ones that asked for it). https://github.com/observepoint/data-collection-api/pull/777#discussion_r3439266156 , https://github.com/observepoint/data-collection-api/pull/785#discussion_r3501645577
Raised by: robbimount; earlier the opposite by kostiantyn-dementiev-op, vlad-yevdokymov-op
In docs: no. `dc-api/terraform/CONTRIBUTING.md` step 3 still says to update the changelog; follow the newer rule.

### 15. Keep the diff to the ticket
Kind: quality
Reviewers catch changes copied from another branch, merge resolutions that silently undo master, and debug values left in. Rebase or merge master before review when a whole file was rewritten.
Check: the ticket is about one service but the diff touches `dc-manager/`, `lambdas/` or another feature package with no reason in the PR text. A rewritten file has older values than master (for example dependency versions). A config default changed with no mention in the description.
Seen: 5 comments on 4 PRs. https://github.com/observepoint/data-collection-api/pull/825#discussion_r4073051871 , https://github.com/observepoint/data-collection-api/pull/844#discussion_r4354593364
Raised by: robbimount, Vorelli, josephrichardson-op, taylor1791
In docs: no

### 16. Log at the right level, with context, and warn on silent data loss
Kind: quality
Expected traffic (for example 409 lock conflicts) does not log a stack trace at INFO. Add shared context to the logging context once, not to every message. When code truncates data with `take` or skips work, log a warning so someone can act. Prefer a metric with an alarm for warnings that must be watched.
Check: a handled client error logs at `error` or logs a full stack trace. `.take(n)` on a value written to the database has no warning. The same prefix is repeated in many log lines of one class.
Seen: 5 comments on 5 PRs. https://github.com/observepoint/data-collection-api/pull/692#discussion_r2590979041 , https://github.com/observepoint/data-collection-api/pull/838#discussion_r4329841433
Raised by: robbimount, andrii-makrushyn-op, taylor1791
In docs: no

### 17. Use enums for fixed sets of values
Kind: quality
Reviewers ask to replace string constants, status strings and action names with an enum, and to reuse an enum that already exists.
Check: the diff compares a value to two or more string literals, or adds `const val` strings for states.
Seen: 4 comments on 4 PRs. https://github.com/observepoint/data-collection-api/pull/712#discussion_r2703535506 , https://github.com/observepoint/data-collection-api/pull/777#discussion_r3439312783
Raised by: kostiantyn-dementiev-op, yelyzaveta-blyumska-op, robbimount
In docs: no

## Lint rule candidates
- Fail when `build.gradle` `version` changes, or when `CHANGELOG.md` changes.
- Fail when the OpenAPI spec changes and `info.version` does not.
- Fail when a response schema has top-level `type: array`.
- Warn on new `environment` entries in `*.service.tf` (prefer `dc-*/terraform/params.tf`).
- Warn on a new `aws_sqs_queue` without an alarm module or `oneleetIgnore` tag.
- Detekt or Error Prone: unused private members, empty or needless `try`/`catch`, nested `if` that can merge.
- Warn on comments that contain "previously", "used to", "restored" or "the original".
- Warn on `DSL.field("` or `DSL.table("` with a string name.

## Lint already catches
- Formatting, import order and unused imports: Spotless runs google-java-format for Java and ktfmt for Kotlin on every compile, and a GitHub Action commits `spotlessApply` on each PR.
- `.editorconfig` sets 100 columns, 2-space indent, final newline and no trailing spaces. The Spotless formatters enforce their own fixed style, which matches it.
- Java unchecked and deprecation warnings: `-Xlint:unchecked` and `deprecation = true` in `op.java-conventions.gradle` (warnings only).

## New, not yet grouped
- 2026-11-06 robbimount: log a 4xx that means our own request was wrong (for example a 400 from an internal service) at error level with the response's error text, not at info level like a normal user rejection. https://github.com/observepoint/data-collection-api/pull/863#discussion_r4498237875
- 2026-11-06 robbimount: give each distinct result its own sealed-type case instead of one case with a status code that callers split again. https://github.com/observepoint/data-collection-api/pull/863#discussion_r4498237884
- 2026-11-06 robbimount: do not keep the same identity twice in one object (a nullable, mutable source object and its copied ids); keep only the non-null copies. https://github.com/observepoint/data-collection-api/pull/863#discussion_r4498237890
- 2026-11-06 robbimount: an optional string field in an OpenAPI request needs `minLength: 1` when an empty value would pass a "needs X or Y" rule. https://github.com/observepoint/data-collection-api/pull/863#discussion_r4498237900
- 2026-11-06 robbimount: write an external service's limit (for example AppConfig's 15 s minimum poll) as one named constant, and `require` that configured values respect it. https://github.com/observepoint/data-collection-api/pull/863#discussion_r4498237908
