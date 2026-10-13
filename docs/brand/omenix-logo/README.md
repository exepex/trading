# Omenix logo (final, 13 Oct 2026)

One mark, chosen by the owner on 13 Oct 2026: the **signal**. The letter O is a trading range; the price line rises
through it and breaks out at the top right. Wordmark: "Omenix" only, Inter SemiBold converted to outlines (no font
needed). Colours come from the dashboard design system (`exepex/omenix-dashboard`, `design/system/tokens.css`):
accent gradient `#5a5ee6` to `#7a7df0` (the sidebar's active gradient), navy `#2f3349`, white. Green, red, amber and
teal stay semantic (profit, loss, warning, info) and are never used on the logo.

Every file stands alone; pick by folder. SVG scales to any size. Only text files are in git: the public-record scan
(story O5) refuses binaries, so `node src/export_final.mjs <svg-dir> <out-dir>` rebuilds the PNG exports listed
below with Playwright's Chromium (`python src/make_logos.py <out-dir>` rebuilds the SVGs; `src/render.mjs` draws the
comparison sheet of the three candidates the owner chose from, kept for the record in `preview.html`).

| Folder | Pick when | SVG in git | PNG exports (rebuilt) |
|---|---|---|---|
| `google-cloud/` | Google Cloud Console OAuth consent screen (app logo 120 x 120 px, PNG, under 1 MB) | avatar-gradient, avatar-white | oauth-app-logo-120, oauth-app-logo-white-120, app-logo-512 |
| `desktop/` | side menu wide with labels (1200 px and wider); wordmark in the top bar from 1360 px | tile, mark-white, mark-gradient, lockup-light, lockup-dark | rail-tile-36 (+-2x), mark-white-28 (+-2x) |
| `tablet/` | side menu icons only (600 to 1199 px) | tile | rail-tile-36 (+-2x) |
| `mobile/` | phone top bar (under 600 px), menu in a drawer | tile | topbar-tile-32 (+-2x, -3x) |
| `favicon/` | browser tab, home screen, PWA | tile, icon-maskable | favicon.ico (16+32+48), favicon-16/32/48, apple-touch-icon-180, pwa-icon-192/512, pwa-icon-maskable-512 |
| `social/` | Facebook, Instagram, Slack, Search Console profile pictures (circle crop safe) | avatar-gradient, avatar-navy, avatar-white | avatar-gradient-1024/400/320, avatar-navy-1024, avatar-white-1024 |
| `lockup/` | mark + wordmark: headers, cover images, documents | lockup-light, lockup-dark, lockup-mono-navy, lockup-mono-white | each at 600 px and 2048 px wide |
| `mark/` | the mark alone | mark-gradient, mark-white, mark-navy | each at 1024 px |

Rules: the tile keeps its 4 px corner radius at 36 px (11 % of the side); no shadow inside the files (the app adds the
rail glow); minimum 16 px for the tile and 24 px for the mark alone; clear space around the lock-up of one ring
width; never recolour with semantic colours.

## Handover

The dashboard repository gets this set under `design/brand/` through the mockups session, and `favicon/tile.svg`
replaces the old chart-line favicon in `web/app/layout.tsx`.
