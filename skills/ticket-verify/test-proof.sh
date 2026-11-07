#!/bin/bash
# Test proof helper: puts the base version of changed source files in place, then puts them back.
#   test-proof.sh swap <evidence-dir> <base-ref> <source-file>...   save, then write base versions
#   test-proof.sh restore <evidence-dir>                            put back, check the diff is the same
# Pass each file as its own argument (no quoted list): zsh does not split "$FILES" into words.
set -euo pipefail
cmd="${1:-}"; ev="${2:-}"
[ -n "$cmd" ] && [ -n "$ev" ] || { sed -n 2,5p "$0"; exit 2; }
proof="$ev/proof"; backup="$proof/backup"
case "$cmd" in
  swap)
    base="$3"; shift 3
    [ $# -gt 0 ] || { echo "test-proof: no source files given" >&2; exit 2; }
    [ ! -e "$proof/files.txt" ] || { echo "test-proof: a swap is already in place; run restore first" >&2; exit 1; }
    mkdir -p "$backup"
    git diff > "$proof/diff-before.patch"
    : > "$proof/files.txt"
    for f in "$@"; do
      mkdir -p "$backup/$(dirname "$f")"
      cp "$f" "$backup/$f"
      echo "$f" >> "$proof/files.txt"
      if git cat-file -e "$base:$f" 2>/dev/null; then
        git show "$base:$f" > "$f"; echo "base version: $f"
      else
        rm "$f"; echo "new file, removed: $f"
      fi
    done
    echo "swapped $# file(s). Run the specs, then: $0 restore $ev" ;;
  restore)
    [ -e "$proof/files.txt" ] || { echo "test-proof: nothing to restore" >&2; exit 1; }
    while IFS= read -r f; do cp "$backup/$f" "$f"; done < "$proof/files.txt"
    if git diff | cmp -s - "$proof/diff-before.patch"; then
      rm "$proof/files.txt"; echo "restored; git diff is the same as before the swap"
    else
      echo "test-proof: git diff differs from before the swap. Stop and report." >&2; exit 1
    fi ;;
  *) sed -n 2,5p "$0"; exit 2 ;;
esac
