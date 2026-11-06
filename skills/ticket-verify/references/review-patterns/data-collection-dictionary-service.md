# Review patterns: observepoint/data-collection-dictionary-service

Built on 2026-11-05 from 31 pull requests (PRs) closed or merged between 2025-12-23 and 2026-11-04 (26 merged). Source: inline review comments, review bodies and PR conversation comments from `gh api` (`pulls/N/comments`, `pulls/N/reviews`, `issues/N/comments`). Bots and PR authors are removed. That leaves 49 reviewer comments on 12 PRs. The patterns were grouped by hand.
Refresh this file after about 20 more merged PRs, or when a second reviewer starts to review often.

**Thin data.** This repo has few human review comments, and robbimount wrote 46 of the 49. The patterns below show one reviewer's preferences, mostly from 5 PRs (#47 to #65). Treat them as strong hints, not team rules. The short list at the end holds topics with fewer than 3 comments.

Stack: Kotlin (some Java), Spring Boot, jOOQ (type-safe SQL), `openApi.yml` with generated models, Terraform in `infrastructure/`.

## Patterns

### 1. Keep the API contract clean and consistent
robbimount asks that `openApi.yml` and the DTOs (data transfer objects) say exactly what the endpoint does. Do not reuse a response DTO as a request body when some of its fields are ignored on input; extend it for the response instead. Put all request data in the body of a POST, not partly in a query parameter. Keep paths and response shapes the same as sibling endpoints (for example `/support-requests/...`). Name DTOs for their purpose (for example `SupportRequestCollection`). Return dates with a zone (UTC), like other OP responses. Validate required request fields (for example `@NotEmpty` on `requestUrl`). After a POST, return what was stored, including server fields such as `createdAt`. Update `openApi.yml` in the same PR as the DTO.
Check: a DTO used for POST or PUT has read-only fields such as `id` or `createdAt`. A POST endpoint also reads `@RequestParam`. A new path does not match the prefix of sibling endpoints. A date field is `LocalDateTime` in a response. A Kotlin DTO changed but `openApi.yml` did not.
Seen: 11 comments on 4 PRs. https://github.com/observepoint/data-collection-dictionary-service/pull/65#discussion_r3359236401 , https://github.com/observepoint/data-collection-dictionary-service/pull/63#discussion_r3269822830
Raised by: robbimount
In docs: partly (`CLAUDE.md` lists validation rules for one endpoint and says the spec drives code generation)

### 2. Make Kotlin types match reality, and avoid `!!`
If a field is required, make its type non-null instead of nullable with `@NotNull`. Give a non-null default (for example `numberJourneys: Int = 1`) instead of `Int?`. A nullable field that later needs `!!` is a sign of missing null handling and can throw a NullPointerException. Values written to S3 must be non-null. Decide once whether a missing value is `null` or `""`, and make the type say it.
Check: a new `?` type carries `@NotNull`, `@NotBlank` or `@NotEmpty`. The diff adds `!!`. A field has type `String?` with default `""`.
Seen: 7 comments on 3 PRs. https://github.com/observepoint/data-collection-dictionary-service/pull/56#discussion_r2976530673 , https://github.com/observepoint/data-collection-dictionary-service/pull/51#discussion_r2790585276
Raised by: robbimount
In docs: no

### 3. Load configuration from Secrets Manager or Parameter Store at startup
Pass configuration through AWS Secrets Manager or SSM (AWS Systems Manager) Parameter Store entries, bootstrapped in `application.properties`, not through Terraform environment variables. Inject values with `@Value` on constructor parameters, or use `lateinit var` in config classes, so a missing value fails fast. Do not give a config property a fake default, do not mark real imports `optional:`, and do not re-check config on every request (use `@PostConstruct` if a check is needed at all).
Check: the diff adds `environment` entries in `infrastructure/*.tfvars` or `*.tf`. A `@ConfigurationProperties` class has defaults such as `= ""`. A `spring.config.import` line uses `optional:`. A service method validates config on each call.
Seen: 5 comments on 2 PRs. https://github.com/observepoint/data-collection-dictionary-service/pull/56#discussion_r2976600108 , https://github.com/observepoint/data-collection-dictionary-service/pull/54#discussion_r2874117795
Raised by: robbimount
In docs: partly (`CLAUDE.md` "AWS Secrets Management" shows the import pattern but not the rules above)

