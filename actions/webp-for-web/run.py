#!/usr/bin/env python3
"""Write a web-ready WebP copy next to an image (ImageMagick).

The copy is "<name>.webp", or "<name> (2).webp" if that exists. The longest
edge is capped at WEBP_MAX_EDGE (default 1920 px, never enlarged) and quality
at WEBP_QUALITY (default 85). EXIF and other metadata are stripped, after the
orientation is applied.
"""
import os
import subprocess
from pathlib import Path

from strata_actions import context, require_tool

ctx = context()
magick = require_tool("magick")
edge = int(os.environ.get("WEBP_MAX_EDGE", "1920"))
quality = int(os.environ.get("WEBP_QUALITY", "85"))

source = Path(ctx.single)
target = source.with_suffix(".webp")
number = 2
while target.exists():
    target = source.with_name(f"{source.stem} ({number}).webp")
    number += 1

ctx.progress(0, 1, f"Converting {source.name}")
subprocess.run([magick, str(source), "-auto-orient", "-strip", "-resize", f"{edge}x{edge}>",
                "-quality", str(quality), str(target)], check=True)
ctx.output(str(target))
ctx.log(f"{source.name} → {target.name} ({target.stat().st_size // 1024} KiB)")
ctx.progress(1, 1, "Done")
