# lambdas review patterns

**Too few comments for real patterns.** Built on 2026-11-05 from human review comments on `observepoint/lambdas` PRs merged or closed from 2025-11-01 to 2026-11-05. The source was 22 PRs. After the filter, 18 comments on 7 PRs were left, and 6 of those are approvals with a short note. The filter removed bots, authors replying on their own PR, and approval-only text. No item below reaches 3 comments on more than one PR. Treat them as hints, not rules. Refresh this file when the repo has about 20 more reviewed PRs.

How to use it: check the diff against each item. Report a hit only when the diff adds or changes the code in question.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Use current versions of the Node runtime, AWS provider and Terraform.
Kind: quality
The reviewer asked for `nodejs24.x` as the Lambda runtime, the latest AWS provider and the latest Terraform version, so the code stays ahead of AWS deprecations. Keep the module default and the caller in step.
Check: a `runtime = "nodejs` value below 24; `required_version` or the `aws` provider pinned below the current release; a module default that differs from the value the caller passes.
Seen: 4 comments, 1 PR (#145). https://github.com/observepoint/lambdas/pull/145#discussion_r3706335390, https://github.com/observepoint/lambdas/pull/145#discussion_r3706346546
Raised by: robbimount
In docs: no

### 2. Follow the Terraform backend layout: one folder and one `.tfbackend` file per environment.
Kind: quality
The reviewer asked to set the S3 backend through a `tfbackend` file per environment, with one folder per environment, as in `data-collection-api/lambdas/site-census-sitemap-harvester/terraform/`.
Check: a new `terraform/` folder whose `backend "s3"` block holds the bucket and key inline, or that has no per-environment folders.
Seen: 1 comment, 1 PR. https://github.com/observepoint/lambdas/pull/145#discussion_r3686845247
Raised by: robbimount
In docs: no

### 3. Recover from a dropped DB connection in a warm Lambda.
Kind: breaks
A module-level connection pool lives as long as the Lambda stays warm, and it can hand a dead connection to the next call. The reviewer asked to catch connection errors (`PROTOCOL_CONNECTION_LOST`, `ECONNRESET`, `ETIMEDOUT`), reset the pool and retry. In an authorizer, let the error reach API Gateway as a 500 instead of a quiet deny.
Check: a module-level `let pool`, `poolPromise` or client with no reset on connection errors; a `catch` in an authorizer that turns a DB error into a deny.
Seen: 2 comments, 1 PR (#140). https://github.com/observepoint/lambdas/pull/140#discussion_r3304637335, https://github.com/observepoint/lambdas/pull/140#discussion_r3304701526
Raised by: robbimount
In docs: no

### 4. Keep shared state correct when a later step fails.
Kind: breaks
In a key rotator, the regenerate step can succeed and the Secrets Manager write can then fail. The old key stays in Secrets Manager and later rotations get stuck.
Check: two writes to different systems in one handler with no rollback, retry or alert when the second write fails.
Seen: 1 comment, 1 PR. https://github.com/observepoint/lambdas/pull/149#discussion_r4063546302
Raised by: preston-ilities
In docs: no

### 5. Find every place that pins the deployed version.
Kind: breaks
A Lambda@Edge version is pinned by ARN in `observepoint/moonbeam` (`terraform/main.tf`). An apply in this repo alone leaves CloudFront on the old version. When a Lambda change must reach a consumer, find where its ARN or version is pinned and update that repo too.
Check: a change to a Lambda that CloudFront or another repo references by version ARN, with no note about the matching change there.
Seen: 1 comment, 1 PR. https://github.com/observepoint/lambdas/pull/151#discussion_r4147029942
Raised by: jackmparker
In docs: no

### 6. Keep the change inside the Lambda folder, and keep CI lean.
Kind: quality
Single comments asked whether a root `package.json` was needed outside the Lambda folder, whether a CI test step related to the deployment at all, and to use `|` in CircleCI path filters instead of repeated lines. One review reminded the author that a change to the authorizer logic must also go to the other authorizer Lambda.
Check: new files at the repo root for a single Lambda; repeated `path-filtering` lines that differ by one path; a change to `authorizer/` or `token-authorizer/` logic that is not in the other one.
Seen: 4 comments, 3 PRs. https://github.com/observepoint/lambdas/pull/143#discussion_r3461872521, https://github.com/observepoint/lambdas/pull/146#pullrequestreview-4977015003
Raised by: robbimount, Vorelli
In docs: no

## Lint rule candidates

- Lambda `runtime` below `nodejs24.x` in Terraform (pattern 1).
- `backend "s3"` block with an inline bucket and key (pattern 2).

## Lint already catches

- Only `stripe-webhook-handler/` has a formatter config (Prettier). No other Lambda has a linter or formatter config in the repo.
