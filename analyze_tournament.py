"""
Tournament Analysis: Generate detailed rankings and metrics (new CSV format).
Works with single-row-per-pairing CSV format.
"""

import csv
import sys
from pathlib import Path
from statistics import stdev, mean

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
CYAN = "\033[96m"
RESET = "\033[0m"

csv_path = Path("results/tournament_10092026-161309_rounds100_unknown-horizon.csv")

if not csv_path.exists():
    print(f"{RED}Error: CSV file not found at {csv_path}{RESET}")
    sys.exit(1)

# Load CSV
rows = []
with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Detect CSV format (old or new)
if rows and 'agent_a' not in rows[0]:
    # Old format - convert to new format
    print(f"{YELLOW}Converting old CSV format to new format...{RESET}\n")
    new_rows = []
    processed_pairings = set()

    for row in rows:
        pairing = tuple(sorted([row['agent_name'], row['opponent_name']]))
        if pairing not in processed_pairings:
            # Find both perspectives of this pairing
            agent_a_name = row['agent_name']
            agent_b_name = row['opponent_name']

            # Find agent_a perspective
            perspective_a = None
            perspective_b = None
            for r in rows:
                if r['agent_name'] == agent_a_name and r['opponent_name'] == agent_b_name:
                    perspective_a = r
                if r['agent_name'] == agent_b_name and r['opponent_name'] == agent_a_name:
                    perspective_b = r

            if perspective_a and perspective_b:
                # Convert old format to new
                new_rows.append({
                    'pairing_id': perspective_a['pairing_id'],
                    'num_rounds': perspective_a['num_rounds'],
                    'agent_a': agent_a_name,
                    'agent_b': agent_b_name,
                    'agent_a_points': float(perspective_a['points_scored']),
                    'agent_b_points': float(perspective_b['points_scored']),
                    'agent_a_first_move_cooperate': perspective_a['first_move_cooperate'] == 'True',
                    'agent_a_total_cooperations': float(perspective_a['total_cooperations']),
                    'agent_a_total_defections': float(perspective_a['total_defections']),
                    'agent_a_cooperate_after_opponent_cooperate': float(perspective_a['cooperate_after_opponent_cooperate']),
                    'agent_a_defect_after_opponent_cooperate': float(perspective_a['defect_after_opponent_cooperate']),
                    'agent_a_cooperate_after_opponent_defect': float(perspective_a['cooperate_after_opponent_defect']),
                    'agent_a_defect_after_opponent_defect': float(perspective_a['defect_after_opponent_defect']),
                    'agent_b_first_move_cooperate': perspective_b['first_move_cooperate'] == 'True',
                    'agent_b_total_cooperations': float(perspective_b['total_cooperations']),
                    'agent_b_total_defections': float(perspective_b['total_defections']),
                    'agent_b_cooperate_after_opponent_cooperate': float(perspective_b['cooperate_after_opponent_cooperate']),
                    'agent_b_defect_after_opponent_cooperate': float(perspective_b['defect_after_opponent_cooperate']),
                    'agent_b_cooperate_after_opponent_defect': float(perspective_b['cooperate_after_opponent_defect']),
                    'agent_b_defect_after_opponent_defect': float(perspective_b['defect_after_opponent_defect']),
                })
                processed_pairings.add(pairing)

    rows = new_rows

# Convert numeric fields
for row in rows:
    for key in row:
        if 'points' in key or 'cooperat' in key or 'defect' in key:
            try:
                row[key] = float(row[key])
            except (ValueError, TypeError):
                if row[key] in ('True', 'False'):
                    row[key] = row[key] == 'True'

agents = sorted({r['agent_a'] for r in rows} | {r['agent_b'] for r in rows})
metrics = {}

