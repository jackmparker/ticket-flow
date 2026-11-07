# Accessibility scan for one page, with axe-core (a standard accessibility checker).
# Run inside browser-harness, on the page to check:
#   browser-harness -c "claim_tab(); exec(open('<this file>').read()); print(a11y_scan())"
# Prints JSON: one entry per rule that fails, with its impact, how many elements fail and up to
# 3 element selectors. Compare the "before" and "after" results: a rule id that is new, or has
# more elements, after the change is a new problem.
import json, os, urllib.request

AXE_VERSION = "4.10.2"
AXE_CACHE = os.path.expanduser(f"~/.cache/ticket-verify/axe-{AXE_VERSION}.min.js")


def _axe_source():
    if not os.path.exists(AXE_CACHE):
        os.makedirs(os.path.dirname(AXE_CACHE), exist_ok=True)
        url = f"https://cdnjs.cloudflare.com/ajax/libs/axe-core/{AXE_VERSION}/axe.min.js"
        urllib.request.urlretrieve(url, AXE_CACHE)
    return open(AXE_CACHE).read()


def a11y_scan(selector="document"):
    """Runs axe on the page (or on one element, for example selector="'app-report-card'")."""
    if not js("typeof window.axe !== 'undefined'"):
        js(_axe_source() + "; true")
    result = js(
        f"""return axe.run({selector if selector == 'document' else 'document.querySelector(' + selector + ')'},
              {{runOnly: {{type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']}}}})
          .then(r => JSON.stringify(r.violations.map(v => ({{
            id: v.id, impact: v.impact, count: v.nodes.length,
            targets: v.nodes.slice(0, 3).map(n => n.target.join(' '))}}))))""")
    return json.dumps(json.loads(result), indent=1)
