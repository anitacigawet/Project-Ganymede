"""Report which Google account the saved NotebookLM cookies belong to.

Zero-RPC probe: fetches the NotebookLM home page HTML with the saved
cookies (same fetch the auth check already does) and extracts the
signed-in account email(s) Google embeds in the page. Used to diagnose
wrong-account sessions after a relogin captured the wrong profile
default (2026-07-22 incident: LIST_NOTEBOOKS returned 0 notebooks and
GET_NOTEBOOK returned PERMISSION_DENIED because the browser profile's
default account was not the Ganymede account).
"""

import asyncio
import re

import httpx

from notebooklm.auth import load_auth_from_storage

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


async def main() -> None:
    cookies = load_auth_from_storage()
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(
            "https://notebooklm.google.com/",
            headers={"Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items())},
        )
    html = resp.text
    print(f"final url: {resp.url}")
    print(f"status: {resp.status_code}, html length: {len(html)}")

    emails = sorted(set(EMAIL_RE.findall(html)))
    # Filter obvious non-account matches (schema/vendor addresses in JS bundles)
    emails = [
        e
        for e in emails
        if not e.lower().endswith((".png", ".jpg", ".svg", ".gstatic.com"))
        and "example" not in e.lower()
        and "schema" not in e.lower()
    ]
    print("account-looking emails embedded in page:")
    for e in emails:
        print(f"  {e}")
    if not emails:
        print("  (none found — page may be a login redirect)")

    m = re.search(r'"authuser"\s*:\s*"?(\d+)', html)
    if m:
        print(f"authuser index: {m.group(1)}")


if __name__ == "__main__":
    asyncio.run(main())
