#!/usr/bin/env bash
# Prints what runs on a moonbeam staging environment now: the branch and commit of the newest
# successful deploy-<env> job in the last pipelines.
# Usage: env-branch.sh <env> [pipelines-to-scan]     (env: us2, us8, ua6, ...)
# Output: one JSON line {"env","branch","commit","deployed_at"}, or {"env","branch":null} when
# no successful deploy is in the scanned pipelines.
set -euo pipefail
env=$1; limit=${2:-60}
best='{"env":"'"$env"'","branch":null}'; best_at=""
while read -r wf branch sha; do
  at=$(aikit circleci workflows get "$wf" 2>/dev/null \
    | jq -r --arg j "deploy-$env" '.jobs[] | select(.name == $j and .status == "success") | .stopped_at' | head -1)
  if [ -n "$at" ] && [[ "$at" > "$best_at" ]]; then
    best_at=$at
    best=$(jq -cn --arg e "$env" --arg b "$branch" --arg c "$sha" --arg t "$at" '{env:$e,branch:$b,commit:$c,deployed_at:$t}')
  fi
done < <(aikit circleci pipelines list --project gh/observepoint/moonbeam --limit "$limit" \
  | jq -r '.items[] | .branch as $b | .commit_sha as $c | .workflows[]
           | select(.name == "BuildAndDeploy_Stage" and .status != "on_hold") | "\(.id) \($b) \($c)"')
echo "$best"
