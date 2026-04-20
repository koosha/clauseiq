# ClauseIQ — docs/

Everything non-code lives here. This folder is also the root of the GitHub Pages site for this repo.

## What's here

| Path | What |
| --- | --- |
| `index.html` | Landing hub — links to every artifact below. Start here. |
| `design/wireframes/ClauseIQ_UI_Plan_v0.1.html` | Low-fi exploration of 3 UX directions (A · classic, B · command bar, C · workbench) with annotations and a recommendation. |
| `design/wireframes/ClauseIQ_HiFi_v0.1.html` | Hi-fi mockups of the chosen direction (C), all key states. |
| `design/wireframes/ClauseIQ_Prototype_v0.1_standalone.html` | **Standalone** interactive prototype — single file, works offline, works on GitHub Pages. This is the one to share. |
| `design/wireframes/ClauseIQ_Prototype_v0.1.html` | Multi-file dev version of the prototype (imports from `proto/*.jsx`). Useful for editing; does not work from plain `file://` — serve locally or use the standalone version. |
| `design/wireframes/proto/*.jsx` | Prototype source (data, palette, viewer, app). Dev-only. |
| `decisions/0001-*.md` | Design Decision Records (DDRs). Format: `NNNN-kebab-title.md`. One decision per file. |
| `architecture/` | Technical/architecture plans. |

## How the site is served

GitHub Pages is configured to deploy from `main` branch, `/docs` folder.

Every push to `main` rebuilds the site at `https://koosha.github.io/clauseiq/`.

- `.nojekyll` is present to bypass Jekyll processing — HTML/CSS/JS ship as-is.
- No build step, no CI.

## Versioning

- Design artifacts carry a `_v0.1`, `_v0.2`, etc. suffix in the filename.
- Never overwrite a shipped version — copy to a new version number, edit the copy.
- When a version is superseded, add a note at the top of the old file pointing at the replacement.

## Adding a new DDR

1. Copy the most recent `decisions/NNNN-*.md` to `decisions/<next-number>-<kebab-title>.md`.
2. Fill in: Context · Decision · Rationale · Consequences · Status.
3. Link it from `index.html`.

## Sharing

- **Internal teammates with repo access:** share the GitHub Pages URL.
- **External (e.g. showing a lawyer):** download the standalone prototype HTML and send the file directly — it works offline by double-click.
