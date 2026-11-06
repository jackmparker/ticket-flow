#!/usr/bin/env python3
"""Build the ticket's evidence PDF and Jira comment from one data file.

    python3 build-report.py <evidence dir>

Reads <dir>/report.json (format below) and the screenshots in <dir>/before/ and <dir>/after/.
Writes:
  <dir>/report.html                    self-contained page (images embedded)
  <dir>/<KEY>-verify-<date>.pdf         the report attached to Jira (short: 1 to 3 pages)
  <dir>/<KEY>-verify-<date>-logs.txt    only when there is long text (logs, full API bodies); attached too
  <dir>/comment.json                   the short Jira comment, as ADF (Jira's comment format)

report.json:
{
  "key": "WORK-41070", "summary": "ticket summary", "date": "2026-11-05",
  "result": "ready" | "not ready", "result_note": "one line",
  "level": "full" | "light", "level_note": "why",
  "repo": "moonbeam", "base": "<sha>", "head": "<sha>", "qa_rounds": 2,
  "cases": [{"id": "1", "area": "...", "steps": "...", "expected": "...", "result": "pass" | "fail",
             "rounds": ["fail", "pass"], "added_in": 1, "note": "..."}],
    One row per case, with its FINAL result. "rounds" is its result in each QA round, in order;
    "added_in" is the round that added it (1 when it was in the plan). Never one table per round.
  "found_fixed": [{"what": "what broke", "fix": "what it does now", "source": "QA" | "Review"}],
  "review": [{"finding": "...", "action": "fixed" | "not changed" | "asked user", "note": "..."}],
  "still_open": ["..."],
  "pairs": [{"file": "01-gallery.png", "caption": "what changed"}],
  "api_pairs": [{"name": "...", "request": "GET /x", "before": "404 Not found", "after": "200, 3 items", "detail": "full bodies (optional)"}],
  "logs": "console errors and failed requests still seen, with why they are not from this change"
}
Leave a list empty when it has nothing. "pairs" is for screens that LOOK different, at most 3, each
cropped to the changed area. "api_pairs" is for backend changes: one short line each for before and
after; full bodies go in "detail". Long "logs" and every "detail" go to the separate text file.
Secrets must be removed before this runs: the PDF goes to Jira as is.
"""
import base64
import html
import json
import mimetypes
import os
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
COMMENT_MAX_ITEMS = 6
MAX_PAIRS = 3
SHORT_LOG_CHARS, SHORT_LOG_LINES = 400, 6  # longer logs go to the separate text file

CSS = """
@page { size: Letter; margin: 14mm; }
body { font: 11px/1.45 -apple-system, Helvetica, Arial, sans-serif; color: #1d1d1f; }
h1 { font-size: 18px; margin: 0 0 2px; } h2 { font-size: 14px; margin: 18px 0 6px; border-bottom: 1px solid #ccc; padding-bottom: 3px; }
.sub { color: #555; margin-bottom: 10px; }
.result { display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: 600; }
.ready { background: #d8f5dd; color: #11632a; } .notready { background: #fde2e1; color: #9b1c1c; }
table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #ddd; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f3f3f3; } td.pass { color: #11632a; font-weight: 600; } td.fail { color: #9b1c1c; font-weight: 600; }
.pair { page-break-inside: avoid; margin-bottom: 14px; } .pair .cap { font-weight: 600; margin-bottom: 6px; }
.pair figure { margin: 0 0 8px; } .pair img { max-width: 100%; max-height: 95mm; object-fit: contain; border: 1px solid #ccc; }
.pair figcaption { color: #555; font-size: 10px; font-weight: 600; margin-bottom: 2px; }
.api .imgs { display: flex; gap: 8px; } .api figure { flex: 1; }
pre { white-space: pre-wrap; background: #f6f6f6; padding: 6px; border: 1px solid #ddd; font-size: 10px; }
"""


