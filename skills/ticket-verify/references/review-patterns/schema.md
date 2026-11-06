# schema review patterns

Built on 2026-11-05 from human review comments on `observepoint/schema` PRs merged or closed from 2025-11-01 to 2026-11-05. The source was 92 PRs. After the filter, 65 comments on 24 PRs were left. The filter removed bots, authors replying on their own PR, and approval-only text. CodeRabbit left 112 comments in the same period. They were dropped as bot output, so they are not counted here. Most PRs merge with no human comment, so the sample is small. Several patterns rest on one or two large PRs (#462, #484, #511), and each pattern says so. Refresh this file every six months, or when `CLAUDE.md` or the PR template changes.

How to use it: check the diff against each pattern. Report a hit only when the diff adds or changes the SQL in question. Never run a migration to check a pattern. `CLAUDE.md` allows migrations only against a local database.

Kind: each pattern has one. **breaks**: a bug, data loss, a security hole, a visual or accessibility break, or a broken deploy or caller. **theme**: a documented styling or design-system rule. **quality**: code that works today but has a concrete cost later (a second copy that will drift, dead code, logic in the wrong layer, a cast that hides a wrong type). **style**: naming, comment wording, idiom and layout. `ticket-verify` checks all four kinds on your own code. `pr-review` uses breaks and theme on a teammate's PR, quality only within its limit, and never style.

## Patterns

### 1. Choose column type, nullability, default and collation on purpose.
Kind: breaks
Reviewers ask for a `DEFAULT` on a new `NOT NULL` column of an existing table, because old rows need a value. They ask whether a column should be `NOT NULL` at all when only some rows use it. Use `datetime`, not `timestamp`, which is the team rule. A foreign key column must have the same type as the column it points to (`int` to `int`). Change collation only on the columns that need it (for example `utf8mb4_bin` on ID columns), and leave names, descriptions and the table default on `utf8mb4_0900_ai_ci`.
Check: `ADD COLUMN ... NOT NULL` with no `DEFAULT`; any new `TIMESTAMP` column; a new FK column whose type differs from the referenced column; `COLLATE` or `CONVERT TO CHARACTER SET` on a whole table or on non-ID columns.
Seen: 6 comments, 5 PRs. https://github.com/observepoint/schema/pull/438#discussion_r2635713708, https://github.com/observepoint/schema/pull/458#discussion_r3200989974
Raised by: robbimount, vovsiichuk-op, kostiantyn-dementiev-op
In docs: no (a Confluence page sets column type rules, the repo docs do not)

### 2. Keep view and ad hoc SQL easy to read.
Kind: style
Reviewers ask for CTEs instead of nested subqueries, CTE and view names that follow the existing `data_dictionary_..._view` style, consistent formatting of similar column aliases, and no extra steps or columns that a simpler query avoids (a join that an earlier view already does, a check that is always true). They also flag sizes that look random (`1024` instead of `1000`, `255` with no reason).
Check: a subquery nested more than one level deep in `FROM` or `WHERE`; a new view whose name starts with `view_` while siblings end with `_view`; a join to a table that a selected view already joins; a length limit with no comment on its source.
Seen: 9 comments, 4 PRs. https://github.com/observepoint/schema/pull/484#discussion_r3912406532, https://github.com/observepoint/schema/pull/503#discussion_r4135231605
Raised by: vovsiichuk-op
In docs: no

### 3. Make migrations and ad hoc scripts safe on large, live tables.
Kind: breaks
Reviewers check that a migration does not force a long table rebuild or lock on a big table (`ALGORITHM=INPLACE` or `INSTANT` may not apply to old tables, and a drop of a column can need downtime). An ad hoc script must be safe to run twice (`WHERE NOT EXISTS` against its own copy table) and should fail fast on locks (`SET SESSION innodb_lock_wait_timeout = 10`). Comments about locking must say what really locks. A migration must not fail on staging or prod because the column or table is already there (Fivetran or stub tables). A new bookkeeping column on a table with an update trigger can bump the lock version on every write; put it in its own table or limit the trigger to certain columns.
Check: `DROP COLUMN` or `ALGORITHM=` on a large or old table; an `INSERT ... SELECT` or `UPDATE` in `ad_hoc/` with no re-run guard and no lock wait timeout; `ADD COLUMN` on a table that Fivetran or a stub migration also creates; a new column on a table that has an `UPDATE` trigger.
Seen: 6 comments, 4 PRs. https://github.com/observepoint/schema/pull/511#discussion_r4247309125, https://github.com/observepoint/schema/pull/518#discussion_r4380412503
Raised by: kostiantyn-dementiev-op, preston-ilities, robbimount, vovsiichuk-op
In docs: partly (the PR template asks about lock risk on large tables. It does not mention re-runs, lock timeouts or triggers.)

### 4. Explain columns with `COMMENT`, and keep SQL comments short and true.
Kind: style
Reviewers ask for a `COMMENT` on each column whose purpose is not clear, and on each column that holds a value from an enum table (name the enum table, such as `data_dictionary_field_formats_enum`). They ask to remove comments that number steps or restate the code, to remove words that do not apply (such as "seed values"), and to reword comments that suggest the wrong intent.
Check: a new column that holds an enum ID, status or type with no `COMMENT`; SQL comments with step numbers; a comment that describes data the migration does not insert.
Seen: 6 comments, 2 PRs (#462 and #484). https://github.com/observepoint/schema/pull/462#discussion_r3420654454, https://github.com/observepoint/schema/pull/484#discussion_r3933947093
Raised by: vovsiichuk-op
In docs: no

### 5. Check a data script against real prod data and every case it touches.
Kind: breaks
Reviewers query prod and ask about rows the script misses or breaks: alerts with the same filter under other metric types, records changed by hand after an import, filters in the JSON that are not there in prod, and a default `custom_message` that becomes wrong after the change. List the cases the ticket names and the cases the data shows, and handle or rule out each one.
Check: an ad hoc `UPDATE` or `INSERT ... SELECT` whose `WHERE` uses a fixed list of IDs or types; a script that changes a type or status but not text fields that mention the old value; a JSON rewrite with no evidence that the key exists in prod data.
Seen: 5 comments, 2 PRs (#503 and #511). https://github.com/observepoint/schema/pull/511#discussion_r4232002214, https://github.com/observepoint/schema/pull/511#discussion_r4269483997
Raised by: vovsiichuk-op, kostiantyn-dementiev-op
In docs: no

### 6. Keep the schema change in step with its sibling PRs in other repos.
Kind: breaks
Reviewers point to review threads on the matching `lakehouse` or `reporting-api` PR, and ask that the same fix lands here. They also ask that the Jira ticket explains manual steps, such as how to fill a new sheet column.
Check: a view or table that the ticket says `lakehouse` or another service also defines; if the diff changes one side, flag it so the reviewer can confirm the other PR matches.
Seen: 5 comments, 4 PRs. https://github.com/observepoint/schema/pull/469#discussion_r3620827524, https://github.com/observepoint/schema/pull/451#discussion_r2830140139
Raised by: vovsiichuk-op, robbimount, yurii-nesteruk-op
In docs: no

## Seen on one PR only

- No FK from a column to an enum lookup table, so new enum values are easy to add. Drop a `KEY` that only repeats a foreign key's index. 2 comments on #462. https://github.com/observepoint/schema/pull/462#discussion_r3420537102
- `CLAUDE.md` content: mark tag migrations and Cassandra as legacy, and say Claude must never run migrations against staging or prod. 4 comments on #429, now in `CLAUDE.md`. https://github.com/observepoint/schema/pull/429#discussion_r2474933120
- Data fixes to saved records (such as renamed column IDs in saved reports) usually go out without a migration. 1 comment on #487. https://github.com/observepoint/schema/pull/487#discussion_r3986444961
- A view that selects every column breaks when new columns are added to its table. 1 comment on #439. https://github.com/observepoint/schema/pull/439#discussion_r2676635704

## Lint rule candidates

- New `TIMESTAMP` column type in a migration (pattern 1).
- `ADD COLUMN ... NOT NULL` with no `DEFAULT` on an `ALTER TABLE` (pattern 1).
- Migration file name that does not match `V{YYYY}.{MM}.{DD}.{HH}.{MM}.{SS}__WORK-{id}_{description}.sql` (in `CLAUDE.md`, not checked today).
- `DEFINER=` with a hard-coded user instead of `CURRENT_USER` (in `CLAUDE.md`, not checked today).
- `ad_hoc/` script with `INSERT` or `UPDATE` and no `innodb_lock_wait_timeout` (pattern 3).

## Lint already catches

- No SQL linter or formatter runs in this repo. CodeRabbit comments on each PR, but it is a bot, not a gate.
- Broken migrations fail the `default_workflow` integration tests (TestContainers), which apply every migration to a fresh MySQL.
