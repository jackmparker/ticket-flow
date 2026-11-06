#!/usr/bin/env bash
# Waits until QA moves every ticket to Ready for Merge. Checks Jira once a minute.
# Usage: watch-ready.sh <max-seconds> <KEY> [<KEY> ...]
# Prints one JSON line and exits:
#   0  {"result":"ready",...}    every ticket is in Ready for Merge or Accepted
#   3  {"result":"stopped",...}  a ticket is in a column that is not part of the wait (for example sent back)
#   4  {"result":"timeout",...}  max-seconds passed; start the watch again
# A failed Jira call is retried on the next check. It never ends the watch by itself.
set -u
max=$1; shift
waiting='^(Ready for Prod|On Prod)$'
done_re='^(Ready for Merge|Accepted)$'
end=$(( $(date +%s) + max ))
statuses=""
while :; do
  statuses=""; all_done=1; stopped=0; failed=0
  for key in "$@"; do
    s=$(aikit jira issues get "$key" --fields status 2>/dev/null | jq -r '.status.name // empty' 2>/dev/null)
    if [ -z "$s" ]; then failed=1; all_done=0; continue; fi
    statuses="$statuses${statuses:+,}\"$key\":\"$s\""
    if [[ "$s" =~ $done_re ]]; then :; elif [[ "$s" =~ $waiting ]]; then all_done=0; else all_done=0; stopped=1; fi
  done
  if [ "$failed" = 0 ] && [ "$stopped" = 1 ]; then echo "{\"result\":\"stopped\",\"statuses\":{$statuses}}"; exit 3; fi
  if [ "$failed" = 0 ] && [ "$all_done" = 1 ]; then echo "{\"result\":\"ready\",\"statuses\":{$statuses}}"; exit 0; fi
  if [ "$(date +%s)" -ge "$end" ]; then echo "{\"result\":\"timeout\",\"statuses\":{$statuses}}"; exit 4; fi
  sleep 60
done
