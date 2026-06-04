import json, os, glob
ROOT='.'
idx=json.load(open('data/teams/index.json'))['teams']
agg=json.load(open('data/teams/aggregates.json'))
team_meta={t['code']:t for t in idx}

players=[]
for t in idx:
    code=t['code']; fp=f'data/teams/{code}.json'
    if not os.path.exists(fp): continue
    roster=json.load(open(fp))
    for pl in roster['players']:
        rec={'name':pl['name'],'team':code,'flag':t['flag'],'club':pl.get('club') or '','pos':pl.get('pos') or '','pid':pl.get('pid'),
             'value':None,'age':None,'caps':None,'goals':None}
        pid=pl.get('pid')
        if pid and os.path.exists(f'data/players/{pid}.json'):
            pf=json.load(open(f'data/players/{pid}.json'))
            rec['value']=pf.get('market_value_eur')
            rec['age']=pf.get('age')
            rec['caps']=pf.get('caps')
            rec['goals']=pf.get('intl_goals')
        players.append(rec)

# top clubs by player count
from collections import Counter
cc=Counter(p['club'] for p in players if p['club'])
top_clubs=[{'club':c,'n':n} for c,n in cc.most_common(14)]

# most valuable players
valued=[p for p in players if p['value']]
top_players=sorted(valued,key=lambda p:-p['value'])[:24]
def slim(p): return {'name':p['name'],'team':p['team'],'flag':p['flag'],'club':p['club'],'value':p['value'],'pos':p['pos'],'pid':p['pid'],'goals':p['goals'],'caps':p['caps']}
top_players=[slim(p) for p in top_players]

# best XI by value (4-3-3): 1 GK, 4 DF, 3 MF, 3 FW
def topby(posprefix,n):
    pool=sorted([p for p in valued if p['pos'].endswith(posprefix)],key=lambda p:-p['value'])[:n]
    return [slim(p) for p in pool]
best_xi={'GK':topby('GK',1),'DF':topby('DF',4),'MF':topby('MF',3),'FW':topby('FW',3)}

# top scorers (intl goals)
scorers=[p for p in players if p['goals'] is not None]
top_scorers=[slim(p) for p in sorted(scorers,key=lambda p:(-(p['goals'] or 0),-(p['caps'] or 0)))[:16]]

# team rankings from aggregates
def team_row(code):
    a=agg.get(code,{}); m=team_meta.get(code,{})
    return {'code':code,'name':m.get('name'),'flag':m.get('flag'),'group':m.get('group'),
            'value':a.get('value_total'),'age':a.get('age_avg'),'caps':a.get('caps_total')}
rows=[team_row(c) for c in team_meta if agg.get(c)]
rank={
 'value':[r for r in sorted(rows,key=lambda r:-(r['value'] or 0))][:12],
 'youngest':[r for r in sorted(rows,key=lambda r:(r['age'] or 99))][:8],
 'oldest':[r for r in sorted(rows,key=lambda r:-(r['age'] or 0))][:8],
 'experienced':[r for r in sorted(rows,key=lambda r:-(r['caps'] or 0))][:8],
}

out={'generated':'2026-06','teamRankings':rank,'topClubs':top_clubs,'topPlayers':top_players,'bestXI':best_xi,'topScorers':top_scorers}
json.dump(out,open('data/stats.json','w'),ensure_ascii=False,indent=1)
print('stats.json escrito.')
print('  jugadores procesados:',len(players),'| con valor:',len(valued))
print('  top club:',top_clubs[0])
print('  jugador más valioso:',top_players[0]['name'],top_players[0]['value'])
print('  XI:',{k:[x['name'] for x in v] for k,v in best_xi.items()})
print('  top goleador:',top_scorers[0]['name'],top_scorers[0]['goals'])
