#!/usr/bin/env python3
"""Strata file provider: a submenu of SFTP (or any GVfs) bookmarks.

Reads ~/.config/strata-extras/sftp-bookmarks.tsv on every menu request, one
bookmark per line:

    label<TAB>uri[<TAB>group]

Lines starting with "#" are comments. Bookmarks with a group go into a nested
submenu of that name. Choosing a bookmark opens the location in a new Strata
window (Strata mounts it through GVfs and asks for credentials if needed).

Protocol: Strata external file providers, protocol 1 (docs/file-providers.md).
Standard library only.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
BOOKMARKS = CONFIG / "strata-extras" / "sftp-bookmarks.tsv"
# Submenu label: "--menu LABEL" in provider.json's command (Strata passes no environment of its own).
MENU_LABEL = (sys.argv[sys.argv.index("--menu") + 1] if "--menu" in sys.argv[:-1]
              else os.environ.get("SFTP_BOOKMARKS_MENU", "Open bookmark"))
SCHEMES = ("sftp://", "ftp://", "ftps://", "smb://", "dav://", "davs://", "afp://", "nfs://", "file://")
MAX_NODES = 64                      # Strata's limit for the whole tree
MAX_LABEL = 128                     # bytes


def clean(label):
    label = " ".join(label.split())
    while len(label.encode()) > MAX_LABEL:
        label = label[:-1]
    return label


def load():
    """Return [(label, uri, group)] from the bookmarks file; bad lines are skipped."""
    try:
        text = BOOKMARKS.read_text(encoding="utf-8")
    except OSError:
        return []
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        label, uri = clean(parts[0]), parts[1].strip()
        group = clean(parts[2]) if len(parts) > 2 and parts[2].strip() else ""
        if label and uri.startswith(SCHEMES):
            rows.append((label, uri, group))
    return rows


def leaf_id(uri):
    return "b-" + hashlib.sha256(uri.encode()).hexdigest()[:16]


def menu_tree(rows):
    """One root branch; grouped bookmarks get a nested branch. Respects the 64-node limit."""
    children, groups, count = [], {}, 1
    for label, uri, group in rows:
        if count >= MAX_NODES:
            break
        leaf = {"id": leaf_id(uri), "label": label, "context": leaf_id(uri)}
        if group:
            if group not in groups:
                if count + 2 > MAX_NODES:
                    break
                groups[group] = {"id": "g-" + hashlib.sha256(group.encode()).hexdigest()[:12],
                                 "label": group, "children": []}
                children.append(groups[group])
                count += 1
            groups[group]["children"].append(leaf)
        else:
            children.append(leaf)
        count += 1
    return [{"id": "bookmarks", "label": MENU_LABEL, "children": children}] if children else []


def open_location(uri):
    strata = os.environ.get("STRATA_BIN") or shutil.which("strata") or "/usr/bin/strata"
    subprocess.Popen([strata, uri], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True, cwd=str(Path.home()))


def handle(request):
    reply = {"version": 1, "id": request.get("id", 0)}
    if request.get("version") != 1 or type(request.get("id")) is not int:
        return {**reply, "error": "invalid-request", "message": "Invalid provider request."}
    method = request.get("method")
    if method == "query":
        return {**reply, "decorations": [], "revision": 0}
    if method == "menu":
        return {**reply, "actions": menu_tree(load()), "revision": 0}
    if method == "activate":
        # Re-read the file: the chosen id must still name the same location.
        wanted = request.get("action")
        match = next((uri for _, uri, _ in load() if leaf_id(uri) == wanted == request.get("context")), None)
        if not match:
            return {**reply, "message": "That bookmark changed. Reopen the menu.", "outcome": {"status": "rejected"}}
        try:
            open_location(match)
        except OSError as error:
            return {**reply, "message": f"Could not start Strata: {error}", "outcome": {"status": "rejected"}}
        return {**reply, "message": "Opening the bookmark in a new window.", "outcome": {"status": "accepted"},
                "feedback": "notice"}
    return {**reply, "error": "unsupported-method", "message": "Unsupported provider method."}


def main():
    for frame in sys.stdin.buffer:
        try:
            request = json.loads(frame)
            if not isinstance(request, dict):
                raise ValueError
        except ValueError:
            return
        sys.stdout.write(json.dumps(handle(request), ensure_ascii=True) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
