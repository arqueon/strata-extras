#!/usr/bin/env bash
# Install strata-extras actions into Strata's configuration.
#
#   ./install.sh                 install every action that is not installed yet
#   ./install.sh send-to-zotero  install only the named actions
#   ./install.sh --force ...     replace actions that are already installed
#   ./install.sh --list          show the available actions
#
# Actions are copied (not linked) into ~/.config/strata/actions/<id>/, with
# private permissions, because Strata only trusts files owned by you.
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/actions"
dest="${XDG_CONFIG_HOME:-$HOME/.config}/strata/actions"
force=0
wanted=()

for arg in "$@"; do
    case "$arg" in
        --force) force=1 ;;
        --list) for d in "$src"/*/; do
                    id="$(basename "$d")"
                    printf '%-22s %s\n' "$id" "$(sed -n 's/^name = "\(.*\)"/\1/p' "$d/action.toml")"
                done; exit 0 ;;
        -h|--help) sed -n '2,10s/^# \{0,1\}//p' "$0"; exit 0 ;;
        *) wanted+=("$arg") ;;
    esac
done
[[ ${#wanted[@]} -gt 0 ]] || for d in "$src"/*/; do wanted+=("$(basename "$d")"); done

mkdir -p "$dest"
chmod 700 "$dest"
for id in "${wanted[@]}"; do
    if [[ ! -f "$src/$id/action.toml" ]]; then
        echo "unknown action: $id (see --list)" >&2
        exit 1
    fi
    if [[ -e "$dest/$id" && $force -eq 0 ]]; then
        echo "skipped $id: already installed (use --force to replace it)"
        continue
    fi
    rm -rf -- "${dest:?}/$id"
    cp -r -- "$src/$id" "$dest/$id"
    chmod 700 "$dest/$id"
    chmod 600 "$dest/$id"/*
    echo "installed $id"
done
echo "Open Strata → Settings → Actions to review and enable them."
