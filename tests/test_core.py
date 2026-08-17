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


def test_team_brief_reports_dispatch_context():
    sim = Simulation.new("normal", mode="ai")
    brief = sim.team_brief()
    assert brief["risk_level"] in {"Low", "Moderate", "High"}
    assert isinstance(brief["summary"], str)
    assert brief["in_conflict"] in {True, False}


def test_forecast_window_and_reasoning():
    sim = Simulation.new("normal", mode="ai")
    rec = sim.current_recommendation()
    if rec:
        assert sim.release_explanation(sim._train(rec["release"]), [sim._train(h) for h in rec["hold"] if sim._train(h)])
    forecast = sim.forecast_window(5)
    assert isinstance(forecast, list)


def test_what_if_analysis() -> None:
    sim = Simulation.new("normal", mode="ai")
    analysis = sim.evaluate_what_if(train_number="12956", hold_minutes=5)
    assert "delay_delta_min" in analysis
    assert isinstance(analysis["summary"], str)
    assert "baseline" in analysis and "candidate" in analysis
