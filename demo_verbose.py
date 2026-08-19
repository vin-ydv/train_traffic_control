from engine.simulation import Simulation

sim = Simulation.new('rajdhani_delay', mode='ai')

for i in range(120):
    sim.step()
    confs = sim.upcoming_conflicts(10)
    rec = sim.current_recommendation()
    if confs:
        print(f"T+{sim.time}m: upcoming_conflicts -> {confs}")
    if rec:
        print(f"T+{sim.time}m: recommendation -> {rec}")
        break
    # also list trains that are ready (at_station, dwell_left<=0, extra_hold<=0)
    ready = [t.number for t in sim.trains if t.at_station and t.dwell_left<=0 and t.extra_hold<=0 and not t.finished]
    if ready:
        print(f"T+{sim.time}m: ready trains -> {ready}")

print('Final KPIs:', sim.kpis())
print('Team brief:', sim.team_brief())
