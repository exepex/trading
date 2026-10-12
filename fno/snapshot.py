"""Render the HTML brief to a PNG with headless Chromium, so Slack can show it inline as an image."""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
from pathlib import Path

CANDIDATES = [
    "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell",
    "/opt/pw-browsers/chromium-*/chrome-linux/chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",  # every Windows 10/11 machine has Edge
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
BROWSER_COMMANDS = ("chromium", "chromium-browser", "google-chrome", "chrome", "msedge")


def find_browser() -> str | None:
    env = os.environ.get("CHROME_BIN")
    if env and Path(env).exists():
        return env
    for pattern in CANDIDATES:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    for name in BROWSER_COMMANDS:
        path = shutil.which(name)
        if path:
            return path
    return None


def _crop_to_content(png: Path) -> None:
    """Trim the empty page background below the content (the viewport is taller than the page)."""
    try:
        from PIL import Image
    except ImportError:
        return
    img = Image.open(png).convert("RGB")
    w, h = img.size
    bg = img.getpixel((2, h - 2))
    px = img.load()
    last = h - 1
    step = max(w // 60, 1)
    while last > 0 and all(px[x, last] == bg for x in range(0, w, step)):
        last -= 1
    img.crop((0, 0, w, min(h, last + 40))).save(png, optimize=True)


def snapshot(html: Path, png: Path, width: int = 760, height: int = 9000, scale: float = 2.0) -> Path | None:
    browser = find_browser()
    if not browser:
        return None
    args = [
        browser,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        f"--window-size={width},{height}",
        "--virtual-time-budget=6000",
        f"--screenshot={png.resolve()}",
        html.resolve().as_uri(),
    ]
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        args.insert(1, f"--proxy-server={proxy}")
    try:
        subprocess.run(args, check=True, capture_output=True, timeout=120)
    except (subprocess.SubprocessError, OSError):
        return None
    if not png.exists():
        return None
    _crop_to_content(png)
    return png


def split_png(png: Path, max_height: int = 3600) -> list[Path]:
    """Cut a tall snapshot into phone-screen pages, cutting only in the gaps between sections."""
    from PIL import Image

    img = Image.open(png).convert("RGB")
    w, h = img.size
    bg = img.getpixel((2, 2))
    px = img.load()
    step = max(w // 80, 1)

    def blank(y: int) -> bool:
        return all(px[x, y] == bg for x in range(0, w, step))

    cuts, top = [], 0
    while h - top > max_height:
        y = top + max_height
        while y > top + max_height // 3 and not blank(y):
            y -= 1
        if y <= top + max_height // 3:
            # A single section taller than a page: extend to its end rather than slicing through a chart.
            y = top + max_height
            while y < min(h - 1, top + max_height * 2) and not blank(y):
                y += 1
        cuts.append((top, y))
        top = y
    cuts.append((top, h))
    out = []
    for i, (a, b) in enumerate(cuts, 1):
        part = png.with_name(f"{png.stem}-{i}of{len(cuts)}.png")
        img.crop((0, a, w, b)).save(part, optimize=True)
        out.append(part)
    return out