for agent in agents:
    agent_rows = []

    # Collect all matches involving this agent
    for row in rows:
        if row['agent_a'] == agent:
            agent_rows.append({
                'opponent': row['agent_b'],
                'points': row['agent_a_points'],
                'opponent_points': row['agent_b_points'],
                'cooperations': row['agent_a_total_cooperations'],
                'defections': row['agent_a_total_defections'],
                'first_move_cooperate': row['agent_a_first_move_cooperate'],
                'cooperate_after_opponent_cooperate': row['agent_a_cooperate_after_opponent_cooperate'],
                'defect_after_opponent_cooperate': row['agent_a_defect_after_opponent_cooperate'],
                'cooperate_after_opponent_defect': row['agent_a_cooperate_after_opponent_defect'],
                'defect_after_opponent_defect': row['agent_a_defect_after_opponent_defect'],
            })
        elif row['agent_b'] == agent:
            agent_rows.append({
                'opponent': row['agent_a'],
                'points': row['agent_b_points'],
                'opponent_points': row['agent_a_points'],
                'cooperations': row['agent_b_total_cooperations'],
                'defections': row['agent_b_total_defections'],
                'first_move_cooperate': row['agent_b_first_move_cooperate'],
                'cooperate_after_opponent_cooperate': row['agent_b_cooperate_after_opponent_cooperate'],
                'defect_after_opponent_cooperate': row['agent_b_defect_after_opponent_cooperate'],
                'cooperate_after_opponent_defect': row['agent_b_cooperate_after_opponent_defect'],
                'defect_after_opponent_defect': row['agent_b_defect_after_opponent_defect'],
            })

    if not agent_rows:
        continue

    total_points = sum(r['points'] for r in agent_rows)
    points_list = [r['points'] for r in agent_rows]
    avg_points = mean(points_list)
    std_points = stdev(points_list) if len(points_list) > 1 else 0

    # vs self
    vs_self = [r for r in agent_rows if r['opponent'] == agent]
    points_vs_self = sum(r['points'] for r in vs_self)

    # vs others
    vs_others = [r for r in agent_rows if r['opponent'] != agent]
    avg_vs_others = mean([r['points'] for r in vs_others]) if vs_others else 0

    # Win/Tie/Loss
    wins = sum(1 for r in agent_rows if r['points'] > r['opponent_points'])
    ties = sum(1 for r in agent_rows if r['points'] == r['opponent_points'])
    losses = sum(1 for r in agent_rows if r['points'] < r['opponent_points'])
    win_rate = wins / len(agent_rows) if agent_rows else 0

    # Cooperation
    total_coop = sum(r['cooperations'] for r in agent_rows)
    total_def = sum(r['defections'] for r in agent_rows)
    coop_rate = total_coop / (total_coop + total_def) if (total_coop + total_def) > 0 else 0
    avg_coop = mean([r['cooperations'] for r in agent_rows]) if agent_rows else 0

    # Best/Worst
    best_row = max(agent_rows, key=lambda r: r['points'])
    worst_row = min(agent_rows, key=lambda r: r['points'])

    metrics[agent] = {
        'total_points': total_points,
        'avg_points': avg_points,
        'std_points': std_points,
        'matches': len(agent_rows),
        'points_vs_self': points_vs_self,
        'avg_vs_others': avg_vs_others,
        'wins': wins,
        'ties': ties,
        'losses': losses,
        'win_rate': win_rate,
        'avg_coop': avg_coop,
        'coop_rate': coop_rate,
        'best_opponent': best_row['opponent'],
        'best_points': best_row['points'],
        'worst_opponent': worst_row['opponent'],
        'worst_points': worst_row['points'],
    }

print(f"\n{CYAN}{'='*110}")
print(f"TOURNAMENT - RANKING BY TOTAL POINTS")
print(f"{'='*110}{RESET}\n")

ranking = sorted(metrics.items(), key=lambda x: x[1]['total_points'], reverse=True)

for i, (agent, m) in enumerate(ranking, 1):
    bar = "=" * int(m['total_points'] / 100)
    print(f"{GREEN}{i:2d}.{RESET} {agent:30s} {WHITE}{m['total_points']:7.0f}{RESET} pts " +
          f"({m['matches']:2d}m, avg {m['avg_points']:6.1f}, std={m['std_points']:5.2f}) {bar}")

print(f"\n{CYAN}{'='*110}")
print(f"POINTS VS SELF (self-play)")
print(f"{'='*110}{RESET}\n")

self_ranking = [(a, m) for a, m in metrics.items() if m['points_vs_self'] > 0]
self_ranking.sort(key=lambda x: x[1]['points_vs_self'], reverse=True)

for i, (agent, m) in enumerate(self_ranking, 1):
    if m['points_vs_self'] > 0:
        self_matches = len([r for r in rows if (r['agent_a'] == agent and r['agent_b'] == agent)])
        avg_self = m['points_vs_self'] / self_matches if self_matches > 0 else 0
        print(f"{i:2d}. {agent:30s} {WHITE}{m['points_vs_self']:7.0f}{RESET} pts total " +
              f"({self_matches} matches, avg {avg_self:.1f} per match)")

