#!/usr/bin/env python3
"""Jersey numbers for all 48 WC2026 squads from Wikipedia (action=raw) → data/numbers.json
Output: { teamCode: { normalisedRosterName: number } } matched to our roster via token overlap."""
import json, re, unicodedata, urllib.request, os

def strip(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
def norm(s): return re.sub(r'[^a-z0-9]', '', strip(s))
def toks(s): return [re.sub(r'[^a-z0-9]','',w) for w in strip(s).split() if len(re.sub(r'[^a-z0-9]','',w))>=3]

URL = "https://en.wikipedia.org/w/index.php?title=2026_FIFA_World_Cup_squads&action=raw"
try:
    req = urllib.request.Request(URL, headers={'User-Agent': 'wc2026-build/1.0'})
    wt = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
except Exception:
    wt = open('/tmp/wc_squads.txt').read()

idx = json.load(open('data/teams/index.json'))['teams']
name2code = {t['name']: t['code'] for t in idx}
ALIAS = {'Korea Republic':'South Korea','Türkiye':'Turkey',"Côte d'Ivoire":'Ivory Coast','Cabo Verde':'Cape Verde'}

wiki = {}; cur = None  # code -> [(name, number)]
for line in wt.splitlines():
    h = re.match(r'^===\s*([^=].*?)\s*===\s*$', line)
    if h:
        nm = h.group(1).strip(); nm = ALIAS.get(nm, nm); cur = name2code.get(nm); continue
    if cur and 'nat fs' in line and 'player|' in line:
        no = re.search(r'\bno=(\d+)', line); nm = re.search(r'name=\[\[([^\]|]+)', line)
        if no and nm: wiki.setdefault(cur, []).append((nm.group(1), int(no.group(1))))

def match(rname, wlist, used):
    rn = norm(rname); rt = set(toks(rname))
    # 1) exact normalised
    for i,(wn,no) in enumerate(wlist):
        if i in used: continue
        if norm(wn)==rn: return i,no
    # 2) best token-overlap (score = total length of shared tokens), require a shared token len>=4 or 2 shared
    best=None
    for i,(wn,no) in enumerate(wlist):
        if i in used: continue
        wt_=set(toks(wn)); sh=rt & wt_
        if not sh: continue
        score=sum(len(x) for x in sh); strong=any(len(x)>=4 for x in sh) or len(sh)>=2
        if strong and (best is None or score>best[0]): best=(score,i,no)
    if best: return best[1],best[2]
    return None,None

out={}; tm=0; tp=0; weak=[]
for t in idx:
    code=t['code']; fp=f'data/teams/{code}.json'
    if not os.path.exists(fp): continue
    roster=json.load(open(fp))['players']; wl=wiki.get(code,[]); used=set(); m={}; matched=0
    for p in roster:
        i,no=match(p['name'], wl, used)
        if i is not None: used.add(i); m[norm(p['name'])]=no; matched+=1
    out[code]=m; tm+=matched; tp+=len(roster)
    if matched < len(roster)-2: weak.append((code,matched,len(roster)))
json.dump(out, open('data/numbers.json','w'), ensure_ascii=False, indent=0)
print(f'numbers.json OK · matched {tm}/{tp} ({100*tm//tp}%) en {len(out)} equipos')
if weak: print('bajo emparejamiento:', weak)
# show Brazil XI numbers
xi=json.load(open('data/team_xi.json'))['BRA']; nums=out['BRA']
print('Brasil XI dorsales:', [(p['name'], nums.get(norm(p['name']),'?')) for ln in ['GK','DF','MF','FW'] for p in xi[ln]])
