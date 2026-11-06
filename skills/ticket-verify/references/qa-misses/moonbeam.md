# moonbeam: bugs QA found after ticket-verify passed

- 2026-11-06 WORK-41060 (Tamera Eaton): bulk Reprocess Rules counted a failed rules request but did not list that audit in the progress dialog. Test: make the request for an audit that has runs answer 500, and check that the dialog lists that audit and the failure count.
