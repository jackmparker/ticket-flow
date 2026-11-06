#!/usr/bin/env python3
"""Build the ticket's evidence PDF and Jira comment from one data file.

    python3 build-report.py <evidence dir>

Reads <dir>/report.json (format below) and the screenshots in <dir>/before/ and <dir>/after/.
Writes:
  <dir>/report.html                    self-contained page (images embedded)
  <dir>/<KEY>-verify-<date>.pdf         the one file attached to Jira
  <dir>/comment.json                   the short Jira comment, as ADF (Jira's comment format)

report.json:
{
  "key": "WORK-41070", "summary": "ticket summary", "date": "2026-11-05",
  "result": "ready" | "not ready", "result_note": "one line",
  "level": "full" | "light", "level_note": "why",
  "repo": "moonbeam", "base": "<sha>", "head": "<sha>", "qa_rounds": 2,
  "cases": [{"id": "1", "area": "...", "steps": "...", "expected": "...", "result": "pass" | "fail", "note": "..."}],
  "found_fixed": [{"what": "what broke", "fix": "what it does now", "source": "QA" | "Review"}],
  "review": [{"finding": "...", "action": "fixed" | "not changed" | "asked user", "note": "..."}],
  "still_open": ["..."],
  "pairs": [{"file": "01-gallery.png", "caption": "what changed"}],
  "api_pairs": [{"name": "...", "request": "...", "before": "...", "after": "..."}],
  "logs": "console errors and failed requests still seen, with why they are not from this change"
}
Leave a list empty when it has nothing. "pairs" is for UI changes, "api_pairs" for backend changes.
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

CSS = """
@page { size: Letter; margin: 14mm; }
body { font: 11px/1.45 -apple-system, Helvetica, Arial, sans-serif; color: #1d1d1f; }
h1 { font-size: 18px; margin: 0 0 2px; } h2 { font-size: 14px; margin: 18px 0 6px; border-bottom: 1px solid #ccc; padding-bottom: 3px; }
.sub { color: #555; margin-bottom: 10px; }
.result { display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: 600; }
.ready { background: #d8f5dd; color: #11632a; } .notready { background: #fde2e1; color: #9b1c1c; }
table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #ddd; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f3f3f3; } td.pass { color: #11632a; font-weight: 600; } td.fail { color: #9b1c1c; font-weight: 600; }
.pair { page-break-before: always; } .pair .cap { font-weight: 600; margin-bottom: 6px; }
.pair figure { margin: 0 0 10px; } .pair img { width: 100%; max-height: 108mm; object-fit: contain; border: 1px solid #ccc; }
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


def build_html(r, d):
    ready = r.get("result") == "ready"
    cases = r.get("cases", [])
    passed = sum(1 for c in cases if c.get("result") == "pass")
    parts = [
        f"<h1>{e(r['key'])}: {e(r.get('summary'))}</h1>",
        f'<div class="sub">Verified {e(r.get("date"))} · {e(r.get("repo"))} · base {e(r.get("base", "")[:10])}, head {e(r.get("head", "")[:10])}</div>',
        f'<span class="result {"ready" if ready else "notready"}">{"Ready" if ready else "Not ready"}</span> {e(r.get("result_note"))}',
        f"<p>{passed} of {len(cases)} test cases pass after {e(r.get('qa_rounds'))} QA round(s). Level: {e(r.get('level'))}, {e(r.get('level_note'))}.</p>",
        "<h2>Found and fixed</h2>", table(r.get("found_fixed", []), [("what", "What broke"), ("fix", "What it does now"), ("source", "Found by")]),
        "<h2>Still open</h2>", "<ul>" + "".join(f"<li>{e(x)}</li>" for x in r.get("still_open", [])) + "</ul>" if r.get("still_open") else "<p>None.</p>",
        "<h2>Test plan</h2>", table(cases, [("id", "#"), ("area", "Area"), ("steps", "Steps"), ("expected", "Expected"), ("result", "Result"), ("note", "Note")], cls_col="result"),
        "<h2>Review findings</h2>", table(r.get("review", []), [("finding", "Finding"), ("action", "Action"), ("note", "Note")]),
    ]
    pairs = r.get("pairs", [])
    if pairs:
        for i, p in enumerate(pairs, 1):
            # One pair per page, before above after, full width, so a whole-screen shot stays readable.
            parts.append(
                f'<div class="pair"><h2>Before and after {i} of {len(pairs)}</h2><div class="cap">{e(p.get("caption"))}</div>'
                f'<figure><figcaption>Before</figcaption>{img_tag(os.path.join(d, "before", p["file"]), "before")}</figure>'
                f'<figure><figcaption>After</figcaption>{img_tag(os.path.join(d, "after", p["file"]), "after")}</figure></div>')
    for p in r.get("api_pairs", []):
        parts.append(f'<div class="pair api"><div class="cap">{e(p.get("name"))}</div><pre>{e(p.get("request"))}</pre>'
                     f'<div class="imgs"><figure><figcaption>Before</figcaption><pre>{e(p.get("before"))}</pre></figure>'
                     f'<figure><figcaption>After</figcaption><pre>{e(p.get("after"))}</pre></figure></div></div>')
    if r.get("logs"):
        parts.append(f'<h2>Appendix: logs</h2><pre>{e(r["logs"])}</pre>')
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


def build_comment(r, pdf_name):
    cases = r.get("cases", [])
    passed = sum(1 for c in cases if c.get("result") == "pass")
    found = [f"{f['what']}. Now: {f['fix']}." if f.get("fix") else f["what"] for f in r.get("found_fixed", [])]
    more = len(found) - COMMENT_MAX_ITEMS
    if more > 0:
        found = found[:COMMENT_MAX_ITEMS] + [f"{more} more in the report."]
    content = [
        {"type": "paragraph", "content": [text(f"Verified before the PR. Full report: {pdf_name}")]},
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
    html_path = os.path.join(d, "report.html")
    open(html_path, "w").write(build_html(r, d))
    pdf_name = f"{r['key']}-verify-{r.get('date', 'undated')}.pdf"
    pdf_path = os.path.join(d, pdf_name)
    print_pdf(html_path, pdf_path)
    json.dump(build_comment(r, pdf_name), open(os.path.join(d, "comment.json"), "w"), indent=1)
    print(json.dumps({"pdf": pdf_path, "html": html_path, "comment": os.path.join(d, "comment.json"),
                      "pdf_kb": os.path.getsize(pdf_path) // 1024}))


if __name__ == "__main__":
    main()