### 4. Write idiomatic Kotlin and drop what is not used
Use a `data class` for models, also with validation annotations. Use `?.let { }` instead of an `if (x != null)` block. Remove Jackson annotations on classes that are never deserialized (keep `@JsonInclude`). Remove fields that only repeat the enum name.
Check: a new model is a plain `class` with only properties. A new `if (x != null)` assigns from a nullable call. `@JsonCreator` or `@JsonProperty` appears on a response-only class.
Seen: 4 comments on 3 PRs. https://github.com/observepoint/data-collection-dictionary-service/pull/63#discussion_r3268748239 , https://github.com/observepoint/data-collection-dictionary-service/pull/63#discussion_r3268606260
Raised by: robbimount, kostiantyn-dementiev-op
In docs: no

### 5. Add dependencies at their latest stable version
When a PR adds or pins a library, use the newest stable release unless there is a known conflict, so the PR does not add tech debt. Do not use an unstable version. If a version must stay pinned, add a comment that says why (for example REST Assured for integration tests).
Check: a new line in `build.gradle` names a version older than the latest release, or a milestone, release candidate (RC) or snapshot version, with no comment.
Seen: 3 comments on 2 PRs. https://github.com/observepoint/data-collection-dictionary-service/pull/63#discussion_r3268478583 , https://github.com/observepoint/data-collection-dictionary-service/pull/56#discussion_r2968296911
Raised by: robbimount
In docs: no

### Fewer than 3 comments (watch for these)
- Do not hard-code one tag (for example the AEP (Adobe Experience Platform) mapping tag) in logic or parameter names; drive it from data such as `tag_payload_mappings`. https://github.com/observepoint/data-collection-dictionary-service/pull/63#discussion_r3268667751
- Never log credentials, and do not log client errors (400) at ERROR level. These came from an AI review that robbimount posted. https://github.com/observepoint/data-collection-dictionary-service/pull/58#issuecomment-4179654707
- Keep the diff to the ticket; code from another branch slipped in. https://github.com/observepoint/data-collection-dictionary-service/pull/63#discussion_r3268585378
- Add setup docs as a section of `README.md`, not as a new file. https://github.com/observepoint/data-collection-dictionary-service/pull/54#discussion_r2874070541
- Prefer an enum to free text for status parameters, and update the spec with it. https://github.com/observepoint/data-collection-dictionary-service/pull/58#discussion_r3011263087

## Lint rule candidates
- Detekt `UnsafeCallOnNullableType`: flag `!!`.
- A custom check: flag a nullable property that also has `@NotNull`, `@NotBlank` or `@NotEmpty`.
- Warn on `optional:` in `spring.config.import`.
- Warn on new `environment` entries in Terraform task definitions.
- Detekt `UseDataClass` and `UseLet`-style rules.

## Lint already catches
- Formatting and import order: Spotless runs google-java-format for Java and ktfmt for Kotlin, `compileJava` depends on `spotlessApply`, and a pre-commit hook applies it.
- Indent, line endings and final newline: `.editorconfig`.

## New, not yet grouped
- 2026-11-06 robbimount: apply a search filter while paging upstream, not after a cap on fetched rows, so a search reaches every record. https://github.com/observepoint/data-collection-dictionary-service/pull/77#discussion_r4496105684
- 2026-11-06 robbimount: do not make per-row HTTP calls (contact or admin enrichment) for a whole list when only one page is returned. https://github.com/observepoint/data-collection-dictionary-service/pull/77#discussion_r4496105701
- 2026-11-06 robbimount: when a list is capped, tell the client (a truncated flag), not only a server log. https://github.com/observepoint/data-collection-dictionary-service/pull/77#discussion_r4496105709
- 2026-11-06 robbimount: compute a sort key once per row; parsing (with thrown exceptions) inside a comparator runs on every comparison. https://github.com/observepoint/data-collection-dictionary-service/pull/77#discussion_r4496105722
- 2026-11-06 robbimount: a comparator that mixes numeric and text order is not transitive and can make TimSort throw. https://github.com/observepoint/data-collection-dictionary-service/pull/77#discussion_r4496105763
- 2026-11-06 robbimount: guard int arithmetic on client-supplied offsets against overflow. https://github.com/observepoint/data-collection-dictionary-service/pull/77#discussion_r4496105780
- 2026-11-06 robbimount: do not copy the same paging loop into two services; put it in one helper in util/. https://github.com/observepoint/data-collection-dictionary-service/pull/77#discussion_r4496105807
- 2026-11-06 robbimount: every new util class gets its own unit test, like the others in src/test/kotlin/.../util/. https://github.com/observepoint/data-collection-dictionary-service/pull/77#discussion_r4496105842
