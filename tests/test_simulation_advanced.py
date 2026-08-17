import pytest
from engine.model import Train, Station, Block
from engine.simulation import Simulation, Event


def test_train_model_initialization():
    t = Train(
        id="T1",
        number="12951",
        name="Test Express",
        direction="up",
        priority=1,
        type="Express",
        pax=500,
        speed=100.0,
        origin="S1",
        dest="S3",
        dep_min=0.0,
        dwell_min=2.0
    )
    assert t.id == "T1"
    assert t.priority == 1
    assert t.pax == 500


def test_station_and_block_models():
    s = Station(id="S1", name="Alpha", x=0.0, y=0.0, loops=2)
    assert s.id == "S1"
    assert s.loops == 2

    b = Block(id="B1", from_id="S1", to_id="S2", length_km=15.0, max_speed=110.0, double_line=False)
    assert b.id == "B1"
    assert b.double_line is False


def test_simulation_initialization_modes():
    sim_ai = Simulation.new("normal", mode="ai")
    assert sim_ai.mode == "ai"
    assert sim_ai.time == 0

    sim_fcfs = Simulation.new("normal", mode="fcfs")
    assert sim_fcfs.mode == "fcfs"


def test_simulation_step_advancement():
    sim = Simulation.new("normal", mode="ai")
    initial_time = sim.time
    sim.step()
    assert sim.time == initial_time + 1


def test_event_record():
    ev = Event(
        time=10,
        kind="HOLD",
        detail="Train held at station",
        train="T1",
        block="B1"
    )
    assert ev.train == "T1"
    assert ev.kind == "HOLD"
    assert ev.time == 10

