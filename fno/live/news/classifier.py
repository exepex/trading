"""Reads a headline the way a desk analyst would at a glance: what kind of news it is, and good or bad for the price.

Rules only: fast and free, right most of the time on headlines. The AI analyst reads the important stories properly.
Every keyword is matched as a whole word ("oil" never matches "turmoil", "war" never "software").
"""

from __future__ import annotations

import re

from ...constants import NEWS_THEME_WORLD, NewsEventType
from .models import Story


def _words(*alternatives: str) -> re.Pattern:
    return re.compile(r"\b(?:" + "|".join(alternatives) + r")\b", re.IGNORECASE)


EVENT_PATTERNS: tuple[tuple[NewsEventType, re.Pattern], ...] = (
    (
        NewsEventType.ROUTINE,
        _words(
            r"certificate under",
            r"trading window",
            r"newspaper (?:publication|advertisement)s?",
            r"copy of newspaper",
            r"loss of share certificates?",
            r"duplicate share",
            r"investor (?:meet|presentation)",
            r"analysts? meet",
            r"change in registrar",
            r"esops?",
            r"intimation of (?:board meeting|record date)",
            r"compliance certificate",
        ),
    ),
    (  # previews, stock-pick lists and live blogs: talk about news, not news
        NewsEventType.OTHER,
        _words(
            r"preview",
            r"what to expect",
            r"set to (?:report|announce)",
            r"earnings (?:tracker|calendar)",
            r"things to watch",
            r"stocks? to (?:buy|watch|sell)",
            r"top \d+ stocks",
            r"buy or sell",
            r"live updates",
            r"trade setup",
            r"technical picks",
        ),
    ),
    (
        NewsEventType.RESULTS,
        _words(
            r"q[1-4]",
            r"quarterly",
            r"results?",
            r"net profit",
            r"revenue",
            r"ebitda",
            r"earnings",
            r"beats? (?:estimates|expectations)",
            r"miss(?:es)? (?:estimates|expectations)",
        ),
    ),
    (NewsEventType.GUIDANCE, _words(r"guidance", r"outlook", r"forecasts?")),
    (
        NewsEventType.REGULATORY,
        _words(
            r"sebi",
            r"rbi (?:penalty|bars|imposes|restricts)",
            r"bans?",
            r"banned",
            r"probes?",
            r"raids?",
            r"ed",
            r"cbi",
            r"income tax",
            r"penalt(?:y|ies)",
            r"fined?",
            r"show[- ]cause",
            r"usfda",
            r"warning letter",
            r"import alert",
        ),
    ),
    (
        NewsEventType.ORDER,
        re.compile(
            r"\b(?:bags?|bagged|wins?|won|secures?|receives?|gets?)\b.{0,40}\b(?:orders?|contracts?|projects?)\b|"
            r"\border (?:worth|win|inflow|book)\b|\bletter of (?:award|intent)\b|\bloa\b",
            re.IGNORECASE,
        ),
    ),
    (
        NewsEventType.CORPORATE_ACTION,
        _words(
            r"fund ?rais\w*",
            r"qip",
            r"rights issue",
            r"acqui\w+",
            r"merger",
            r"demerger",
            r"buyback",
            r"dividends?",
            r"bonus",
            r"stock split",
            r"split",
            r"delist\w*",
            r"ipo",
            r"stake (?:buy|purchase)",
        ),
    ),
    (
        NewsEventType.DEAL_FLOW,
        _words(r"block deals?", r"bulk deals?", r"stake sale", r"sells? stake", r"offloads?", r"ofs", r"pledge\w*"),
    ),
    (
        NewsEventType.MANAGEMENT,
        _words(r"ceo", r"cfo", r"managing director", r"md", r"chairman", r"resign\w*", r"steps? down", r"appoint\w*"),
    ),
    (
        NewsEventType.RATING,
        _words(
            r"upgrades?",
            r"downgrades?",
            r"target price",
            r"rating",
            r"initiates? coverage",
            r"overweight",
            r"underweight",
            r"buy call",
            r"sell call",
        ),
    ),
)
MACRO_PATTERN = _words(
    r"repo rate",
    r"policy rate",
    r"inflation",
    r"gdp",
    r"fed",
    r"fomc",
    r"crude",
    r"oil prices?",
    r"brent",
    r"bond yields?",
    r"yields?",
    r"dollar",
    r"rupee",
    r"tariffs?",
    r"war",
    r"missiles?",
    r"attacks?",
    r"sanctions?",
)
UP_WORDS = (
    r"recovers?",
    r"jumps?",
    r"surges?",
    r"soars?",
    r"rall(?:y|ies)",
    r"gains?",
    r"rises?",
    r"climbs?",
    r"spikes?",
    r"higher",
    r"advances?",
    r"rebounds?",
)
DOWN_WORDS = (
    r"falls?",
    r"drops?",
    r"slumps?",
    r"plunges?",
    r"tanks?",
    r"crash(?:es)?",
    r"slides?",
    r"declines?",
    r"slips?",
    r"lower",
    r"tumbles?",
    r"sinks?",
    r"weakens?",
)
POSITIVE = _words(
    *UP_WORDS,
    r"beats?",
    r"record high",
    r"wins?",
    r"bags?",
    r"secures?",
    r"upgrade[sd]?",
    r"approv(?:al|es|ed)",
    r"buyback",
    r"bonus",
    r"strong",
    r"expands?",
    r"boost\w*",
    r"highs?",
    r"narrows? loss",
    r"turns? profitable",
    r"ceasefire",
    r"rate cut",
)
NEGATIVE = _words(
    *DOWN_WORDS,
    r"misses?",
    r"loss(?:es)?",
    r"downgrade[sd]?",
    r"cuts? (?:target|guidance|rating|outlook)",
    r"probes?",
    r"raids?",
    r"penalt(?:y|ies)",
    r"fined?",
    r"bans?",
    r"bars",
    r"fraud",
    r"defaults?",
    r"resign\w*",
    r"warning letter",
    r"import alert",
    r"pledge\w*",
    r"stake sale",
    r"offloads?",
    r"weak",
    r"slowdown",
    r"halts?",
    r"shut ?down",
    r"war",
    r"attacks?",
    r"missiles?",
    r"sanctions?",
    r"rate hike",
    r"lows?",
    r"turmoil",
)
# Costs for Indian markets: when these themselves rise it is bad news, when they fall good news. The move word must
# follow the cost directly ("crude jumps 4%", "US yields ease"), never across a clause ("Dollar steady, Sensex rises").
COST_SUBJECT = r"\b(?:crude(?: oil)?|oil prices?|brent(?: crude)?|(?:us |bond |treasury )?yields?|dollar(?: index)?)"
RUPEE_SUBJECT = r"\brupee"
COST_EASES = (r"eases?", r"cools?", r"softens?", r"retreats?")
IN_BETWEEN = r"(?:\s+(?:prices?|futures|index|sharply|further|again|nearly|over|by|\$?[\d.,]+%?))*"
# what usually follows the move and must go with it: "to a 16-year high", "from record low", "3%", "20 paise"
MOVE_TAIL = (
    r"(?:\s+(?:by\s+)?[\d.,]+\s*(?:%|paise|points?|bps|basis points)?)?"
    r"(?:\s+(?:to|from|at)\s+(?:a\s+)?[\w-]+(?:\s+[\w-]+)?\s+(?:highs?|lows?))?"
    r"(?:\s+(?:after|from|off|since)(?:\s+(?:record|fresh|recent|lifetime|all-time|multi-year|session|intraday|"
    r"\d+-\w+))?\s+(?:highs?|lows?)(?:\s+of\s+\d{4})?)?"  # "high after record lows", never "after Nifty lows"
)


