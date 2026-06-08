#!/usr/bin/env python3
"""Scrape the marked starting XI (once titular) for all 48 teams from porraselsapo.site
and write data/xi_overrides.json (matched to our roster). Then run build_team_xi.py."""
import json, re, unicodedata, urllib.request, time, os

def strip(s):
    s=unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c)!='Mn').lower()
def norm(s): return re.sub(r'[^a-z0-9]','',strip(s))
def toks(s): return [t for t in (re.sub(r'[^a-z0-9]','',w) for w in strip(s).split()) if len(t)>=3]
POS={'POR':'GK','DEF':'DF','MED':'MF','DEL':'FW'}

def fetch(url):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=25).read().decode('utf-8','ignore')

ALT={'CUW':['cur'],'COD':['drc']}   # porraselsapo codes that differ from ours
# Korea: porraselsapo lists names in Western order → poor match; keep a manual reference XI
KOR_MANUAL={'GK':['Kim Seung-gyu'],'DF':['Lee Tae-seok','Kim Min-jae','Kim Tae-hyeon','Seol Young-woo'],
            'MF':['Hwang In-beom','Lee Jae-sung','Lee Kang-in'],'FW':['Son Heung-min','Oh Hyeon-gyu','Hwang Hee-chan']}
idx=json.load(open('data/teams/index.json'))['teams']

def match(name, roster, used):
    rn=norm(name); rt=set(toks(name))
    for p in roster:
        if p['pid'] in used: continue
        if norm(p['name'])==rn: return p
    best=None
    for p in roster:
        if p['pid'] in used: continue
        sh=rt & set(toks(p['name']))
        if sh and (any(len(x)>=4 for x in sh) or len(sh)>=2):
            sc=sum(len(x) for x in sh)
            if best is None or sc>best[0]: best=(sc,p)
    return best[1] if best else None

out={'_README':'Starting XIs scraped from porraselsapo.site/equipos/<code> (once titular). Matched to our roster. Rebuild: python3 scripts/build_team_xi.py ; regenerate: python3 scripts/build_lineups_sapo.py'}
rep=[]
for t in idx:
    code=t['code']
    if code=='KOR':
        out['KOR']=KOR_MANUAL; rep.append((code,'manual','11/11')); continue
    html=None
    for c in [code.lower()]+ALT.get(code,[]):
        try: html=fetch(f'https://porraselsapo.site/equipos/{c}'); break
        except Exception as e: err=str(e)[:30]
    if html is None: rep.append((code,'fetch-fail',err)); continue
    rows=re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S)
    xi=[]
    for r in rows:
        if '>XI</span>' not in r: continue
        nm=re.search(r'font-medium">([^<]+)</span>', r)
        ps=re.search(r'rounded[^>]*>\s*([A-Za-z]{2,4})\s*<', r)
        if nm and ps: xi.append((nm.group(1).strip(), POS.get(ps.group(1).upper(),'MF')))
    if len(xi)<11: rep.append((code,'incompleto',len(xi))); continue
    try: roster=json.load(open(f'data/teams/{code}.json'))['players']
    except: continue
    lines={'GK':[],'DF':[],'MF':[],'FW':[]}; used=set(); matched=0
    for nm,ln in xi:
        rp=match(nm, roster, used)
        if rp: lines[ln].append(rp['name']); used.add(rp['pid']); matched+=1
        else: lines[ln].append(nm)
    if matched<9: rep.append((code,'low-match',f'{matched}/11')); continue  # unreliable → keep heuristic
    out[code]=lines; rep.append((code,'ok',f'{matched}/11'))
    time.sleep(0.25)
json.dump(out, open('data/xi_overrides.json','w'), ensure_ascii=False, indent=1)
ok=[r for r in rep if r[1]=='ok']
print(f'Equipos con XI de porraselsapo: {len(ok)}/48')
bad=[r for r in rep if r[1]!='ok']
if bad: print('sin XI / fallos:', bad)
print('match flojo:', [r for r in ok if r[2]!='11/11'][:20])
