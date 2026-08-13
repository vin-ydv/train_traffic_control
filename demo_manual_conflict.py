"""Manual conflict demo: place two trains on opposite sides of B3, let AI recommend which to release."""
from engine.simulation import Simulation

sim = Simulation.new('normal', mode='ai')
# pick trains
train_A = sim._train('T3')  # we'll occupy B3 with T3 (down)
train_B = sim._train('T7')  # we'll place T7 at KSV (up) wanting to enter B3

blk = next((b for b in sim.net.blocks if b.id=='B3'), None)
if blk is None:
    raise SystemExit('B3 not found')

# Place T3 on block B3 occupying it in down direction
blk.enter(train_A.id, 'down')
train_A.on_block = blk.id
train_A.entered_section = True
train_A.at_station = None
train_A.last_station = 'PWL'
train_A.next_station = 'KSV'
train_A.block_progress_km = blk.length_km/2

# Place T7 at station KSV ready to depart (will want to enter B3 towards PWL)
train_B.at_station = 'KSV'
train_B.entered_section = True
train_B.on_block = None
train_B.last_station = 'MTJ'
train_B.next_station = 'PWL'
train_B.dwell_left = 0
train_B.extra_hold = 0

print('Initial state:')
print('Block B3 occupants:', blk.occupant_up, blk.occupant_down)
print('Train A (on block):', train_A.number, train_A.on_block)
print('Train B (at station):', train_B.number, train_B.at_station)

# Now ask AI for recommendation
rec = sim.current_recommendation()
print('Recommendation:', rec)

# If rec suggests releasing someone, apply holds and step forward
if rec and rec.get('hold'):
    for hid in rec['hold']:
        t = sim._train(hid)
        if t:
            t.extra_hold += 3
            print('Applied hold to', t.number)

# step a few minutes
for i in range(10):
    sim.step()

print('KPIs after applying AI decision and 10 mins:')
print(sim.kpis())
print('Team brief:', sim.team_brief())
