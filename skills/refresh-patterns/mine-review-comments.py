#!/usr/bin/env python3
"""Fetch the human review comments on a repo's closed pull requests, for the review-patterns files.

    python3 mine-review-comments.py <repo> --since 2026-08-01 --out <dir> [--owner observepoint]

Writes <dir>/<repo>.json: one object per comment (pr, title, pr_author, kind, user, body, url, path,
hunk, created), and prints a summary: PRs read, comments kept, PRs with comments, reviewers, authors.

Kept: comments created on or after --since, on PRs that are merged or closed, by someone other than
the PR author. Dropped: bots, empty text, and approval-only or praise-only text. Grouping the kept
comments into patterns is the agent's job (see SKILL.md); this script only fetches and filters.

Needs `gh`, authenticated. Uses the GraphQL API, about one call per 20 PRs.
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

QUERY = """query($owner:String!,$name:String!,$cursor:String){
 repository(owner:$owner,name:$name){
  pullRequests(first:20, after:$cursor, orderBy:{field:UPDATED_AT,direction:DESC}){
   pageInfo{hasNextPage endCursor}
   nodes{ number title url state updatedAt author{login}
    comments(first:100){nodes{author{login} body createdAt url}}
    reviews(first:50){nodes{author{login} state body url createdAt
      comments(first:100){nodes{author{login} body path diffHunk url createdAt}}}}
   }}}}"""

BOT = re.compile(r"(\[bot\]$|^coderabbit|^github-actions|^netlify|^vercel|^codecov|^sonar|^copilot|^claude$|^cursor|^chromatic)", re.I)
PRAISE = re.compile(r"^\s*(lgtm|looks good( to me)?|approved?|nice( work| job)?|great( work| job)?|thanks!?|thank you!?|ship it|:shipit:|👍|🚀|✅)[\s.!]*$", re.I)


def fetch(owner, repo, since):
    """Closed or merged PRs updated on or after `since`, newest first."""
    prs, cursor = [], None
    while True:
        args = ["gh", "api", "graphql", "-f", "query=" + QUERY, "-F", f"owner={owner}", "-F", f"name={repo}"]
        if cursor:
            args += ["-F", f"cursor={cursor}"]
        page = json.loads(subprocess.check_output(args))["data"]["repository"]["pullRequests"]
        for pr in page["nodes"]:
            if pr["updatedAt"] < since:
                return prs  # ordered by update time, so every later PR is older too
            if pr["state"] != "OPEN":
                prs.append(pr)
        if not page["pageInfo"]["hasNextPage"]:
            return prs
        cursor = page["pageInfo"]["endCursor"]


def human_comments(prs, since):
    out = []
    for pr in prs:
        author = (pr["author"] or {}).get("login", "")

        def add(kind, c):
            user = (c["author"] or {}).get("login", "ghost")
            body = (c.get("body") or "").strip()
            if c.get("createdAt", "") < since or BOT.search(user) or user == author or not body or PRAISE.match(body):
                return
            out.append({
                "pr": pr["number"], "title": pr["title"], "pr_author": author, "kind": kind, "user": user,
                "body": body, "url": c.get("url"), "path": c.get("path"), "hunk": (c.get("diffHunk") or "")[-400:],
                "created": c.get("createdAt"),
            })

        for c in pr["comments"]["nodes"]:
            add("conversation", c)
        for review in pr["reviews"]["nodes"]:
            add("review", review)
            for c in review["comments"]["nodes"]:
                add("inline", c)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo")
    ap.add_argument("--since", required=True, help="YYYY-MM-DD; comments created on or after this date")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--owner", default="observepoint")
    a = ap.parse_args()

    prs = fetch(a.owner, a.repo, a.since)
    comments = human_comments(prs, a.since)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"{a.repo}.json")
    with open(path, "w") as f:
        json.dump(comments, f, indent=1)

    print(f"{a.owner}/{a.repo} since {a.since}: {len(prs)} closed or merged PRs read, "
          f"{len(comments)} human comments kept on {len({c['pr'] for c in comments})} PRs -> {path}")
    print("reviewers:", collections.Counter(c["user"] for c in comments).most_common(10))
    print("authors:", collections.Counter(p["author"]["login"] for p in prs if p["author"]).most_common(10))


if __name__ == "__main__":
    sys.exit(main())
