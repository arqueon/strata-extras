#!/usr/bin/env bash
# Register the sftp-bookmarks provider with Strata.
#
#   ./install.sh                 menu label "Open bookmark"
#   ./install.sh --menu Servers  choose the submenu label
#
# Strata requires real files (no symlinks) that are not group/world writable,
# so the provider is copied and provider.json is written with absolute paths.
# Your bookmarks stay in ~/.config/strata-extras/sftp-bookmarks.tsv.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
config="${XDG_CONFIG_HOME:-$HOME/.config}"
dest="$config/strata/providers/sftp-bookmarks"
menu="Open bookmark"
[[ "${1:-}" == "--menu" && -n "${2:-}" ]] && menu="$2"

python="$(command -v python3)"
mkdir -p "$dest"
chmod 700 "$dest"
install -m 700 "$here/provider.py" "$dest/provider.py"
"$python" - "$dest" "$python" "$menu" <<'PY'
import json, sys
dest, python, menu = sys.argv[1:]
manifest = {"version": 1, "id": "sftp-bookmarks", "name": "Bookmarks", "category": "other",
            "command": [python, f"{dest}/provider.py", "--menu", menu]}
with open(f"{dest}/provider.json", "w") as handle:
    json.dump(manifest, handle, indent=2)
PY
chmod 600 "$dest/provider.json"

bookmarks="$config/strata-extras/sftp-bookmarks.tsv"
if [[ ! -e "$bookmarks" ]]; then
    mkdir -p "$(dirname "$bookmarks")"
    install -m 600 "$here/sftp-bookmarks.example.tsv" "$bookmarks"
    echo "created $bookmarks from the example: edit it with your hosts"
fi
echo "installed the sftp-bookmarks provider (menu: $menu)"
echo "In Strata: Settings → Integrations → Refresh, or restart Strata."