def _moves(subject: str, words: tuple[str, ...]) -> re.Pattern:
    return re.compile(subject + IN_BETWEEN + r"\s+(?:" + "|".join(words) + r")\b" + MOVE_TAIL, re.IGNORECASE)


COST_RISES = _moves(COST_SUBJECT, (*UP_WORDS, "up"))
COST_FALLS = _moves(COST_SUBJECT, (*DOWN_WORDS, *COST_EASES, "down"))
LOW_LEVEL = r"(?:lows?|lowest|weakest)"
HIGH_LEVEL = r"(?:highs?|peak|highest|strongest)"
LEVEL_STOP = r"(?:back|from|with|after|off|since|against|amid|on)"
# up to 3 words between "hits" and the level, never past another level word or a linking word: "hits 3-week high after
# lows" is a high, "hits importers with lowest margins" says nothing about the rupee's level
LEVEL_FILLER = rf"(?:\s+(?!(?:{LOW_LEVEL}|{HIGH_LEVEL}|{LEVEL_STOP})\b)(?:an?\s+)?[\w-]+){{0,3}}"
RUPEE_HITS_LOW = rf"hits{LEVEL_FILLER}\s+{LOW_LEVEL}"  # "hits record low", "hits weakest level"
RUPEE_HITS_HIGH = rf"hits{LEVEL_FILLER}\s+{HIGH_LEVEL}"  # "hits one-year peak"
# A strong dollar is a cost only as the stated cause of a move ("rupee falls on strong dollar"): never after "despite",
# never when it is fading or describes something else ("strong dollar inflows", "dollar strength eases")
STRONG_DOLLAR = re.compile(
    r"(\bdespite\s+(?:an?\s+|the\s+)?)?\b(?:(?:strong(?:er)?|firm(?:er)?|surging|rising)\s+dollar|dollar strength)\b"
    r"(?!\s+(?:inflows?|revenues?|deposits?|bonds?|fades?|eases?|wanes?|ebbs?|cools?)\b)",
    re.IGNORECASE,
)
RUPEE_FALLS = _moves(RUPEE_SUBJECT, (*DOWN_WORDS, "down", RUPEE_HITS_LOW))
RUPEE_RISES = _moves(RUPEE_SUBJECT, (*UP_WORDS, "up", RUPEE_HITS_HIGH))


