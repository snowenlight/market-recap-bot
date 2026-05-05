from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Instrument:
    symbol: str
    label: str
    kind: str  # fx | fx_jpy | yield | index


@dataclass(frozen=True)
class Group:
    name: str
    instruments: list[Instrument]


@dataclass(frozen=True)
class CalendarConfig:
    enabled: bool = True
    currencies: list[str] = field(default_factory=lambda: ["USD"])
    impacts: list[str] = field(default_factory=lambda: ["High"])


@dataclass(frozen=True)
class Config:
    groups: list[Group]
    calendar: CalendarConfig


def load_config(path: str | Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    groups: list[Group] = []
    for g in data["groups"]:
        instruments = [Instrument(**i) for i in g["instruments"]]
        groups.append(Group(name=g["name"], instruments=instruments))

    cal_raw = data.get("calendar") or {}
    calendar = CalendarConfig(
        enabled=cal_raw.get("enabled", True),
        currencies=cal_raw.get("currencies", ["USD"]),
        impacts=cal_raw.get("impacts", ["High"]),
    )

    return Config(groups=groups, calendar=calendar)
