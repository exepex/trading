"""Which F&O underlyings and world themes a headline is about, from company names, symbols and index words."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ...constants import NEWS_THEME_WORLD

NAME_SUFFIXES = re.compile(r"\b(limited|ltd\.?|corporation|corp\.?|company|co\.?|\(india\))\s*$", re.IGNORECASE)
MIN_FIRST_WORD_LENGTH = 5  # "Reliance" alone may name Reliance Industries; "Tata" or "Bank" may not
MIN_SYMBOL_LENGTH = 3
INDEX_PATTERNS = {
    "BANKNIFTY": re.compile(r"\b(bank\s*nifty|nifty\s*bank)\b", re.IGNORECASE),
    "FINNIFTY": re.compile(r"\b(fin\s*nifty|nifty\s*financial)\b", re.IGNORECASE),
    "NIFTY": re.compile(
        r"\b((?<!bank )(?<!bank)(?<!fin )(?<!fin)"  # not the second word of Bank Nifty / Fin Nifty
        r"nifty(?!\s*(bank|financial|midcap|smallcap|it|pharma|auto|metal))|sensex)\b",
        re.IGNORECASE,
    ),
}
WORLD_RISK_PATTERN = re.compile(
    r"\b(war|missile|strike[sd]?|attack|ceasefire|sanction\w*|tariff\w*|crude|oil|opec|brent|fed|fomc|"
    r"rate (cut|hike)|inflation|recession|treasur(y|ies)|yields?|dollar|rupee|gold|china|iran|israel|russia|"
    r"ukraine|houthi\w*|wall street|nasdaq|dow|s&p|nikkei|kospi|hang seng)\b",
    re.IGNORECASE,
)
GENERIC_FIRST_WORDS = frozenset(  # first words that name many things besides one company: never used alone
    "india indian bharat global national state power steel union central general great hindustan united "  # noqa: SIM905
    "eastern western southern northern life first prime capital sun bank star max oil coal gujarat indus "
    "asian money metro home".split()
)
COMMON_WORD_SYMBOLS = {"IDEA", "BEL", "ABB", "MRF", "PEL", "SAIL", "IRFC", "NHPC", "GAIL"}  # matched by name only


@dataclass(frozen=True)
class Alias:
    pattern: re.Pattern
    symbol: str


def _clean_name(name: str) -> str:
    previous = None
    name = name.strip().rstrip(".")
    while previous != name:
        previous, name = name, NAME_SUFFIXES.sub("", name).strip().rstrip(",.")
    return name


class SymbolTagger:
    def __init__(self, company_names: dict[str, str]):
        """company_names: NSE symbol -> company name (from NSE's index constituent files)."""
        first_words: dict[str, list[str]] = {}
        aliases = []
        for symbol, name in company_names.items():
            clean = _clean_name(name)
            if clean:
                aliases.append(Alias(re.compile(rf"\b{re.escape(clean)}\b", re.IGNORECASE), symbol))
                first_words.setdefault(clean.split()[0].lower(), []).append(symbol)
            if len(symbol) >= MIN_SYMBOL_LENGTH and symbol not in COMMON_WORD_SYMBOLS and symbol.isalpha():
                aliases.append(Alias(re.compile(rf"\b{re.escape(symbol)}\b"), symbol))  # case-sensitive: TCS, not tcs
        for word, symbols in first_words.items():
            if len(symbols) == 1 and len(word) >= MIN_FIRST_WORD_LENGTH and word not in GENERIC_FIRST_WORDS:
                aliases.append(Alias(re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE), symbols[0]))
        self.aliases = aliases

    def symbols(self, text: str, already: tuple[str, ...] = ()) -> tuple[str, ...]:
        found = list(already)
        found += [alias.symbol for alias in self.aliases if alias.pattern.search(text)]
        found += [index for index, pattern in INDEX_PATTERNS.items() if pattern.search(text)]
        return tuple(dict.fromkeys(found))

    @staticmethod
    def themes(text: str) -> tuple[str, ...]:
        return (NEWS_THEME_WORLD,) if WORLD_RISK_PATTERN.search(text) else ()