def e(text):
    return html.escape(str(text or ""))


def img_tag(path, alt):
    if not os.path.exists(path):
        return f"<p><i>missing: {e(os.path.basename(path))}</i></p>"
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(open(path, "rb").read()).decode()
    return f'<img alt="{e(alt)}" src="data:{mime};base64,{data}">'


def table(rows, cols, cls_col=None):
    if not rows:
        return "<p>None.</p>"
    head = "".join(f"<th>{e(c[1])}</th>" for c in cols)
    body = ""
    for r in rows:
        cells = ""
        for key, _ in cols:
            cls = f' class="{e(r.get(key))}"' if key == cls_col else ""
            cells += f"<td{cls}>{e(r.get(key))}</td>"
        body += f"<tr>{cells}</tr>"
    return f"<table><tr>{head}</tr>{body}</table>"


def history(case):
    """'all rounds' when nothing changed, else 'R1 fail, R2 pass'; notes a case added in a later round."""
    rounds = case.get("rounds") or []
    start = int(case.get("added_in") or 1)
    if not rounds:
        return ""
    if all(x == rounds[-1] for x in rounds) and start == 1:
        return "all rounds"
    text = ", ".join(f"R{start + i} {x}" for i, x in enumerate(rounds))
    return f"added in R{start}: {text}" if start > 1 else text


def long_text(r):
    """The text that goes to the separate file: long logs and every API detail. Empty when none."""
    out = []
    logs = r.get("logs") or ""
    if len(logs) > SHORT_LOG_CHARS or logs.count("\n") >= SHORT_LOG_LINES:
        out.append("== Logs ==\n" + logs)
    for p in r.get("api_pairs", []):
        if p.get("detail"):
            out.append(f"== {p.get('name')} ==\n{p['detail']}")
    return "\n\n".join(out)


def build_html(r, d, logs_name):
    ready = r.get("result") == "ready"
    cases = r.get("cases", [])
    passed = sum(1 for c in cases if c.get("result") == "pass")
    review = r.get("review", [])
    kept = [x for x in review if x.get("action") != "fixed"]
    for c in cases:
        c["history"] = history(c)
    parts = [
        f"<h1>{e(r['key'])}: {e(r.get('summary'))}</h1>",
        f'<div class="sub">Verified {e(r.get("date"))} · {e(r.get("repo"))} · base {e(r.get("base", "")[:10])}, head {e(r.get("head", "")[:10])}</div>',
        f'<span class="result {"ready" if ready else "notready"}">{"Ready" if ready else "Not ready"}</span> {e(r.get("result_note"))}',
        f"<p>{passed} of {len(cases)} test cases pass after {e(r.get('qa_rounds'))} QA round(s). "
        f"Review: {len(review) - len(kept)} of {len(review)} findings fixed.</p>",
        "<h2>Found and fixed</h2>", table(r.get("found_fixed", []), [("what", "What broke"), ("fix", "What it does now"), ("source", "Found by")]),
        "<h2>Still open</h2>", "<ul>" + "".join(f"<li>{e(x)}</li>" for x in r.get("still_open", [])) + "</ul>" if r.get("still_open") else "<p>None.</p>",
    ]
    if kept:
        parts += ["<h2>Review findings not changed</h2>", table(kept, [("finding", "Finding"), ("note", "Why not")])]
    parts += [f"<h2>Test plan (final result of each case, {e(r.get('qa_rounds'))} QA round(s))</h2>",
              table(cases, [("id", "#"), ("area", "Area"), ("steps", "Steps"), ("expected", "Expected"), ("result", "Result"),
                            ("history", "Rounds"), ("note", "Note")], cls_col="result")]
    pairs = r.get("pairs", [])
    if pairs:
        parts.append('<h2 style="page-break-before: always">Before and after</h2>')
        for p in pairs:
            parts.append(
                f'<div class="pair"><div class="cap">{e(p.get("caption"))}</div>'
                f'<figure><figcaption>Before</figcaption>{img_tag(os.path.join(d, "before", p["file"]), "before")}</figure>'
                f'<figure><figcaption>After</figcaption>{img_tag(os.path.join(d, "after", p["file"]), "after")}</figure></div>')
    if r.get("api_pairs"):
        rows = [{"name": p.get("name"), "request": p.get("request"), "before": p.get("before"), "after": p.get("after")} for p in r["api_pairs"]]
        parts += ["<h2>Requests before and after</h2>", table(rows, [("name", "Case"), ("request", "Request"), ("before", "Before"), ("after", "After")])]
    logs = r.get("logs") or ""
    if logs_name:
        parts.append(f"<p><b>Logs and full responses:</b> attached separately as {e(logs_name)}.</p>")
    elif logs:
        parts.append(f"<p><b>Logs:</b> {e(logs)}</p>")
    return f'<!doctype html><html><head><meta charset="utf-8"><title>{e(r["key"])} verification</title><style>{CSS}</style></head><body>{"".join(parts)}</body></html>'


