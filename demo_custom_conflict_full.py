"""Full custom conflict demo: set up opposing trains at B3, run until both clear, and show KPIs.
"""
from engine.simulation import Simulation

sim = Simulation.new('normal', mode='ai')
high = sim._train('T1')
low = sim._train('T10')
blk = next((b for b in sim.net.blocks if b.id=='B3'), None)

# Setup as before
high.at_station = 'PWL'
high.last_station = 'FDB'
high.next_station = 'KSV'
high.dwell_left = 0
high.extra_hold = 0
high.entered_section = True

low.at_station = 'KSV'
low.last_station = 'MTJ'
low.next_station = 'PWL'
low.dwell_left = 0
low.extra_hold = 0
low.entered_section = True

print('Before step — B3 occupants:', blk.occupant_up, blk.occupant_down)
print('Before — KPIs:', sim.kpis())

# Run until both trains have passed B3 (finished or moved beyond)
max_minutes = 60
for _ in range(max_minutes):
    sim.step()
    # break when both are not blocking B3 and low has progressed
    if not (blk.occupant_up or blk.occupant_down):
        # if both trains have moved beyond B3 (neither occupying it)
        print(f'B3 cleared at T+{sim.time}m')
        break

print('After run — B3 occupants:', blk.occupant_up, blk.occupant_down)
print('After — KPIs:', sim.kpis())
print('Train statuses:')
for tid in ['T1','T10']:
    t = sim._train(tid)
    print(t.number, 'on_block:', t.on_block, 'at_station:', t.at_station, 'finished:', t.finished)
