"""Reads a headline the way a desk analyst would at a glance: what kind of news it is, and good or bad for the stock.

Rules only: fast and free, right most of the time on headlines. The AI analyst reads the important stories properly.
"""

from __future__ import annotations

import re

from ...constants import NEWS_THEME_WORLD, NewsEventType
from .models import Story

EVENT_PATTERNS: tuple[tuple[NewsEventType, re.Pattern], ...] = tuple(
    (event, re.compile(pattern, re.IGNORECASE))
    for event, pattern in (
        (
            NewsEventType.ROUTINE,
            r"certificate under|trading window|newspaper (publication|advertisement)|copy of newspaper|"
            r"loss of share certificate|duplicate share|investor (meet|presentation)|analysts? meet|"
            r"change in registrar|esop|intimation of (board meeting|record date)|compliance certificate",
        ),
        (
            NewsEventType.RESULTS,
            r"\bq[1-4]\b|quarterly|results?\b|net profit|profit (rises|falls|jumps|drops|up|down)|"
            r"revenue|ebitda|earnings|beats? (estimates|expectations)|miss(es)? (estimates|expectations)",
        ),
        (NewsEventType.GUIDANCE, r"guidance|outlook|forecast"),
        (
            NewsEventType.REGULATORY,
            r"\bsebi\b|\brbi\b (action|penalty|bars|imposes)|\bban(s|ned)?\b|probe|raid|"
            r"\bed\b|\bcbi\b|income tax|penalt|\bfined?\b|show[- ]cause|usfda|warning letter|import alert",
        ),
        (
            NewsEventType.ORDER,
            r"\b(bags?|bagged|wins?|won|secures?|receives?|gets?)\b.{0,40}\b(orders?|contracts?|projects?)\b|"
            r"\border (worth|win|inflow|book)|letter of (award|intent)|\bloa\b",
        ),
        (
            NewsEventType.CORPORATE_ACTION,
            r"fund ?rais|\bqip\b|rights issue|acqui|merger|demerger|buyback|dividend|"
            r"bonus|split|delist|\bipo\b|stake (buy|purchase)",
        ),
        (NewsEventType.DEAL_FLOW, r"block deal|bulk deal|stake sale|sells? stake|offload|\bofs\b|pledge"),
        (NewsEventType.MANAGEMENT, r"\bceo\b|\bcfo\b|managing director|\bmd\b|chairman|resign|steps? down|appoint"),
        (
            NewsEventType.RATING,
            r"upgrade|downgrade|target price|\btarget\b|rating|initiates? coverage|overweight|"
            r"underweight|buy call|sell call|brokerage",
        ),
    )
)
MACRO_PATTERN = re.compile(
    r"repo rate|policy rate|inflation|\bgdp\b|\bfed\b|fomc|crude|oil|brent|yields?|dollar|"
    r"rupee|tariff|war|missile|attack|sanction",
    re.IGNORECASE,
)
POSITIVE = re.compile(
    r"jumps?|surges?|soars?|rall(y|ies)|gains?|rises?|climbs?|beats?|record high|\bwins?\b|bags?|"
    r"secures?|upgrade[sd]?|approv(al|es|ed)|buyback|bonus|strong|expands?|higher|boost|\bhighs?\b|"
    r"narrows? loss|turns? profitable|ceasefire|rate cut",
    re.IGNORECASE,
)
NEGATIVE = re.compile(
    r"falls?|drops?|slumps?|plunges?|tanks?|crash(es)?|slides?|declines?|misses?|\bloss(es)?\b|"
    r"downgrade[sd]?|cuts? (target|guidance|rating|outlook)|probe|raid|penalt|\bfined?\b|\bbans?\b|"
    r"\bbars\b|fraud|default|resign|warning letter|import alert|pledge|stake sale|offload|weak|"
    r"slowdown|halts?|shut ?down|war|attack|missile|sanctions?|rate hike|lower|\blows?\b",
    re.IGNORECASE,
)
COST_PRESSURES = re.compile(r"crude|oil|brent|yields?|dollar|inflation", re.IGNORECASE)  # rising = bad for India


def event_type(story: Story) -> NewsEventType:
    text = f"{story.title} {story.summary[:200]}"
    for event, pattern in EVENT_PATTERNS:
        if pattern.search(text):
            return event
    if NEWS_THEME_WORLD in story.themes or MACRO_PATTERN.search(text):
        return NewsEventType.MACRO
    return NewsEventType.OTHER


def direction(story: Story) -> float:
    """-1 (bad for the price) to +1 (good); 0 when the headline does not say. A source's own score wins."""
    if story.sentiment is not None:
        return max(-1.0, min(1.0, story.sentiment))
    text = story.title
    up, down = len(POSITIVE.findall(text)), len(NEGATIVE.findall(text))
    if up + down == 0:
        return 0.0
    score = (up - down) / (up + down)
    if COST_PRESSURES.search(text) and not re.search(r"war|attack|missile|sanction", text, re.IGNORECASE):
        score = -score  # "crude jumps" is bad news for Indian markets, "oil falls" good
    return score
