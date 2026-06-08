#!/usr/bin/env python3
"""Per-team probable XI (4-3-3) placed by real position → data/team_xi.json"""
import json, os, re
idx = json.load(open('data/teams/index.json'))['teams']
norm = lambda s: re.sub(r'[^a-z]', '', (s or '').lower())
try: OV = json.load(open('data/xi_overrides.json'))   # {code:{GK:[names],DF:[...],MF:[...],FW:[...]}}
except Exception: OV = {}

def pf(pid):
    fp = f'data/players/{pid}.json'
    return json.load(open(fp)) if pid and os.path.exists(fp) else {}

out = {}
for t in idx:
    code = t['code']; fp = f'data/teams/{code}.json'
    if not os.path.exists(fp): continue
    roster = json.load(open(fp))['players']
    pls = []
    for p in roster:
        d = pf(p.get('pid'))
        pls.append({'name': p['name'], 'pid': p.get('pid'), 'pos': p.get('pos') or '',
                    'club': p.get('club') or '', 'sub': d.get('sub_position') or d.get('position'),
                    'value': d.get('market_value_eur') or 0, 'caps': d.get('caps') or 0})
    def slim(p): return p and {'name': p['name'], 'pid': p['pid'], 'value': p['value']}
    # manual override (probable XI taken from reference sites), matched by name
    if code in OV:
        def by_name(nm):
            nn = norm(nm)
            for p in pls:
                if norm(p['name']) == nn: return p
            for p in pls:
                if nn and (nn in norm(p['name']) or norm(p['name']).endswith(nn)): return p
            return None
        o = OV[code]
        def fn(lst): return [slim(by_name(n)) for n in lst if by_name(n)]
        out[code] = {'GK': fn(o.get('GK', [])), 'DF': fn(o.get('DF', [])), 'MF': fn(o.get('MF', [])), 'FW': fn(o.get('FW', []))}
        continue
    used = set()
    # likely starter ≈ most international caps (then market value as tiebreaker)
    def take(cond):
        pool = sorted([p for p in pls if p['pid'] not in used and cond(p)], key=lambda p: (-p['caps'], -p['value']))
        if not pool: return None
        used.add(pool[0]['pid'] or pool[0]['name']); return pool[0]
    def sub_is(p, *names): return (p['sub'] or '') in names
    def line(prefix): return lambda p: p['pos'].endswith(prefix)
    # GK
    gk = take(line('GK'))
    # DF: LB, CB, CB, RB then fill to 4
    lb = take(lambda p: sub_is(p,'Left-Back')) 
    rb = take(lambda p: sub_is(p,'Right-Back'))
    cb1 = take(lambda p: sub_is(p,'Centre-Back')); cb2 = take(lambda p: sub_is(p,'Centre-Back'))
    df = [x for x in [lb, cb1, cb2, rb] if x]
    while len(df) < 4:
        x = take(line('DF'))
        if not x: break
        df.append(x)
    df = df[:4]
    # MF: 3 best central, fill
    mf = []
    for _ in range(3):
        x = take(lambda p: p['pos'].endswith('MF'))
        if x: mf.append(x)
    # FW: LW, CF, RW then fill to 3
    lw = take(lambda p: sub_is(p,'Left Winger','Left Midfield'))
    cf = take(lambda p: sub_is(p,'Centre-Forward','Second Striker'))
    rw = take(lambda p: sub_is(p,'Right Winger','Right Midfield'))
    fw = [x for x in [lw, cf, rw] if x]
    while len(fw) < 3:
        x = take(line('FW'))
        if not x: break
        fw.append(x)
    fw = fw[:3]
    def slim(p): return p and {'name': p['name'], 'pid': p['pid'], 'value': p['value']}
    # order DF as LB,CB,CB,RB already; ensure mf centred (highest value middle)
    mf_sorted = sorted(mf, key=lambda p:-p['value'])
    mf_line = [mf_sorted[1], mf_sorted[0], mf_sorted[2]] if len(mf_sorted)==3 else mf_sorted
    out[code] = {'GK':[slim(gk)] if gk else [], 'DF':[slim(x) for x in df],
                 'MF':[slim(x) for x in mf_line], 'FW':[slim(x) for x in fw]}

json.dump(out, open('data/team_xi.json','w'), ensure_ascii=False, indent=0)
print('team_xi.json OK ·', len(out), 'equipos')
print('Brasil XI:', '| FW', [p['name'] for p in out['BRA']['FW']], '| MF', [p['name'] for p in out['BRA']['MF']], '| DF', [p['name'] for p in out['BRA']['DF']], '| GK', [p['name'] for p in out['BRA']['GK']])
