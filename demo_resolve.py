"""Demonstration: find a conflict on block B3 in the 'rajdhani_delay' scenario,
compute AI's preferred release, apply holds to others, and compare KPIs before/after."""
from engine.simulation import Simulation


def resolve_demo():
    sim = Simulation.new('rajdhani_delay', mode='ai')
    # advance until we detect upcoming_conflicts mentioning B3 (or timeout)
    target_block = 'B3'
    found_at = None
    for _ in range(120):
        sim.step()
        confs = sim.upcoming_conflicts(10)
        for c in confs:
            if c.get('block') == target_block:
                found_at = sim.time
                print(f"Detected conflict for {target_block} at T+{sim.time}m: {c}")
                break
        if found_at is not None:
            break
    if found_at is None:
        print('No B3 conflict detected within 120 minutes')
        return

    # show trains that are ready and targeting B3 now
    contenders = [t for t in sim.trains if (not t.finished and t.at_station is not None
                    and t.dwell_left <= 0 and t.extra_hold <= 0
                    and sim.net.next_block(t.at_station, t.direction) is not None
                    and sim.net.next_block(t.at_station, t.direction).id == target_block)]
    print('Contenders for B3:', [(t.number, t.id, t.priority, t.pax) for t in contenders])

    # AI chooses
    chosen = sim._choose(contenders) if contenders else None
    print('AI would release:', (chosen.number if chosen else None))

    # KPIs before
    k_before = sim.kpis()
    print('KPIs before:', k_before)

    # apply holds to others
    held_ids = []
    if chosen:
        for t in contenders:
            if t.id != chosen.id:
                t.extra_hold += 3
                held_ids.append(t.number)
        print('Applied holds to:', held_ids)

    # step forward 30 minutes
    for _ in range(30):
        sim.step()

    k_after = sim.kpis()
    print('KPIs after 30 minutes:', k_after)
    print('Team brief:', sim.team_brief())

if __name__ == '__main__':
    resolve_demo()
