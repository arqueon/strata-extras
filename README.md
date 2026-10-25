# strata-extras

Custom actions and a dynamic theme for [Strata](https://github.com/lgse/strata), the keyboard-first GTK 4 file manager.

Everything here uses Strata's documented extension points: [custom actions](https://github.com/lgse/strata/blob/main/docs/custom-actions.md) for the context menu and [custom theme files](https://github.com/lgse/strata/blob/main/docs/themes.md) that Strata reloads live.

## Actions

| Action | Shows up for | What it does |
| --- | --- | --- |
| **Send to Zotero** | PDF, EPUB | Saves the file in the library or collection currently selected in the Zotero desktop app, then lets Zotero retrieve the metadata and create the parent item. |
| **Upload to Immich** | images, videos | Uploads each file to an [Immich](https://immich.app) server. Immich detects duplicates. |
| **Copy to Nextcloud** | files, folders | Copies the selection into a folder that the Nextcloud desktop client keeps in sync (default `~/Nextcloud/Inbox`). Never overwrites: `report.pdf` becomes `report (2).pdf`. |
| **WebP for the web** | images | Writes a WebP copy next to each image: longest edge at most 1920 px, quality 85, metadata stripped. |
| **Compare with Meld** | 2–3 files or folders | Opens the selection in [Meld](https://meldmerge.org). |
| **Open in Sublime Text** | files | Opens the selection in Sublime Text. |

The Python actions use only the standard library and Strata's bundled `strata_actions` helper, so there is nothing to `pip install`. They report progress and created files to Strata's Jobs dashboard.

### Install

```sh
git clone https://github.com/arqueon/strata-extras.git
cd strata-extras
./install.sh --list          # what is available
./install.sh                 # install everything not installed yet
./install.sh send-to-zotero  # or only some actions
```

Then review them in **Strata → Settings → Actions**. Actions run with your permissions: read the scripts before enabling them.

### Configuration

- **Send to Zotero** needs Zotero running (it talks to Zotero's local connector on `127.0.0.1:23119`). Select the target collection in Zotero first. Set `ZOTERO_CONNECTOR` to use another address.
- **Upload to Immich** reads `~/.config/strata-extras/immich.env`, which must be mode `600`:

  ```sh
  IMMICH_URL=http://immich.lan:2283
  IMMICH_API_KEY=...
  ```

  Create a dedicated API key in Immich (**Account settings → API keys**) with only the `asset.upload` permission.
- **Copy to Nextcloud** reads `~/.config/strata-extras/nextcloud.toml`:

  ```toml
  folder = "~/Nextcloud/Inbox"
  ```
- **WebP for the web** needs ImageMagick (`magick`). `WEBP_MAX_EDGE` and `WEBP_QUALITY` change the defaults.

## Matugen theme

[`themes/matugen/strata-theme.toml`](themes/matugen/strata-theme.toml) is a [matugen](https://github.com/InioX/matugen) template that maps the Material You palette of your wallpaper to Strata's nine interface colors and five code-preview colors. Strata watches its themes folder, so open windows recolor as soon as matugen rewrites the file.

1. Copy the template to `~/.config/matugen/templates/strata-theme.toml`.
2. Add it to `~/.config/matugen/config.toml`:

   ```toml
   [templates.strata]
   input_path = '~/.config/matugen/templates/strata-theme.toml'
   output_path = '~/.config/strata/themes/matugen.toml'
   ```
3. Run matugen once (or change wallpaper), then pick **Matugen** in **Settings → Appearance**.

Shells that run user matugen templates on every wallpaper change, such as DankMaterialShell, keep Strata in sync without any extra step.

| Strata token | Material color |
| --- | --- |
| background | `surface` |
| surface | `surface_container` |
| text | `on_surface` |
| accent | `primary` |
| danger | `error` |
| muted | `surface_container_high` |
| highlight (selection) | `secondary_container` |
| border | `outline_variant` |
| dim_text | `on_surface_variant` |
| syntax keyword / string / constant / type / preprocessor | `tertiary` / `secondary` / `tertiary_fixed_dim` / `primary` / `on_surface_variant` |

## License

MIT. See [LICENSE](LICENSE).
