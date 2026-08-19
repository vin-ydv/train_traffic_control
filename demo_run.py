"""Demo: run 'rajdhani_delay' scenario, detect conflict, apply AI recommendation, and show KPIs."""
from engine.simulation import Simulation, compare


def run_demo():
    sim = Simulation.new("rajdhani_delay", mode="ai")
    print(f"Starting demo for scenario: {sim.scenario_id} (mode={sim.mode})")

    # advance until a recommendation appears or 60 minutes
    rec = None
    for _ in range(60):
        sim.step()
        rec = sim.current_recommendation()
        if rec:
            print(f"T+{sim.time}m — Recommendation found:")
            print(rec)
            break
    if not rec:
        print("No recommendation found within 60 minutes. Current KPIs:")
        print(sim.kpis())
        return

    # show upcoming conflicts
    print("Upcoming conflicts (lookahead):", sim.upcoming_conflicts(20))

    # snapshot KPIs before applying
    k_before = sim.kpis()
    print("KPIs before applying recommendation:")
    print(k_before)

    # apply recommendation (hold other trains)
    for hid in rec.get("hold", []):
        t = sim._train(hid)
        if t:
            t.extra_hold += 2
            print(f"Applied extra_hold +2 to {t.number}")

    # step forward 20 minutes to observe impact
    for _ in range(20):
        sim.step()

    k_after = sim.kpis()
    print("KPIs after applying recommendation and 20 minutes progress:")
    print(k_after)

    # show final team brief
    print("Final team brief:")
    print(sim.team_brief())


if __name__ == '__main__':
    run_demo()
