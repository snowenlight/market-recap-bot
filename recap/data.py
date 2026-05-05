from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf

from recap.config import Instrument


@dataclass(frozen=True)
class Quote:
    instrument: Instrument
    last: float
    prev: float

    @property
    def change(self) -> float:
        return self.last - self.prev

    @property
    def change_pct(self) -> float:
        if self.prev == 0:
            return 0.0
        return (self.last - self.prev) / self.prev * 100.0


def fetch_quote(instrument: Instrument) -> Quote | None:
    """Fetch the last close and previous close for one instrument.

    Returns None if Yahoo did not return at least two rows.
    """
    hist = yf.Ticker(instrument.symbol).history(period="5d", auto_adjust=False)
    closes = hist["Close"].dropna()
    if len(closes) < 2:
        return None
    return Quote(
        instrument=instrument,
        last=float(closes.iloc[-1]),
        prev=float(closes.iloc[-2]),
    )


def fetch_quotes(instruments: list[Instrument]) -> list[Quote | None]:
    return [fetch_quote(i) for i in instruments]
