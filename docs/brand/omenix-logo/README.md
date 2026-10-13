# Omenix logo candidates (13 Oct 2026)

Three marks for the owner to choose from. All colours come from the dashboard design system
(`exepex/omenix-dashboard`, `design/system/tokens.css`, scheme v2): accent indigo `#5a5ee6` to `#7a7df0`
(the sidebar's active gradient), navy `#2f3349` (sidebar, light theme) and `#1f2233` (sidebar, dark theme).
Green, red, amber and teal are left to profit, loss, warning and info meaning, so no mark uses them.
Wordmark: "Omenix" only, Inter SemiBold converted to outlines (no font needed). `preview.html` shows every mark in
the rail (36 px tile, light and dark), on a phone (32 px), as a favicon (16 px), as a circle-cropped avatar and
as both lock-ups.

Only text files are committed: the public-record scan (story O5) refuses binaries, so the PNG exports are not in
git. `node src/render.mjs <dir>` rebuilds every PNG listed below (and `preview.png`) in under a minute.

| Folder | Idea | Reads as |
|---|---|---|
| `signal/` | The O is a trading range; the price line rises through it and breaks out at the top right | breakout, outlook |
| `omen/` | An upper eyelid over an open ring iris: the omen, watching what is coming | foresight, an O in the eye |
| `monogram/` | O and M in one shape: the ring with the M standing inside it | OM, a seal |

## Files in each folder

| File | Use |
|---|---|
| `mark-gradient.svg` | the mark alone, accent gradient, on white or light surfaces |
| `mark-white.svg`, `mark-navy.svg` | single-colour marks for the navy rail (white) and for print or mono (navy) |
| `tile.svg` + `png/tile-{16,32,48,180,192,512}.png` | app rail tile (36 px, 4 px radius), favicon (16, 32, 48), Apple touch icon (180), PWA icon (192, 512) |
| `icon-maskable.svg` + `png/icon-maskable-512.png` | Android maskable icon: the mark sits inside the safe 80 % circle |
| `avatar-gradient.svg`, `avatar-navy.svg`, `avatar-white.svg` + `png/avatar-*-{512,1024}.png` | square profile pictures for Facebook, Instagram, Google Cloud Console, Search Console, Slack; safe for the circle crop |
| `lockup-light.svg`, `lockup-dark.svg` + `png/lockup-*-2048.png` | mark + wordmark for page headers, cover images and documents |
| `lockup-mono-navy.svg`, `lockup-mono-white.svg` | single-colour lock-ups where gradients are not allowed |

Rules: no shadow inside the files (the app adds the rail glow itself); minimum size 16 px for the tile and 24 px
for the mark alone; clear space around the lock-up of one ring width; never recolour with semantic colours.

## Rebuild

`python src/make_logos.py <out-dir>` writes the SVGs (needs `fonttools` and the Inter OTF files);
`node src/render.mjs <out-dir>` renders the PNGs and `preview.png` with Playwright's Chromium.

## Handover

The owner's decision (13 Oct 2026): the chosen files go to the dashboard repository under `design/brand/` through
the mockups session, and replace the old chart-line favicon in `web/app/layout.tsx`.