print(f"\n{CYAN}{'='*110}")
print(f"WIN RATE (Wins-Ties-Losses)")
print(f"{'='*110}{RESET}\n")

win_ranking = sorted(metrics.items(), key=lambda x: x[1]['win_rate'], reverse=True)
for i, (agent, m) in enumerate(win_ranking, 1):
    w, t, l = m['wins'], m['ties'], m['losses']
    wr = m['win_rate'] * 100
    print(f"{i:2d}. {agent:30s} {GREEN}{w:2d}W{RESET}-{YELLOW}{t:2d}T{RESET}-{RED}{l:2d}L{RESET}  " +
          f"({wr:5.1f}% win rate)")

print(f"\n{CYAN}{'='*110}")
print(f"CONSISTENCY (Standard Deviation of Points)")
print(f"{'='*110}{RESET}\n")

consistency = sorted(metrics.items(), key=lambda x: x[1]['std_points'])
print(f"{GREEN}MOST CONSISTENT (lowest variation):{RESET}")
for agent, m in consistency[:5]:
    print(f"  {agent:30s} std={m['std_points']:6.2f} (average: {m['avg_points']:6.1f})")

print(f"\n{RED}MOST INCONSISTENT (highest variation):{RESET}")
for agent, m in consistency[-5:]:
    print(f"  {agent:30s} std={m['std_points']:6.2f} (average: {m['avg_points']:6.1f})")

print(f"\n{CYAN}{'='*110}")
print(f"AVERAGE COOPERATION")
print(f"{'='*110}{RESET}\n")

coop_ranking = sorted(metrics.items(), key=lambda x: x[1]['coop_rate'], reverse=True)
for i, (agent, m) in enumerate(coop_ranking, 1):
    coop_pct = m['coop_rate'] * 100
    bar = "=" * int(coop_pct / 5)
    print(f"{i:2d}. {agent:30s} {coop_pct:5.1f}% cooperation {bar}")

print(f"\n{CYAN}{'='*110}")
print(f"BEST AND WORST MATCHUPS (by points)")
print(f"{'='*110}{RESET}\n")

print(f"{GREEN}TOP 5 BEST RESULTS:{RESET}")
best_matchups = sorted(metrics.items(), key=lambda x: x[1]['best_points'], reverse=True)[:5]
for i, (agent, m) in enumerate(best_matchups, 1):
    print(f"{i}. {agent:30s} vs {m['best_opponent']:30s}: {m['best_points']:6.0f} points")

print(f"\n{RED}TOP 5 WORST RESULTS:{RESET}")
worst_matchups = sorted(metrics.items(), key=lambda x: x[1]['worst_points'])[:5]
for i, (agent, m) in enumerate(worst_matchups, 1):
    print(f"{i}. {agent:30s} vs {m['worst_opponent']:30s}: {m['worst_points']:6.0f} points")

print(f"\n{CYAN}{'='*110}")
print(f"WORST AGENTS RANKING")
print(f"{'='*110}{RESET}\n")

worst_ranking = sorted(metrics.items(), key=lambda x: x[1]['total_points'])
for i, (agent, m) in enumerate(worst_ranking, 1):
    print(f"{RED}{i:2d}.{RESET} {agent:30s} {m['total_points']:7.0f} pts " +
          f"({m['matches']:2d}m, avg {m['avg_points']:6.1f})")

print(f"\n{CYAN}{'='*110}")
print(f"GLOBAL STATISTICS SUMMARY")
print(f"{'='*110}{RESET}\n")

total_agents = len(agents)
total_points_all = sum(m['total_points'] for m in metrics.values())
avg_points_per_agent = total_points_all / total_agents

print(f"Total agents:                  {WHITE}{total_agents}{RESET}")
print(f"Total tournament points:       {WHITE}{total_points_all:.0f}{RESET}")
print(f"Average points per agent:      {WHITE}{avg_points_per_agent:.1f}{RESET}")

leader = ranking[0]
loser = worst_ranking[0]
print(f"\n{GREEN}[CHAMPION]      {leader[0]:28s} {leader[1]['total_points']:7.0f} points{RESET}")
print(f"{RED}[LAST PLACE]    {loser[0]:28s} {loser[1]['total_points']:7.0f} points{RESET}")

diff = leader[1]['total_points'] - loser[1]['total_points']
print(f"{YELLOW}Difference:     {diff:7.0f} points{RESET}")

print(f"\n{CYAN}{'='*110}{RESET}\n")
