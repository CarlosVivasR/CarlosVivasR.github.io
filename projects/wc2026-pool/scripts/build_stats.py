#!/usr/bin/env python3
"""Build data/stats.json for the Datos page (team rankings, best XI by real position,
most valuable players, top scorers, top clubs) + merge FIFA ranking."""
import json, os
from collections import Counter

idx = json.load(open('data/teams/index.json'))['teams']
agg = json.load(open('data/teams/aggregates.json'))
fifa = json.load(open('data/fifa_ranking.json'))['ranks']
team_meta = {t['code']: t for t in idx}

players = []
for t in idx:
    code = t['code']; fp = f'data/teams/{code}.json'
    if not os.path.exists(fp): continue
    for pl in json.load(open(fp))['players']:
        rec = {'name': pl['name'], 'team': code, 'flag': t['flag'], 'club': pl.get('club') or '',
               'pos': pl.get('pos') or '', 'pid': pl.get('pid'), 'sub': None,
               'value': None, 'age': None, 'caps': None, 'goals': None}
        pid = pl.get('pid')
        if pid and os.path.exists(f'data/players/{pid}.json'):
            pf = json.load(open(f'data/players/{pid}.json'))
            rec['sub'] = pf.get('sub_position') or pf.get('position')
            rec['value'] = pf.get('market_value_eur')
            rec['age'] = pf.get('age'); rec['caps'] = pf.get('caps'); rec['goals'] = pf.get('intl_goals')
        players.append(rec)

valued = [p for p in players if p['value']]
def slim(p): return {'name': p['name'], 'team': p['team'], 'flag': p['flag'], 'club': p['club'],
                      'value': p['value'], 'pos': p['pos'], 'sub': p['sub'], 'pid': p['pid'],
                      'goals': p['goals'], 'caps': p['caps']}

# ---- top clubs ----
cc = Counter(p['club'] for p in players if p['club'])
top_clubs = [{'club': c, 'n': n} for c, n in cc.most_common(14)]

# ---- most valuable players / top scorers ----
top_players = [slim(p) for p in sorted(valued, key=lambda p: -p['value'])[:24]]
scorers = [p for p in players if p['goals'] is not None]
top_scorers = [slim(p) for p in sorted(scorers, key=lambda p: (-(p['goals'] or 0), -(p['caps'] or 0)))[:16]]

# ---- best XI by REAL position (4-3-3), each player on their natural side ----
used = set()
def best(subs):
    pool = sorted([p for p in valued if p['sub'] in subs and p['pid'] not in used], key=lambda p: -p['value'])
    if not pool: return None
    used.add(pool[0]['pid']); return slim(pool[0])
gk  = best({'Goalkeeper'})
lb  = best({'Left-Back'});  rb  = best({'Right-Back'})
cb1 = best({'Centre-Back'}); cb2 = best({'Centre-Back'})
lw  = best({'Left Winger', 'Left Midfield'})
rw  = best({'Right Winger', 'Right Midfield'})
cf  = best({'Centre-Forward', 'Second Striker'})
# midfield: 3 best central; most valuable centred
midpool = sorted([p for p in valued if p['sub'] in {'Defensive Midfield', 'Central Midfield', 'Attacking Midfield'}
                  and p['pid'] not in used], key=lambda p: -p['value'])[:3]
for m in midpool: used.add(m['pid'])
mids = [slim(m) for m in midpool]
mid_line = [mids[1], mids[0], mids[2]] if len(mids) == 3 else mids
best_xi = {
    'FW': [x for x in [lw, cf, rw] if x],     # left → centre → right
    'MF': mid_line,
    'DF': [x for x in [lb, cb1, cb2, rb] if x],
    'GK': [x for x in [gk] if x],
}

# ---- team rankings ----
def row(code):
    a = agg.get(code, {}); m = team_meta.get(code, {})
    return {'code': code, 'name': m.get('name'), 'flag': m.get('flag'), 'group': m.get('group'),
            'value': a.get('value_total'), 'age': a.get('age_avg'), 'caps': a.get('caps_total'),
            'fifa': fifa.get(code)}
rows = [row(c) for c in team_meta if agg.get(c)]
rank = {
    'value':       sorted(rows, key=lambda r: -(r['value'] or 0))[:12],
    'youngest':    sorted(rows, key=lambda r: (r['age'] or 99))[:8],
    'oldest':      sorted(rows, key=lambda r: -(r['age'] or 0))[:8],
    'experienced': sorted(rows, key=lambda r: -(r['caps'] or 0))[:8],
    'fifa':        sorted([{'code': c, 'name': team_meta[c]['name'], 'flag': team_meta[c]['flag'],
                            'group': team_meta[c]['group'], 'fifa': rk} for c, rk in fifa.items()],
                          key=lambda r: r['fifa']),
}

out = {'generated': '2026-06', 'fifaDate': '2026-04', 'teamRankings': rank,
       'topClubs': top_clubs, 'topPlayers': top_players, 'bestXI': best_xi, 'topScorers': top_scorers}
json.dump(out, open('data/stats.json', 'w'), ensure_ascii=False, indent=1)
print('stats.json OK · players', len(players), 'valued', len(valued))
print('XI FW:', [p['name']+' ('+(p['sub'] or '?')+')' for p in best_xi['FW']])
print('XI MF:', [p['name']+' ('+(p['sub'] or '?')+')' for p in best_xi['MF']])
print('XI DF:', [p['name']+' ('+(p['sub'] or '?')+')' for p in best_xi['DF']])
print('XI GK:', [p['name'] for p in best_xi['GK']])
