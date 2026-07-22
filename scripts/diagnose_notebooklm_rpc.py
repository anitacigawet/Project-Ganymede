"""Diagnose GET_NOTEBOOK null-result against the live account.

Mirrors upstream notebooklm-py scripts/diagnose_get_notebook.py, adapted to
the vendored 0.3.4 API surface. Makes exactly 3 batchexecute calls with 8s+
spacing (respecting the project's cooldown discipline):

  1. LIST_NOTEBOOKS  -> which notebooks can this session actually see?
  2. GET_NOTEBOOK (nested #1546 shape) -> raw response captured
  3. GET_NOTEBOOK (old flat shape)     -> raw response captured

Prints raw response head + which rpc ids came back so we can tell apart:
  - wrong account / notebook invisible (list lacks the Engine id)
  - response-envelope drift (data present but decoder misses it)
  - genuine server-side rejection (explicit error frames)
"""

import asyncio
import json
import sys
from urllib.parse import urlencode

import httpx

from notebooklm.auth import AuthTokens, fetch_tokens, load_auth_from_storage
from notebooklm.rpc import (
    BATCHEXECUTE_URL,
    RPCMethod,
    build_request_body,
    build_template_block,
    encode_rpc_request,
    parse_chunked_response,
    strip_anti_xssi,
)

ENGINE_ID = "0a7d2672-009e-4995-9477-68c9b2fd9e54"
AUDITOR_ID = "756e3683-f651-4381-b560-b13711b84ce6"


async def rpc_raw(client, auth, method, params, source_path="/"):
    query = urlencode(
        {
            "rpcids": method.value,
            "source-path": source_path,
            "f.sid": auth.session_id,
            "rt": "c",
        }
    )
    url = f"{BATCHEXECUTE_URL}?{query}"
    body = build_request_body(encode_rpc_request(method, params), auth.csrf_token)
    cookie_header = "; ".join(f"{k}={v}" for k, v in auth.cookies.items())
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie_header,
    }
    resp = await client.post(url, content=body, headers=headers)
    resp.raise_for_status()
    return resp.text


def show(label, raw):
    print(f"\n===== {label} =====")
    print(f"raw length: {len(raw)}")
    stripped = strip_anti_xssi(raw)
    try:
        chunks = parse_chunked_response(stripped)
    except Exception as e:  # pragma: no cover - diagnostic only
        print(f"parse_chunked_response failed: {e}")
        print("head 400:", raw[:400].replace("\n", "\\n"))
        return
    print(f"chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        for item in chunk if isinstance(chunk, list) else []:
            if isinstance(item, list) and item and item[0] == "wrb.fr":
                rpc_id = item[1] if len(item) > 1 else "?"
                payload = item[2] if len(item) > 2 else None
                status = item[5] if len(item) > 5 else None
                p_desc = (
                    f"str[{len(payload)}]" if isinstance(payload, str) else repr(payload)[:120]
                )
                print(f"  chunk{i}: wrb.fr id={rpc_id} payload={p_desc} slot5={repr(status)[:200]}")
            elif isinstance(item, list) and item and item[0] in ("di", "af.httprm", "e"):
                print(f"  chunk{i}: frame {item[:4]!r}")


async def main():
    cookies = load_auth_from_storage()
    csrf, sid = await fetch_tokens(cookies)
    auth = AuthTokens(cookies=cookies, csrf_token=csrf, session_id=sid)
    print(f"auth ok: csrf={'yes' if csrf else 'NO'} sid={'yes' if sid else 'NO'}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        raw = await rpc_raw(client, auth, RPCMethod.LIST_NOTEBOOKS, [None, 1, None, [2]])
        show("LIST_NOTEBOOKS", raw)
        # Decode the list to enumerate visible notebook ids
        stripped = strip_anti_xssi(raw)
        chunks = parse_chunked_response(stripped)
        ids = []
        for chunk in chunks:
            for item in chunk if isinstance(chunk, list) else []:
                if isinstance(item, list) and item and item[0] == "wrb.fr" and len(item) > 2:
                    if isinstance(item[2], str):
                        try:
                            data = json.loads(item[2])
                        except json.JSONDecodeError:
                            continue
                        rows = data[0] if data and isinstance(data, list) else []
                        for row in rows if isinstance(rows, list) else []:
                            if isinstance(row, list):
                                title = row[0] if row and isinstance(row[0], str) else "?"
                                nid = None
                                for cell in row:
                                    if isinstance(cell, str) and len(cell) == 36 and cell.count("-") == 4:
                                        nid = cell
                                        break
                                ids.append((nid, title))
        print(f"\nvisible notebooks ({len(ids)}):")
        for nid, title in ids:
            marker = ""
            if nid == ENGINE_ID:
                marker = "  <== ENGINE"
            elif nid == AUDITOR_ID:
                marker = "  <== MIRROR AUDITOR"
            print(f"  {nid}  {title[:60]!r}{marker}")
        engine_visible = any(nid == ENGINE_ID for nid, _ in ids)
        print(f"\nENGINE visible: {engine_visible}; AUDITOR visible: {any(n == AUDITOR_ID for n, _ in ids)}")

        await asyncio.sleep(9)
        raw = await rpc_raw(
            client,
            auth,
            RPCMethod.GET_NOTEBOOK,
            [ENGINE_ID, None, build_template_block(), None, 0],
            source_path=f"/notebook/{ENGINE_ID}",
        )
        show("GET_NOTEBOOK nested (#1546) shape", raw)

        await asyncio.sleep(9)
        raw = await rpc_raw(
            client,
            auth,
            RPCMethod.GET_NOTEBOOK,
            [ENGINE_ID, None, [2], None, 0],
            source_path=f"/notebook/{ENGINE_ID}",
        )
        show("GET_NOTEBOOK old flat shape", raw)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
