# 230redstreet.com

Audition page for *230 Red Street*, a short horror film by Ryan Clayton.

Static page on GitHub Pages. The form posts to a Google Apps Script web app
that appends a row to the audition spreadsheet and emails a notification.

## Editing

- `index.html` — the whole page. No build step; edit and push.
- `apps-script/Code.gs` — reference copy of the backend. **Editing this file
  does nothing on its own.** Paste changes into the Apps Script editor and
  redeploy for them to take effect.
- `CNAME` — the custom domain. Do not delete; Pages drops the domain without it.

## Before pushing

```bash
python3 tools/validate_site.py
```

Catches placeholders, broken sides links, and form fields that have drifted out
of sync with the spreadsheet columns.

## Gotcha

The form posts `application/x-www-form-urlencoded`, not JSON. Apps Script web
apps do not answer CORS preflight requests, so switching to JSON breaks
submissions silently. The validator enforces this.
