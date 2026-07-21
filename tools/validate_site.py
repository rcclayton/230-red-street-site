#!/usr/bin/env python3
"""Check the audition site for the failure modes that break it silently."""
import pathlib
import re
import sys
from urllib.parse import unquote

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
GS = ROOT / "apps-script" / "Code.gs"
CNAME = ROOT / "CNAME"
SIDES = ROOT / "Audition Sides - 230 Red Street.pdf"

errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def report():
    if errors:
        print("\n".join("FAIL: " + e for e in errors))
        sys.exit(1)


check(HTML.exists(), "index.html is missing")
check(GS.exists(), "apps-script/Code.gs is missing")
check(CNAME.exists(), "CNAME is missing")
check(SIDES.exists(), "Audition sides PDF is missing")
report()

html = HTML.read_text()
gs = GS.read_text()

# Placeholders and dead backend references must not ship.
for bad in ["EDIT_YOUR_EMAIL", "[EDIT", "YOURID", "PASTE_DEPLOYMENT_URL_HERE",
            "data-netlify", "netlify-honeypot", "FORMSPREE", "form-name"]:
    check(bad not in html, f"placeholder or dead backend reference in index.html: {bad}")

# The form and the backend must agree on field names, or submissions land in
# the wrong columns with no error anywhere. Scoped per-form: the page now has
# two independent forms writing to two different sheet tabs.
FORM_BODIES = dict(re.findall(r'<form[^>]*\bid="([^"]+)"[^>]*>(.*?)</form>', html, re.S))

# Not data columns: the honeypot is anti-spam, form_type is backend routing.
NON_FIELD_INPUTS = {"bot-field", "form_type"}


def form_fields_of(form_id):
    body = FORM_BODIES.get(form_id, "")
    names = set(re.findall(r'<(?:input|select|textarea)[^>]*\bname="([^"]+)"', body))
    return names - NON_FIELD_INPUTS


def gs_array(var_name):
    m = re.search(r"var %s = \[(.*?)\];" % var_name, gs, re.S)
    if m is None:
        errors.append(f"could not find the {var_name} array in apps-script/Code.gs")
        return None
    return set(re.findall(r"'([^']+)'", m.group(1)))


def check_form_matches(form_id, var_name):
    check(form_id in FORM_BODIES, f"<form id={form_id}> is missing from index.html")
    fields = form_fields_of(form_id)
    expected = gs_array(var_name)
    if expected is None:
        return fields
    check(
        fields == expected,
        f"{form_id} fields and Code.gs {var_name} disagree.\n"
        f"    only in the form:  {sorted(fields - expected)}\n"
        f"    only in Code.gs:   {sorted(expected - fields)}",
    )
    return fields


audition_fields = check_form_matches("auditionForm", "FIELDS")
crew_fields = check_form_matches("crewForm", "CREW_FIELDS")
form_fields = audition_fields | crew_fields

# Both forms must carry the honeypot, and only the crew form routes on form_type.
for form_id in ("auditionForm", "crewForm"):
    check('name="bot-field"' in FORM_BODIES.get(form_id, ""),
          f"the honeypot field is missing from {form_id}")
check('name="form_type"' in FORM_BODIES.get("crewForm", "") and
      'value="crew"' in FORM_BODIES.get("crewForm", ""),
      'the crew form must carry <input type="hidden" name="form_type" value="crew">')
check('name="form_type"' not in FORM_BODIES.get("auditionForm", ""),
      "the audition form must NOT carry form_type; it would reroute auditions")

check(
    re.search(r'ENDPOINT\s*=\s*"https://script\.google\.com/macros/s/[^"]+/exec"', html)
    is not None,
    "the Apps Script endpoint URL is not set in index.html",
)
# type="url" rejects links pasted without a scheme, which actors do constantly.
# The page uses text inputs plus its own normalizer instead.
check(re.search(r'<input[^>]*type="url"', html) is None,
      'type="url" rejects links without https://; use inputmode="url" + normalizeUrl')
check("function normalizeUrl" in html, "the URL normalizer was removed from index.html")
url_fields = re.findall(r'<input[^>]*inputmode="url"[^>]*\bname="([^"]+)"', html)
check(sorted(url_fields) == ["headshot", "links", "reel", "tape_link"],
      f"expected 4 link fields with inputmode=url, found: {sorted(url_fields)}")
check("application/x-www-form-urlencoded" in html,
      "the form must post form-encoded; JSON breaks on Apps Script CORS preflight")

for href in re.findall(r'href="([^"]+\.pdf)"', html):
    check((ROOT / unquote(href)).exists(), f"sides link points at a missing file: {href}")

check(CNAME.read_text().strip() == "230redstreet.com",
      "CNAME must contain exactly 230redstreet.com")
check("ryan@ryanclayton.media" in html, "contact email is missing from index.html")

# Case-insensitive: the source page contains "Minor / guardian status".
html_lower = html.lower()
for stale in ["early-august", "early august", "guardian", "minor"]:
    check(stale not in html_lower, f"stale copy in index.html: {stale}")

# Twist guardrail. The doppelganger reveal must never appear in public copy.
# See HANDOFF.md item 9 — this has been violated once already.
for spoiler in ["doppelganger", "bad corey", "unmask"]:
    check(spoiler not in html_lower, f"TWIST SPOILER in index.html: {spoiler}")

report()
print(f"PASS: {len(form_fields)} form fields, all checks green")