def print_pdf(html_path, pdf_path):
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}", f"file://{html_path}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=120)
    if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
        sys.exit(f"build-report: Chrome did not write {pdf_path}")


def text(t):
    return {"type": "text", "text": t}


def bullets(items):
    return {"type": "bulletList", "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [text(i)]}]} for i in items]}


def build_comment(r, pdf_name, logs_name):
    cases = r.get("cases", [])
    passed = sum(1 for c in cases if c.get("result") == "pass")
    found = [f"{f['what']}. Now: {f['fix']}." if f.get("fix") else f["what"] for f in r.get("found_fixed", [])]
    more = len(found) - COMMENT_MAX_ITEMS
    if more > 0:
        found = found[:COMMENT_MAX_ITEMS] + [f"{more} more in the report."]
    content = [
        {"type": "paragraph", "content": [text(f"Verified before the PR. Full report: {pdf_name}" + (f", logs: {logs_name}" if logs_name else ""))]},
        {"type": "paragraph", "content": [text(f"Result: {r.get('result')}. {passed} of {len(cases)} test cases pass after {r.get('qa_rounds')} QA round(s).")]},
        {"type": "paragraph", "content": [text("Found and fixed:")]},
        bullets(found) if found else {"type": "paragraph", "content": [text("Nothing.")]},
        {"type": "paragraph", "content": [text("Still open:")]},
        bullets(r["still_open"]) if r.get("still_open") else {"type": "paragraph", "content": [text("None.")]},
    ]
    return {"type": "doc", "version": 1, "content": content}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = os.path.abspath(sys.argv[1])
    r = json.load(open(os.path.join(d, "report.json")))
    if len(r.get("pairs", [])) > MAX_PAIRS:
        sys.exit(f"build-report: {len(r['pairs'])} screenshot pairs; keep the {MAX_PAIRS} that show the change best")
    stem = f"{r['key']}-verify-{r.get('date', 'undated')}"
    extra = long_text(r)
    logs_name = f"{stem}-logs.txt" if extra else None
    if logs_name:
        open(os.path.join(d, logs_name), "w").write(extra + "\n")
    html_path = os.path.join(d, "report.html")
    open(html_path, "w").write(build_html(r, d, logs_name))
    pdf_path = os.path.join(d, f"{stem}.pdf")
    print_pdf(html_path, pdf_path)
    json.dump(build_comment(r, os.path.basename(pdf_path), logs_name), open(os.path.join(d, "comment.json"), "w"), indent=1)
    attach = [pdf_path] + ([os.path.join(d, logs_name)] if logs_name else [])
    print(json.dumps({"attach": attach, "comment": os.path.join(d, "comment.json"), "html": html_path,
                      "pdf_kb": os.path.getsize(pdf_path) // 1024}))


if __name__ == "__main__":
    main()
