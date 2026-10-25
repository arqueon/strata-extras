#!/usr/bin/env python3
"""Upload one photo or video to Immich.

Reads IMMICH_URL and IMMICH_API_KEY from ~/.config/strata-extras/immich.env
(KEY=value lines; keep it mode 600). Use an API key that only has the
"asset.upload" permission. IMMICH_URL is the server root, e.g.
http://immich.lan:2283 (the action adds /api).
"""
import json
import mimetypes
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from strata_actions import context

ENV = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "strata-extras" / "immich.env"


def settings():
    values = {}
    if ENV.is_file():
        if ENV.stat().st_mode & 0o077:
            raise SystemExit(f"{ENV} must not be readable by others (chmod 600).")
        for line in ENV.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    url = os.environ.get("IMMICH_URL") or values.get("IMMICH_URL")
    key = os.environ.get("IMMICH_API_KEY") or values.get("IMMICH_API_KEY")
    if not url or not key:
        raise SystemExit(f"Set IMMICH_URL and IMMICH_API_KEY in {ENV}.")
    return url.rstrip("/").removesuffix("/api") + "/api", key


def iso(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


ctx = context()
api, key = settings()
path = Path(ctx.single)
info = path.stat()
fields = {
    "deviceAssetId": f"{path.name}-{info.st_size}-{int(info.st_mtime)}",
    "deviceId": "strata",
    "fileCreatedAt": iso(getattr(info, "st_birthtime", info.st_mtime)),
    "fileModifiedAt": iso(info.st_mtime),
}
boundary = uuid.uuid4().hex
body = b"".join(
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
    for name, value in fields.items()
)
mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"assetData\"; filename=\"{path.name}\"\r\n"
         f"Content-Type: {mime}\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()

ctx.progress(0, 1, f"Uploading {path.name}")
request = urllib.request.Request(api + "/assets", data=body, method="POST", headers={
    "x-api-key": key, "Accept": "application/json",
    "Content-Type": f"multipart/form-data; boundary={boundary}",
})
try:
    with urllib.request.urlopen(request, timeout=600) as response:
        reply = json.loads(response.read() or b"{}")
except urllib.error.HTTPError as error:
    raise SystemExit(f"Immich refused {path.name}: HTTP {error.code} {error.read()[:200].decode(errors='replace')}")
ctx.log(f"{path.name}: {reply.get('status', 'uploaded')} (asset {reply.get('id', '?')})")
ctx.progress(1, 1, "Done")
