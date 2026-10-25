#!/usr/bin/env python3
"""Copy files and folders into a Nextcloud-synced folder.

The destination comes from ~/.config/strata-extras/nextcloud.toml:

    folder = "~/Nextcloud/Inbox"

and defaults to ~/Nextcloud/Inbox. Existing names are never overwritten:
"report.pdf" becomes "report (2).pdf". The Nextcloud client uploads the copies.
"""
import os
import shutil
import tomllib
from pathlib import Path

from strata_actions import context

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "strata-extras" / "nextcloud.toml"


def destination():
    folder = "~/Nextcloud/Inbox"
    if CONFIG.is_file():
        folder = tomllib.loads(CONFIG.read_text()).get("folder", folder)
    target = Path(folder).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    return target


def free_name(target, name):
    candidate = target / name
    stem, suffix = Path(name).stem, Path(name).suffix
    number = 2
    while candidate.exists():
        candidate = target / f"{stem} ({number}){suffix}"
        number += 1
    return candidate


ctx = context()
target = destination()
for index, source in enumerate(map(Path, ctx.paths), start=1):
    ctx.progress(index - 1, ctx.count, f"Copying {source.name}")
    copy = free_name(target, source.name)
    if source.is_dir():
        shutil.copytree(source, copy, symlinks=True)
    else:
        shutil.copy2(source, copy)
    ctx.output(str(copy))
ctx.progress(ctx.count, ctx.count, f"Copied to {target}")
