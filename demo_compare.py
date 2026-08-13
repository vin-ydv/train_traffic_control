"""Run full 120-min comparison between FCFS and AI for 'rajdhani_delay' scenario and show KPIs."""
from engine.simulation import compare

fcfs, ai = compare('rajdhani_delay', minutes=120)
print('FCFS KPIs:', fcfs.kpis())
print('AI KPIs  :', ai.kpis())
print('\nDifferences (AI - FCFS):')
fb = fcfs.kpis(); ab = ai.kpis()
for k in ['throughput','avg_delay','punctuality','pax_minutes','total_delay']:
    print(k, ab[k] - fb[k])
