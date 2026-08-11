"""Run with:  pytest -q   (install pytest:  pip install pytest)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.simulation import Simulation, compare


def test_no_safety_violation_normal():
    sim = Simulation.new("normal", mode="ai").run(120)
    assert sim.kpis()["safety_violations"] == 0


def test_no_safety_violation_disruption():
    for sid in ["rajdhani_delay", "signal_fail", "freight_breakdown", "fog"]:
        sim = Simulation.new(sid, mode="ai").run(120)
        assert sim.kpis()["safety_violations"] == 0, sid


def test_ai_beats_or_matches_fcfs_on_delay():
    fcfs = Simulation.new("rajdhani_delay", mode="fcfs").run(120)
    ai = Simulation.new("rajdhani_delay", mode="ai").run(120)
    assert ai.kpis()["total_delay"] <= fcfs.kpis()["total_delay"] + 0.5


def test_compare_utility():
    fcfs, ai = compare("normal", minutes=60)
    assert isinstance(fcfs.kpis(), dict)
    assert isinstance(ai.kpis(), dict)


def test_disruption_injection_speed_and_fog():
    sim = Simulation.new("normal", mode="ai")
    sim.speed_restrictions["B4"] = 40
    sim.network_speed = 60
    sim.run(30)
    assert sim.kpis()["safety_violations"] == 0

