"""Custom conflict demo: place a high-priority and low-priority train on opposite sides of B3 and let AI decide."""
from engine.simulation import Simulation

sim = Simulation.new('normal', mode='ai')
# choose trains
high = sim._train('T1')  # high-prio down
low = sim._train('T10')  # low-prio up
blk = next((b for b in sim.net.blocks if b.id=='B3'), None)
print('Initial B3 occupied?', blk.occupant_up, blk.occupant_down)

# Place high at PWL ready to depart down -> wants B3
high.at_station = 'PWL'
high.last_station = 'FDB'
high.next_station = 'KSV'
high.dwell_left = 0
high.extra_hold = 0
high.entered_section = True

# Place low at KSV ready to depart up -> wants B3
low.at_station = 'KSV'
low.last_station = 'MTJ'
low.next_station = 'PWL'
low.dwell_left = 0
low.extra_hold = 0
low.entered_section = True

print('High ready:', high.number, 'priority', high.priority)
print('Low ready :', low.number, 'priority', low.priority)

# Ask AI for recommendation
rec = sim.current_recommendation()
print('Recommendation at setup:', rec)

# Now step once (simulate release decision)
sim.step()

# After step, check who entered B3
print('After step, B3 occupants:', blk.occupant_up, blk.occupant_down)
print('High on_block:', high.on_block, 'at_station:', high.at_station)
print('Low on_block:', low.on_block, 'at_station:', low.at_station)
print('KPIs:', sim.kpis())
