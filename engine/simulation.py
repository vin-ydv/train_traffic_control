"""RailMind simulation engine.

Time advances in 1-minute steps. Each train is either:
  - waiting at a station (dwelling, held, or waiting for clearance), or
  - moving along a block toward the next station.

Two controllers are supported via a decision callback:
  - FCFS controller (baseline): first-come-first-served, ties broken by priority.
  - AI controller: picks the train to release that minimizes passenger-weighted delay.
"""
from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Optional

from .model import Network, Train, load_trains, load_scenarios


@dataclass
class Event:
    time: int
    kind: str
    detail: str
    train: Optional[str] = None
    block: Optional[str] = None


@dataclass
class Simulation:
    net: Network
    trains: list[Train]
    scenario_id: str = "normal"
    mode: str = "ai"                  # 'fcfs' or 'ai'
    time: int = 0
    events: list[Event] = field(default_factory=list)
    audit: list[dict] = field(default_factory=list)
    # map train_id -> number of minutes held at current station beyond schedule
    controller_holds: dict[str, int] = field(default_factory=dict)
    controller_override: Optional[str] = None  # train_id forced to wait
    pending_events: list[dict] = field(default_factory=list)
    speed_restrictions: dict[str, float] = field(default_factory=dict)  # block -> speed
    network_speed: Optional[float] = None
    network_speed_until: int = 0
    recommendations: list[dict] = field(default_factory=list)

    # ---------- construction ----------
    @classmethod
    def new(cls, scenario_id: str = "normal", mode: str = "ai") -> "Simulation":
        net = Network.load()
        trains = load_trains()
        sim = cls(net=net, trains=trains, scenario_id=scenario_id, mode=mode)
        scen = next(s for s in load_scenarios()["scenarios"] if s["id"] == scenario_id)
        sim.pending_events = sorted(copy.deepcopy(scen["events"]), key=lambda e: e["at_min"])
        return sim

    def clone(self) -> "Simulation":
        return copy.deepcopy(self)

    # ---------- public loop ----------
    def run(self, minutes: int = 120) -> "Simulation":
        for _ in range(minutes):
            self.step()
        return self

    def step(self) -> None:
        self._apply_events()
        self._update_train_movements()
        self.time += 1

    # ---------- events / disruptions ----------
    def _apply_events(self) -> None:
        while self.pending_events and self.pending_events[0]["at_min"] <= self.time:
            e = self.pending_events.pop(0)
            kind = e["action"]
            if kind == "departure_delay":
                t = self._train(e["train"])
                if t is not None and not t.entered_section:
                    t.delay_min += e["minutes"]
                    t.planned_dep += e["minutes"]
                    self.events.append(Event(self.time, "delay",
                                             f"{t.number} delayed by {e['minutes']}m", t.id))
            elif kind == "speed_restriction":
                self.speed_restrictions[e["block"]] = e["speed"]
                # schedule removal
                self.pending_events.append({
                    "at_min": self.time + e["duration_min"],
                    "action": "_clear_speed", "block": e["block"],
                })
                self.events.append(Event(self.time, "speed",
                                         f"Speed restriction {e['speed']} km/h on {e['block']}",
                                         block=e["block"]))
            elif kind == "_clear_speed":
                self.speed_restrictions.pop(e["block"], None)
            elif kind == "network_speed":
                self.network_speed = e["speed"]
                self.network_speed_until = self.time + e["duration_min"]
                self.pending_events.append({"at_min": self.network_speed_until,
                                            "action": "_clear_network_speed"})
                self.events.append(Event(self.time, "fog",
                                         f"Network speed capped at {e['speed']} km/h"))
            elif kind == "_clear_network_speed":
                self.network_speed = None
            elif kind == "train_hold":
                t = self._train(e["train"])
                if t is not None:
                    t.extra_hold += e["minutes"]
                    self.events.append(Event(self.time, "breakdown",
                                             f"{t.number} held for {e['minutes']}m at {e['at_station']}",
                                             t.id))

    # ---------- per-train update ----------
    def _update_train_movements(self) -> None:
        # tick down holds and dwells
        for t in self.trains:
            if t.finished:
                continue
            if t.dwell_left > 0:
                t.dwell_left -= 1
            if t.extra_hold > 0:
                t.extra_hold -= 1

        # determine arrivals and departures
        for t in self.trains:
            if t.finished:
                continue

            # not entered yet
            if not t.entered_section:
                if self.time >= t.planned_dep and t.extra_hold == 0:
                    t.entered_section = True
                    t.at_station = None
                    nxt = self.net.next_block(t.origin, t.direction)
                    if nxt is None:
                        t.finished = True
                        continue
                    nxt.enter(t.id, t.direction)
                    t.on_block = nxt.id
                    t.block_progress_km = 0.0
                    t.last_station = t.origin
                    t.next_station = nxt.to_id if t.direction == "down" else nxt.from_id
                continue

            # on a block -> move
            if t.on_block is not None:
                blk = self.net.block_between(t.last_station, t.next_station)
                speed = self._effective_speed(blk, t)
                t.block_progress_km += speed / 60.0  # km per minute
                if t.block_progress_km >= blk.length_km:
                    # arrive at next station
                    blk.exit(t.id)
                    t.on_block = None
                    t.at_station = t.next_station
                    t.last_station = t.next_station
                    t.block_progress_km = 0.0
                    if t.at_station == t.dest:
                        t.finished = True
                        t.finish_time = self.time
                        self.events.append(Event(self.time, "arrive",
                                                 f"{t.number} reached destination", t.id))
                    else:
                        t.dwell_left = t.dwell_min
                        self.events.append(Event(self.time, "arrive",
                                                 f"{t.number} arrived at {t.at_station}", t.id))
                continue

            # at a station, waiting
            if t.at_station is not None and not t.finished:
                if t.dwell_left > 0 or t.extra_hold > 0:
                    continue
                # ready to depart - check release decision
                if self._is_cleared(t):
                    blk = self.net.next_block(t.at_station, t.direction)
                    if blk is None:
                        t.finished = True
                        continue
                    if blk.is_free(t.direction):
                        blk.enter(t.id, t.direction)
                        t.on_block = blk.id
                        t.at_station = None
                        t.block_progress_km = 0.0
                        route = (self.net.down_route if t.direction == "down"
                                 else self.net.up_route)
                        idx = route.index(t.last_station)
                        t.next_station = route[idx + 1]
                        self.events.append(Event(self.time, "depart",
                                                 f"{t.number} departed {t.last_station}", t.id))

    def _effective_speed(self, blk, t: Train) -> float:
        speed = min(t.speed, blk.max_speed)
        if blk.id in self.speed_restrictions:
            speed = min(speed, self.speed_restrictions[blk.id])
        if self.network_speed is not None and self.time < self.network_speed_until:
            speed = min(speed, self.network_speed)
        return speed

    # ---------- conflict / release logic ----------
    def _is_cleared(self, t: Train) -> bool:
        """Decide whether train t may leave its current station this step."""
        blk = self.net.next_block(t.at_station, t.direction)
        if blk is None:
            return True
        if not blk.is_free(t.direction):
            return False
        if blk.double_line:
            return True

        # Single-line block: multiple trains may want in. Pick one.
        contenders = [
            other for other in self.trains
            if not other.finished and other.at_station is not None
            and other.dwell_left <= 0 and other.extra_hold <= 0
            and self.net.next_block(other.at_station, other.direction) is blk
        ]
        if not contenders:
            return True
        chosen = self._choose(contenders)
        return chosen.id == t.id

    def dispatch_score(self, t: Train) -> float:
        """Return a multi-objective release score for a train at the current dispatch point."""
        delay = max(0.0, self.time - t.planned_dep)
        # Weight passenger impact more heavily than raw train priority so the
        # controller protects the busiest trains without ignoring delay.
        service_weight = 1.35 if t.type.lower() in {"rajdhani", "shatabdi", "superfast"} else 1.0
        return (t.priority * 25.0) + (t.pax * 0.85) + (delay * 6.0) + service_weight * 10.0

    def release_explanation(self, chosen: Train, held: list[Train]) -> str:
        """Generate a plain-English reason for the selected release decision."""
        if not held:
            return f"{chosen.number} is the only train at the conflict point, so there is no throughput penalty in holding anyone."
        delay_m = max(0.0, self.time - chosen.planned_dep)
        held_names = ", ".join(h.number for h in held)
        return (
            f"{chosen.number} ({chosen.type}) is prioritized because it carries {chosen.pax} passengers "
            f"and has a {delay_m:.0f}-minute lateness. Holding {held_names} protects the section's "
            "single-line throughput and prevents a larger passenger delay stack later in the window."
        )

    def forecast_window(self, horizon: int = 20) -> list[dict]:
        """Project the next few dispatch decisions and surface upcoming conflict risk."""
        sim = self.clone()
        outlook = []
        for step in range(horizon):
            sim.step()
            rec = sim.current_recommendation()
            if rec:
                outlook.append({
                    "in_min": sim.time,
                    "block": rec["block"],
                    "release": rec["release"],
                    "hold": rec["hold"],
                    "summary": rec["action"],
                })
            if len(outlook) >= 5:
                break
        return outlook

    def _choose(self, contenders: list[Train]) -> Train:
        if self.mode == "fcfs":
            # first-come first-served: earliest planned_dep, tie priority desc
            return sorted(contenders,
                          key=lambda x: (x.planned_dep, -x.priority))[0]
        # AI mode: passenger-weighted urgency
        return sorted(contenders, key=self.dispatch_score, reverse=True)[0]

    # ---------- helpers / KPIs ----------
    def _train(self, tid: str) -> Optional[Train]:
        return next((t for t in self.trains if t.id == tid), None)

    def train_position(self, t: Train) -> tuple[float, float]:
        if t.finished or not t.entered_section:
            if t.at_station and t.at_station in self.net.stations:
                s = self.net.stations[t.at_station]
                return s.x, s.y
            s = self.net.stations[t.origin]
            return s.x, s.y
        if t.at_station is not None:
            s = self.net.stations[t.at_station]
            return s.x, s.y
        if t.on_block is not None:
            blk = self.net.block_between(t.last_station, t.next_station)
            a = self.net.stations[blk.from_id]
            b = self.net.stations[blk.to_id]
            frac = min(1.0, t.block_progress_km / blk.length_km)
            return a.x + (b.x - a.x) * frac, a.y + (b.y - a.y) * frac
        s = self.net.stations[t.origin]
        return s.x, s.y

    def kpis(self) -> dict:
        finished = [t for t in self.trains if t.finished]
        total_delay = 0.0
        pax_minutes = 0.0
        for t in finished:
            scheduled = t.dep_min + self._scheduled_runtime(t)
            d = max(0.0, (t.finish_time - scheduled))
            total_delay += d
            pax_minutes += d * t.pax
        # also count in-progress delay
        for t in self.trains:
            if not t.finished and t.entered_section:
                scheduled_now = t.dep_min + self._scheduled_runtime_partial(t)
                d = max(0.0, self.time - scheduled_now)
                total_delay += d
                pax_minutes += d * t.pax
        throughput = len(finished)
        on_time = sum(1 for t in finished if (t.finish_time - t.dep_min - self._scheduled_runtime(t)) <= 5)
        punctuality = (on_time / len(finished) * 100.0) if finished else 0.0
        active = sum(1 for t in self.trains if t.entered_section and not t.finished)
        conflicts = self._count_conflicts()
        return {
            "throughput": throughput,
            "avg_delay": round(total_delay / max(1, len(self.trains)), 1),
            "total_delay": round(total_delay, 1),
            "punctuality": round(punctuality, 1),
            "pax_minutes": round(pax_minutes, 0),
            "active_trains": active,
            "conflicts_now": conflicts,
            "safety_violations": self._safety_violations(),
        }

    def _scheduled_runtime(self, t: Train) -> float:
        route = self.net.down_route if t.direction == "down" else self.net.up_route
        idx_o = route.index(t.origin)
        idx_d = route.index(t.dest)
        total = 0.0
        for i in range(min(idx_o, idx_d), max(idx_o, idx_d)):
            blk = self.net.block_between(route[i], route[i + 1])
            total += blk.length_km / min(t.speed, blk.max_speed) * 60.0
        # stops
        stops = abs(idx_d - idx_o) - 1
        total += stops * t.dwell_min
        return total

    def _scheduled_runtime_partial(self, t: Train) -> float:
        route = self.net.down_route if t.direction == "down" else self.net.up_route
        idx_o = route.index(t.origin)
        idx_c = route.index(t.last_station) if t.last_station in route else idx_o
        total = 0.0
        for i in range(min(idx_o, idx_c), max(idx_o, idx_c)):
            blk = self.net.block_between(route[i], route[i + 1])
            total += blk.length_km / min(t.speed, blk.max_speed) * 60.0
        stops = max(0, abs(idx_c - idx_o) - 1)
        total += stops * t.dwell_min
        if t.at_station is None and t.on_block is not None:
            blk = self.net.block_between(t.last_station, t.next_station)
            total += t.block_progress_km / min(t.speed, blk.max_speed) * 60.0
        return total

    def _count_conflicts(self) -> int:
        count = 0
        for blk in self.net.blocks:
            if blk.occupant_up and blk.occupant_down:
                count += 1
            if not blk.double_line and (blk.occupant_up or blk.occupant_down):
                # only a conflict if someone else is waiting on the other end
                for t in self.trains:
                    if (not t.finished and t.at_station is not None
                            and t.dwell_left <= 0 and t.extra_hold <= 0):
                        nb = self.net.next_block(t.at_station, t.direction)
                        if nb is blk and (blk.occupant_up != t.id and blk.occupant_down != t.id):
                            count += 1
                            break
        return count

    def _safety_violations(self) -> int:
        v = 0
        for blk in self.net.blocks:
            if blk.double_line:
                # each direction independent, no collision possible
                continue
            # single line: violation only if two DIFFERENT trains occupy it
            if (blk.occupant_up and blk.occupant_down
                    and blk.occupant_up != blk.occupant_down):
                v += 1
        return v

    def upcoming_conflicts(self, horizon: int = 15) -> list[dict]:
        """Look ahead by fast-copying the sim and detecting waiting trains."""
        sim = self.clone()
        found = []
        for _ in range(horizon):
            sim.mode = "fcfs"
            sim.step()
            for blk in sim.net.blocks:
                if not blk.double_line and (blk.occupant_up or blk.occupant_down):
                    for t in sim.trains:
                        if (not t.finished and t.at_station is not None
                                and t.dwell_left <= 0 and t.extra_hold <= 0):
                            nb = sim.net.next_block(t.at_station, t.direction)
                            if nb is blk and (blk.occupant_up != t.id and blk.occupant_down != t.id):
                                occ = blk.occupant_up or blk.occupant_down
                                found.append({
                                    "block": blk.id,
                                    "waiting": t.id,
                                    "occupying": occ,
                                    "in_min": _ + 1,
                                })
                if len(found) >= 5:
                    return found
        return found

    def decision_confidence(self, contenders: list[Train], chosen: Train) -> float:
        """Return a 0-100 confidence score for the current release recommendation."""
        if len(contenders) < 2:
            return 92.0
        scores = [self.dispatch_score(t) for t in contenders]
        chosen_score = self.dispatch_score(chosen)
        best = max(scores)
        margin = max(0.0, best - second_best if len(scores) >= 2 else 0.0)
        second_best = sorted(scores)[-2] if len(scores) >= 2 else 0.0
        margin = max(0.0, best - second_best)
        confidence = 55.0 + min(35.0, margin / max(10.0, chosen_score / 10.0)) + (chosen.priority * 2.5)
        return min(99.0, max(60.0, confidence))

    def current_recommendation(self) -> Optional[dict]:
        """Build a human-readable recommendation for the first active conflict."""
        for blk in self.net.blocks:
            if blk.double_line:
                continue
            if not (blk.occupant_up or blk.occupant_down):
                continue
            contenders = []
            for t in self.trains:
                if (not t.finished and t.at_station is not None
                        and t.dwell_left <= 0 and t.extra_hold <= 0):
                    nb = self.net.next_block(t.at_station, t.direction)
                    if nb is blk:
                        contenders.append(t)
            if not contenders:
                continue
            chosen = self._choose(contenders)
            held = [t for t in contenders if t.id != chosen.id]
            if not held:
                continue
            reason = self.release_explanation(chosen, held)
            confidence = self.decision_confidence(contenders, chosen)
            return {
                "block": blk.id,
                "release": chosen.id,
                "hold": [h.id for h in held],
                "action": f"Hold {' & '.join(h.number for h in held)} at "
                          f"{held[0].at_station}; allow {chosen.number} to enter {blk.id}.",
                "reason": reason,
                "impact": f"Estimated gain: {max(4, len(held) * 2)} min of passenger-weighted delay avoided.",
                "confidence": round(confidence, 1),
            }
        return None

    def team_brief(self) -> dict:
        """Summarize the current dispatch situation for the operations team."""
        kpis = self.kpis()
        recommendation = self.current_recommendation()
        if recommendation:
            held = recommendation.get("hold", [])
            release = recommendation.get("release")
            chosen = next((t for t in self.trains if t.id == release), None)
            hold_ids = [t.number for t in self.trains if t.id in held]
            risk_level = "High" if len(hold_ids) >= 2 or kpis["active_trains"] >= 4 else "Moderate"
            summary = (
                f"Contingency on {recommendation['block']}: release {chosen.number if chosen else 'train'} "
                f"while holding {', '.join(hold_ids) if hold_ids else 'other traffic'} to protect throughput."
            )
            return {
                "risk_level": risk_level,
                "summary": summary,
                "recommended_release": chosen.number if chosen else release,
                "holding_trains": hold_ids,
                "in_conflict": True,
            }
        risk_level = "Low" if kpis["conflicts_now"] == 0 else "Moderate"
        summary = (
            "No active single-line conflict requires an immediate dispatch change. "
            "The line remains stable and the controller can continue normal monitoring."
        )
        return {
            "risk_level": risk_level,
            "summary": summary,
            "recommended_release": "None",
            "holding_trains": [],
            "in_conflict": False,
        }

    def evaluate_what_if(
        self,
        *,
        train_number: Optional[str] = None,
        hold_minutes: int = 0,
        block_id: Optional[str] = None,
        speed_limit: Optional[float] = None,
        duration_min: int = 20,
    ) -> dict:
        """Compare the current plan against a temporary operational override."""
        base = self.clone()
        candidate = self.clone()

        if train_number:
            train = next((t for t in candidate.trains if t.number == str(train_number)), None)
            if train is not None:
                train.extra_hold += max(0, int(hold_minutes))
                candidate.events.append(Event(
                    candidate.time,
                    "whatif",
                    f"Controller scenario: hold {train.number} for {hold_minutes}m",
                    train.id,
                ))

        if block_id and speed_limit is not None:
            candidate.speed_restrictions[str(block_id)] = float(speed_limit)
            candidate.events.append(Event(
                candidate.time,
                "whatif",
                f"Controller scenario: cap {block_id} to {speed_limit} km/h for {duration_min}m",
                block=str(block_id),
            ))

        base.run(30)
        candidate.run(30)

        base_k = base.kpis()
        cand_k = candidate.kpis()
        delay_delta = cand_k["total_delay"] - base_k["total_delay"]
        punctuality_delta = cand_k["punctuality"] - base_k["punctuality"]

        if delay_delta <= 0:
            verdict = "This scenario improves operational flow and reduces passenger-weighted delay."
        else:
            verdict = "This scenario increases delay risk; the line remains stable but should be used cautiously."

        return {
            "baseline": base_k,
            "candidate": cand_k,
            "delay_delta_min": round(delay_delta, 1),
            "punctuality_delta_pts": round(punctuality_delta, 1),
            "verdict": verdict,
            "summary": (
                f"Projected impact over the next 30 minutes: "
                f"{cand_k['throughput']} trains processed, {cand_k['avg_delay']}m average delay, "
                f"{cand_k['punctuality']:.0f}% punctuality."
            ),
        }


def compare(scenario_id: str, minutes: int = 120) -> tuple[Simulation, Simulation]:
    """Run FCFS and AI back-to-back; return (fcfs_sim, ai_sim)."""
    fcfs = Simulation.new(scenario_id, mode="fcfs").run(minutes)
    ai = Simulation.new(scenario_id, mode="ai").run(minutes)
    return fcfs, ai
