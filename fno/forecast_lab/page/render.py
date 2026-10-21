"""How the page is drawn (story FL1-1c): a port, so the owner's signed-off design (the designer's session owns the
look) replaces the interim drawing by one class and one line in the composition root, with nothing else changing."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .html import render_page
from .model import PageView
from .simple import render_simple


class PageRenderer(ABC):
    @abstractmethod
    def picture(self, view: PageView) -> str:
        """The HTML the picture is drawn from: what a reader sees in the message."""

    @abstractmethod
    def details(self, view: PageView) -> str:
        """The attached HTML file: everything behind the picture."""


class InterimRenderer(PageRenderer):
    """The v4 drawing, used until the designer's is signed off."""

    def picture(self, view: PageView) -> str:
        return render_simple(view)

    def details(self, view: PageView) -> str:
        return render_page(view)
