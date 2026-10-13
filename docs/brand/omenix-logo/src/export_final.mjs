// Export the chosen mark as independent files, one per use (node export_final.mjs <svg-dir> <out-dir>)
import pw from "playwright";
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from "node:fs";
import { join } from "node:path";
const { chromium } = pw;
const [src, out] = process.argv.slice(2);
const read = (f) => readFileSync(join(src, f), "utf8");
const SETS = {
  "google-cloud":   [["avatar-gradient.svg", 120, "oauth-app-logo-120.png"], ["avatar-gradient.svg", 512, "app-logo-512.png"], ["avatar-white.svg", 120, "oauth-app-logo-white-120.png"]],
  "desktop":        [["tile.svg", 36, "rail-tile-36.png"], ["tile.svg", 72, "rail-tile-36-2x.png"], ["mark-white.svg", 28, "mark-white-28.png"], ["mark-white.svg", 56, "mark-white-28-2x.png"]],
  "tablet":         [["tile.svg", 36, "rail-tile-36.png"], ["tile.svg", 72, "rail-tile-36-2x.png"]],
  "mobile":         [["tile.svg", 32, "topbar-tile-32.png"], ["tile.svg", 64, "topbar-tile-32-2x.png"], ["tile.svg", 96, "topbar-tile-32-3x.png"]],
  "favicon":        [["tile.svg", 16, "favicon-16.png"], ["tile.svg", 32, "favicon-32.png"], ["tile.svg", 48, "favicon-48.png"], ["tile.svg", 180, "apple-touch-icon-180.png"], ["tile.svg", 192, "pwa-icon-192.png"], ["tile.svg", 512, "pwa-icon-512.png"], ["icon-maskable.svg", 512, "pwa-icon-maskable-512.png"]],
  "social":         [["avatar-gradient.svg", 1024, "avatar-gradient-1024.png"], ["avatar-navy.svg", 1024, "avatar-navy-1024.png"], ["avatar-white.svg", 1024, "avatar-white-1024.png"], ["avatar-gradient.svg", 400, "avatar-gradient-400.png"], ["avatar-gradient.svg", 320, "avatar-gradient-320.png"]],
};
const SVGS = {
  "google-cloud": ["avatar-gradient.svg", "avatar-white.svg"], "desktop": ["tile.svg", "mark-white.svg", "mark-gradient.svg", "lockup-light.svg", "lockup-dark.svg"],
  "tablet": ["tile.svg"], "mobile": ["tile.svg"], "favicon": ["tile.svg", "icon-maskable.svg"],
  "social": ["avatar-gradient.svg", "avatar-navy.svg", "avatar-white.svg"],
  "lockup": ["lockup-light.svg", "lockup-dark.svg", "lockup-mono-navy.svg", "lockup-mono-white.svg"], "mark": ["mark-gradient.svg", "mark-white.svg", "mark-navy.svg"],
};
const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 1 });
async function shoot(svg, path) {
  await page.setContent(`<body style="margin:0;background:transparent">${svg}</body>`);
  await (await page.$("svg")).screenshot({ path, omitBackground: true });
}
for (const [set, files] of Object.entries(SVGS)) { mkdirSync(join(out, set), { recursive: true }); for (const f of files) copyFileSync(join(src, f), join(out, set, f)); }
for (const [set, list] of Object.entries(SETS)) for (const [f, s, name] of list) await shoot(read(f).replace('width="64" height="64"', `width="${s}" height="${s}"`), join(out, set, name));
for (const f of ["lockup-light.svg", "lockup-dark.svg", "lockup-mono-navy.svg", "lockup-mono-white.svg"]) {
  const w = Number(read(f).match(/ width="([\d.]+)"/)[1]);
  for (const W of [600, 2048]) await shoot(read(f).replace(/ width="[\d.]+" height="44"/, ` width="${W}" height="${Math.round(44 * W / w)}"`), join(out, "lockup", f.replace(".svg", `-${W}.png`)));
}
for (const [f, W] of [["mark-gradient.svg", 1024], ["mark-white.svg", 1024], ["mark-navy.svg", 1024]]) await shoot(read(f).replace('width="64" height="64"', `width="${W}" height="${W}"`), join(out, "mark", f.replace(".svg", `-${W}.png`)));
await browser.close();
console.log("exported", out);
