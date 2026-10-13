// Render the logo SVGs to PNG and a preview sheet with Chromium (node render.mjs <logo-dir>)
import pw from "playwright";
const { chromium } = pw;
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const dir = process.argv[2];
const MARKS = ["signal", "omen", "monogram"];
const NAVY = "#2f3349", DARK = "#1f2233", PAGE = "#f7f7f9";
const read = (m, f) => readFileSync(join(dir, m, f), "utf8");

function sheet() {
  const row = (m) => `
  <section>
    <h2>${m}</h2>
    <div class="ctx">
      <div class="rail" title="rail, light theme, 36 px tile">${read(m, "tile.svg").replace('width="64" height="64"', 'width="36" height="36"')}<span class="lbl">Dashboard</span></div>
      <div class="rail dark" title="rail, dark theme">${read(m, "tile.svg").replace('width="64" height="64"', 'width="36" height="36"')}<span class="lbl">Dashboard</span></div>
      <div class="phone" title="phone 32 px">${read(m, "tile.svg").replace('width="64" height="64"', 'width="32" height="32"')}</div>
      <div class="fav" title="favicon 16 px">${read(m, "tile.svg").replace('width="64" height="64"', 'width="16" height="16"')} <span>16 px</span></div>
      <div class="circle">${read(m, "avatar-gradient.svg").replace('width="64" height="64"', 'width="96" height="96"')}</div>
      <div class="circle">${read(m, "avatar-navy.svg").replace('width="64" height="64"', 'width="96" height="96"')}</div>
      <div class="circle white">${read(m, "avatar-white.svg").replace('width="64" height="64"', 'width="96" height="96"')}</div>
      <div class="big">${read(m, "mark-gradient.svg").replace('width="64" height="64"', 'width="140" height="140"')}</div>
    </div>
    <div class="lock light">${read(m, "lockup-light.svg").replace(/height="44(?:\.0)?"/, 'height="56"').replace(/ width="[\d.]+"/, "")}</div>
    <div class="lock dark">${read(m, "lockup-dark.svg").replace(/height="44(?:\.0)?"/, 'height="56"').replace(/ width="[\d.]+"/, "")}</div>
  </section>`;
  return `<!doctype html><meta charset="utf-8"><style>
  body{margin:0;padding:24px;background:${PAGE};font:14px Inter,sans-serif;color:#4b465c;width:1180px}
  h2{margin:0 0 10px;font:600 16px Inter;text-transform:capitalize}
  section{background:#fff;border-radius:4px;box-shadow:0 2px 8px rgba(47,51,73,.08);padding:20px;margin-bottom:20px}
  .ctx{display:flex;align-items:center;gap:20px;margin-bottom:16px}
  .rail{background:${NAVY};width:84px;height:120px;display:flex;flex-direction:column;align-items:center;gap:14px;padding-top:12px;border-radius:4px}
  .rail.dark{background:${DARK}}
  .rail svg{filter:drop-shadow(0 4px 12px rgba(90,94,230,.45))}
  .lbl{color:#d7d8e5;font:500 11px Inter}
  .phone{background:#fff;width:56px;height:56px;display:grid;place-items:center;box-shadow:0 0 0 1px #e7e9ef}
  .fav{display:flex;align-items:center;gap:6px;color:#65708a;font-size:12px}
  .circle{width:96px;height:96px;border-radius:50%;overflow:hidden;box-shadow:0 0 0 1px #e7e9ef}
  .circle svg{display:block}
  .lock{padding:18px 24px;border-radius:4px;margin-top:10px;display:inline-block;margin-right:16px}
  .lock.light{background:#fff;box-shadow:0 0 0 1px #e7e9ef}.lock.dark{background:${NAVY}}
  </style><body>${MARKS.map(row).join("")}</body>`;
}

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 2 });
writeFileSync(join(dir, "preview.html"), sheet());
await page.setContent(sheet());
await page.screenshot({ path: join(dir, "preview.png"), fullPage: true });

// PNG exports
const sizes = { "tile.svg": [16, 32, 48, 180, 192, 512], "icon-maskable.svg": [512], "avatar-gradient.svg": [512, 1024], "avatar-navy.svg": [512, 1024], "avatar-white.svg": [512, 1024] };
for (const m of MARKS) {
  const png = join(dir, m, "png"); mkdirSync(png, { recursive: true });
  for (const [f, list] of Object.entries(sizes)) for (const s of list) {
    const svg = read(m, f).replace('width="64" height="64"', `width="${s}" height="${s}"`);
    await page.setContent(`<body style="margin:0;background:transparent">${svg}</body>`);
    const el = await page.$("svg");
    await el.screenshot({ path: join(png, `${f.replace(".svg", "")}-${s}.png`), omitBackground: true });
  }
  for (const f of ["lockup-light.svg", "lockup-dark.svg"]) {
    // scale so the lock-up is 2048 px wide
    const w = Number(read(m, f).match(/ width="([\d.]+)"/)[1]);
    const h = Math.round(44 * 2048 / w);
    const svg2 = read(m, f).replace(/ width="[\d.]+" height="44(?:\.0)?"/, ` width="2048" height="${h}"`);
    await page.setContent(`<body style="margin:0;background:transparent">${svg2}</body>`);
    const el = await page.$("svg");
    await el.screenshot({ path: join(png, `${f.replace(".svg", "")}-2048.png`), omitBackground: true });
  }
}
await browser.close();
console.log("rendered", dir);
