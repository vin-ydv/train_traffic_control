from engine.simulation import Simulation

sim = Simulation.new('rajdhani_delay', mode='ai')
# advance to when conflict appears (T+53 as seen earlier)
for _ in range(53):
    sim.step()
print('time', sim.time)
confs = sim.upcoming_conflicts(10)
print('confs', confs)
if confs:
    c = confs[0]
    wait_id = c['waiting']
    occ_id = c['occupying']
    print('waiting id', wait_id, 'occupying id', occ_id)
    w = sim._train(wait_id)
    o = sim._train(occ_id)
    print('waiting train state:', vars(w))
    print('occupying train state:', vars(o))
    # force waiting train to be ready at its station
    if w:
        w.dwell_left = 0
        w.extra_hold = 0
        print('Forced waiting train to be ready')
    # ensure occupying train remains on block (do not change)
    # check contenders now
    contenders = [t for t in sim.trains if (not t.finished and t.at_station is not None
                    and t.dwell_left <= 0 and t.extra_hold <= 0
                    and sim.net.next_block(t.at_station, t.direction) is not None
                    and sim.net.next_block(t.at_station, t.direction).id == c['block'])]
    print('contenders after forcing:', [(t.number,t.id) for t in contenders])
    if contenders:
        chosen = sim._choose(contenders)
        print('chosen', chosen.number)
        for t in contenders:
            if t.id!=chosen.id:
                t.extra_hold+=3
                print('applied hold to', t.number)
        # step forward a few minutes
        for _ in range(15):
            sim.step()
        print('KPIs after resolution attempt:', sim.kpis())
else:
    print('No conflicts')
