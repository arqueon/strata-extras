#!/usr/bin/env python3
"""Send a PDF or EPUB to the running Zotero desktop app.

Uses Zotero's local connector (the same endpoint the browser connector uses):
the file is saved as a standalone attachment in the library or collection that
is currently selected in Zotero, and Zotero then retrieves its metadata and
creates the parent item. Zotero must be running.
"""
import json
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from strata_actions import context

CONNECTOR = os.environ.get("ZOTERO_CONNECTOR", "http://127.0.0.1:23119")
TYPES = {".pdf": "application/pdf", ".epub": "application/epub+zip"}


def post(path, data, headers, timeout=120):
    request = urllib.request.Request(CONNECTOR + path, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        return response.status, json.loads(body) if body else None


ctx = context()
path = Path(ctx.single)
try:
    urllib.request.urlopen(CONNECTOR + "/connector/ping", timeout=5).read()
except OSError:
    raise SystemExit("Zotero is not running (no answer on its local connector).")

session = uuid.uuid4().hex
metadata = {"sessionID": session, "title": path.stem, "url": path.as_uri()}
ctx.progress(0, 2, f"Saving {path.name} in Zotero")
status, reply = post("/connector/saveStandaloneAttachment", path.read_bytes(), {
    "Content-Type": TYPES.get(path.suffix.lower(), "application/octet-stream"),
    "X-Metadata": json.dumps(metadata),
})
if status != 201:
    raise SystemExit(f"Zotero did not save the file (HTTP {status}); is the selected library editable?")

if reply and reply.get("canRecognize"):
    ctx.progress(1, 2, "Retrieving metadata")
    try:
        status, item = post("/connector/getRecognizedItem", json.dumps({"sessionID": session}).encode(),
                            {"Content-Type": "application/json"}, timeout=180)
        if status == 200 and item:
            ctx.log(f"{path.name} → {item.get('itemType')}: {item.get('title')}")
        else:
            ctx.log(f"{path.name} saved; Zotero found no metadata for it.")
    except urllib.error.URLError as error:
        ctx.log(f"{path.name} saved; metadata lookup did not finish ({error}).")
else:
    ctx.log(f"{path.name} saved as a standalone attachment.")
ctx.progress(2, 2, "Done")