def event_type(story: Story) -> NewsEventType:
    text = f"{story.title} {story.summary[:200]}"
    for event, pattern in EVENT_PATTERNS:
        if pattern.search(text):
            return event
    if NEWS_THEME_WORLD in story.themes or MACRO_PATTERN.search(text):
        return NewsEventType.MACRO
    return NewsEventType.OTHER


def _sign(value: float) -> float:
    return (value > 0) - (value < 0)


def direction(story: Story) -> float:
    """-1 (bad for the price) to +1 (good); 0 when the headline does not say. A source's own score wins.
    Phrases about costs ("crude surges", "rupee falls") are scored for India first and removed; the rest of the
    headline is scored by its own words; the two are averaged."""
    if story.sentiment is not None:
        return max(-1.0, min(1.0, story.sentiment))
    text, macro = story.title, []
    for pattern, sign in ((COST_RISES, -1.0), (COST_FALLS, 1.0), (RUPEE_FALLS, -1.0), (RUPEE_RISES, 1.0)):
        for match in pattern.finditer(text):
            macro.append(sign)
            text = text.replace(match.group(0), " ")
    strong_dollar = [m for m in STRONG_DOLLAR.finditer(text) if not m.group(1)]
    for match in STRONG_DOLLAR.finditer(text):
        text = text.replace(match.group(0), " ")  # "strong" here is about the dollar, not the stock
    if strong_dollar and not macro:  # only a cause when no rupee or cost move was named
        macro.append(-1.0)
    up, down = len(POSITIVE.findall(text)), len(NEGATIVE.findall(text))
    parts = ([(up - down) / (up + down)] if up + down else []) + ([_sign(sum(macro))] if macro else [])
    return sum(parts) / len(parts) if parts else 0.0
