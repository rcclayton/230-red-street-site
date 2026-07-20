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
# the wrong columns with no error anywhere.
form_fields = set(re.findall(r'<(?:input|select|textarea)[^>]*\bname="([^"]+)"', html))
form_fields.discard("bot-field")
m = re.search(r"var FIELDS = \[(.*?)\];", gs, re.S)
check(m is not None, "could not find the FIELDS array in apps-script/Code.gs")
if m:
    gs_fields = set(re.findall(r"'([^']+)'", m.group(1)))
    check(
        form_fields == gs_fields,
        "form fields and Code.gs FIELDS disagree.\n"
        f"    only in the form:  {sorted(form_fields - gs_fields)}\n"
        f"    only in Code.gs:   {sorted(gs_fields - form_fields)}",
    )

check(
    re.search(r'ENDPOINT\s*=\s*"https://script\.google\.com/macros/s/[^"]+/exec"', html)
    is not None,
    "the Apps Script endpoint URL is not set in index.html",
)
check('name="bot-field"' in html, "the honeypot field was removed from index.html")
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

report()
print(f"PASS: {len(form_fields)} form fields, all checks green")
