from __future__ import annotations

from dataclasses import dataclass
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


def load_groups(path: str | Path) -> list[Group]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    groups: list[Group] = []
    for g in data["groups"]:
        instruments = [Instrument(**i) for i in g["instruments"]]
        groups.append(Group(name=g["name"], instruments=instruments))
    return groups
