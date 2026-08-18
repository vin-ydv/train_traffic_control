"""Core data structures for the RailMind digital twin."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from db.models import ensure_db_ready, load_blocks_from_db, load_stations_from_db, load_trains_from_db

DATA = Path(__file__).resolve().parent.parent / "data"

PRIORITY_LABEL = {
    5: "Rajdhani/Shatabdi",
    4: "Superfast",
    3: "Express",
    2: "Passenger/MEMU",
    1: "Freight",
}

PRIORITY_COLOR = {
    5: "#ef4444",  # red
    4: "#3b82f6",  # blue
    3: "#22c55e",  # green
    2: "#a855f7",  # purple
    1: "#6b7280",  # grey
}


@dataclass
class Station:
    id: str
    name: str
    x: float
    y: float
    loops: int

    def label(self) -> str:
        return f"{self.id}\n{self.name}"


@dataclass
class Block:
    id: str
    from_id: str
    to_id: str
    length_km: float
    max_speed: float
    double_line: bool
    # occupancy: on double line one slot per direction; on single line, one slot total
    occupant_up: Optional[str] = None
    occupant_down: Optional[str] = None

    def is_free(self, direction: str) -> bool:
        if self.double_line:
            return self.occupant_up is None if direction == "up" else self.occupant_down is None
        # single line: exactly one train total, regardless of direction
        return self.occupant_up is None and self.occupant_down is None

    def enter(self, train_id: str, direction: str) -> None:
        if self.double_line:
            if direction == "up":
                self.occupant_up = train_id
            else:
                self.occupant_down = train_id
        else:
            # both up and down point at the same (single) slot
            self.occupant_up = train_id
            self.occupant_down = train_id

    def exit(self, train_id: str) -> None:
        if self.occupant_up == train_id:
            self.occupant_up = None
        if self.occupant_down == train_id:
            self.occupant_down = None


@dataclass
class Train:
    id: str
    number: str
    name: str
    direction: str            # 'up' or 'down'
    priority: int
    type: str
    pax: int
    speed: float
    origin: str
    dest: str
    dep_min: float
    dwell_min: float

    # runtime state
    entered_section: bool = False
    at_station: Optional[str] = None  # None means on a block
    on_block: Optional[str] = None
    block_progress_km: float = 0.0
    dwell_left: float = 0.0
    extra_hold: float = 0.0   # controller/AI-imposed hold at current station
    planned_dep: float = 0.0  # when it is allowed to leave current station
    delay_min: float = 0.0
    finished: bool = False
    finish_time: Optional[float] = None
    last_station: Optional[str] = None
    next_station: Optional[str] = None
    color: str = field(init=False)

    def __post_init__(self) -> None:
        self.color = PRIORITY_COLOR.get(self.priority, "#888")
        self.at_station = self.origin
        self.last_station = self.origin
        self.planned_dep = self.dep_min + self.delay_min


@dataclass
class Network:
    stations: dict[str, Station]
    blocks: list[Block]
    # down order from origin to dest, up reversed
    down_route: list[str] = field(default_factory=list)
    up_route: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path = DATA / "section.json") -> "Network":
        ensure_db_ready()
        db_stations = load_stations_from_db()
        db_blocks = load_blocks_from_db()
        if db_stations and db_blocks:
            raw = {"stations": db_stations, "blocks": db_blocks}
        else:
            raw = json.loads(path.read_text())
        stations = {s["id"]: Station(**s) for s in raw["stations"]}
        blocks = [
            Block(
                id=b["id"],
                from_id=b["from"],
                to_id=b["to"],
                length_km=b["length_km"],
                max_speed=b["max_speed"],
                double_line=b["double_line"],
            )
            for b in raw["blocks"]
        ]
        net = cls(stations=stations, blocks=blocks)
        net.down_route = [b.from_id for b in blocks] + [blocks[-1].to_id]
        net.up_route = list(reversed(net.down_route))
        return net

    def block_between(self, a: str, b: str) -> Optional[Block]:
        for blk in self.blocks:
            if (blk.from_id == a and blk.to_id == b) or (
                blk.from_id == b and blk.to_id == a
            ):
                return blk
        return None

    def next_block(self, station_id: str, direction: str) -> Optional[Block]:
        route = self.down_route if direction == "down" else self.up_route
        if station_id not in route:
            return None
        idx = route.index(station_id)
        if idx + 1 >= len(route):
            return None
        return self.block_between(route[idx], route[idx + 1])

    def block_xy(self, blk: Block) -> tuple[float, float, float, float]:
        a = self.stations[blk.from_id]
        b = self.stations[blk.to_id]
        return a.x, a.y, b.x, b.y


def load_trains(path: Path = DATA / "timetable.json") -> list[Train]:
    ensure_db_ready()
    db_trains = load_trains_from_db()
    if db_trains:
        return [Train(**t) for t in db_trains]
    raw = json.loads(path.read_text())
    return [Train(**t) for t in raw["trains"]]


def load_scenarios(path: Path = DATA / "scenarios.json") -> dict:
    return json.loads(path.read_text())
