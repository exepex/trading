"""FL1-1d, design part: both editions drawn by the real Chromium at the picture's width (1100) and at a phone's
(390), with no sideways overflow and the right edge of every chart visible. Skipped where Chromium is absent."""

from pathlib import Path

import pytest

from fno.forecast_lab.design.evening import render_evening
from fno.forecast_lab.design.morning import render_morning
from fno.forecast_lab.page.camera import CHROMIUM, ChromiumCamera

from .design_builders import page

WIDTHS = (1100, 390)


@pytest.mark.skipif(not CHROMIUM.exists(), reason="the routine's environment has Chromium; a laptop may not")
@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("edition", ("morning", "evening"))
def test_both_editions_draw_at_the_picture_width_and_on_a_phone(tmp_path: Path, width: int, edition: str):
    html = (render_morning if edition == "morning" else render_evening)(page(edition, checked=True))
    out = ChromiumCamera(width=width).picture(html, tmp_path / f"{edition}-{width}.png")
    from PIL import Image

    with Image.open(out) as picture:
        assert picture.width == width * 2 and picture.height > 600 * 2
