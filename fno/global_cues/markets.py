"""When each foreign market's close is final (story A17e): its time zone and the local time its closing value is fixed,
the input of `available_at` and of the as-of rule. Times are the end of each market's closing auction (reasoning from
the exchanges' published hours; the boundary tests pin them), so a value is never labelled known before its market
could have fixed it. Daylight saving follows the zone (Sydney, London, Frankfurt, New York)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from .source import at_local


@dataclass(frozen=True)
class MarketClose:
    zone: str
    close: time

    def available_at(self, value_date: date) -> datetime:
        return at_local(value_date, self.close, self.zone)


TOKYO = MarketClose("Asia/Tokyo", time(15, 30))  # 12:00 IST
SEOUL = MarketClose("Asia/Seoul", time(15, 30))  # 12:00 IST
SHANGHAI = MarketClose("Asia/Shanghai", time(15, 0))  # 12:30 IST
TAIPEI = MarketClose("Asia/Taipei", time(13, 30))  # 11:00 IST
HONG_KONG = MarketClose("Asia/Hong_Kong", time(16, 10))  # after the closing auction: 13:40 IST
SINGAPORE = MarketClose("Asia/Singapore", time(17, 0))  # 14:30 IST
# after the closing auction: 10:40 IST in Australian summer time, 11:40 in winter
SYDNEY = MarketClose("Australia/Sydney", time(16, 10))
LONDON = MarketClose("Europe/London", time(16, 35))  # after the closing auction
FRANKFURT = MarketClose("Europe/Berlin", time(17, 35))  # Xetra after the closing auction
EURO_STOXX = MarketClose("Europe/Berlin", time(17, 50))  # the Euro Stoxx 50's final value
NEW_YORK = MarketClose("America/New_York", time(16, 0))
CBOE_VIX = MarketClose("America/New_York", time(16, 15))  # VIX is calculated until 16:15 New York
