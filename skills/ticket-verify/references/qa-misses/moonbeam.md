# moonbeam: bugs QA found after ticket-verify passed

**Grouping check.** Every agent that reads this file does this check. When 3 or more entries
under `## Not yet grouped` describe the same kind of bug, they are due for a group. Start a
background subagent that does the grouping in the ticket-flow clone at `~/ObservePoint/ticket-flow`
(`git pull --ff-only` first), not in the installed plugin copy, and go on with your own work. If you cannot start a subagent, say in your report that a
group is due. The subagent does this:

1. Write one group under `## Groups`: a numbered heading that says what to test, as an
   instruction, then the lines `Test:` (the general case that finds this kind of bug) and
   `Seen:` (the count and the ticket keys).
2. Remove the entries that the group now holds. Add a new entry to a group that already fits
   it: raise its `Seen:` count and add the key.
3. Commit on `main` with the message `QA misses: group <repo> entries` and push. If the pull or
   push fails, leave the change uncommitted and say so.

## Groups

None yet.

## Not yet grouped

- 2026-11-06 WORK-41060 (Tamera Eaton): bulk Reprocess Rules counted a failed rules request but did not list that audit in the progress dialog. Test: make the request for an audit that has runs answer 500, and check that the dialog lists that audit and the failure count.
- 2026-11-06 WORK-41060 (Tamera Eaton): a bulk reprocess whose request got a 500 retried without end, so the result dialog never came and the audit was never listed. Test: answer the bulk action request with a 500 (not only a 400) and wait for the result dialog; it must list the item within a minute.
