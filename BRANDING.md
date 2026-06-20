# FoFo brand assets

<p align="center">
  <img src="./assets/icon-transparent.png" alt="FoFo mark" width="160">
</p>

The mark is a navy hexagon "gate" badge holding a teal checkmark whose stroke rises
through three dots into an amber spark — *a green test run, passing.* It ties the
two ideas the project is about: a **gate** (verification) and a **passing run you can
trust**.

## Palette

| Token | Hex | Use |
|-------|-----|-----|
| Navy | `#1B2440` | primary / backgrounds / the badge |
| Deep navy | `#0E1430` | gradient floor |
| Teal | `#10B78F` | primary accent (pass / gates) |
| Mint | `#7FE3CB` | secondary accent / subtitles |
| Amber | `#F5A623` | spark / single highlight, used sparingly |
| Off-white | `#EEF2F7` | text on dark |

## Typography

- **Wordmark / headings:** a geometric sans (SF Pro Display / Helvetica Neue / Arial).
  "FoFo" is set tight (`letter-spacing: -2px`, weight 800), with the second "Fo" in
  teal.
- **Labels / code / subtitles:** a monospace (SF Mono / Menlo), uppercase and
  letter-spaced for role labels and the `/fofo:sdlc` chip.

## Assets

| File | Size | Use |
|------|------|-----|
| `assets/icon.png` | 1024² | app/skill icon (white background) |
| `assets/icon-transparent.png` | 1024² | icon on any background |
| `assets/icon-{512,256,128,64,32}.png` | square | sized icons |
| `assets/favicon.ico` | multi | favicon (16/32/48/64) |
| `assets/banner.png` | 1280×640 | GitHub social preview & README hero |
| `assets/header.png` | 1280×340 | slim README header |
| `assets/architecture.png` | 1280×560 | the "how it works" diagram |

## Regenerating

Branding was generated with **Imagen 4** (Vertex AI) for the mark, and composed into
banners/diagrams with HTML rendered headlessly to PNG. The mark prompt and the
HTML/CSS compositors are reproducible; keep the palette and the hexagon-gate +
rising-check-dots motif consistent if you re-roll.

## Usage

- Keep clear space around the mark equal to the height of one badge dot.
- Don't recolor the mark outside the palette, stretch it, or add a drop shadow on
  light backgrounds.
- Amber is a *spark*, not a fill — use it for one small accent at a time.

## Set the GitHub social preview

Repo **Settings → General → Social preview → Upload an image** → `assets/banner.png`.
(GitHub has no API for this, so it's a one-time manual step.)
