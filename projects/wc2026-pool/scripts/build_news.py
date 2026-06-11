#!/usr/bin/env python3
"""Pre-fetch Google News RSS (es/en/tr) server-side → data/news.json.
This is the always-available baseline the page shows instantly; the page still
refreshes live via CORS proxies on top. Re-run to refresh: python3 scripts/build_news.py"""
import json, re, html, time, email.utils, urllib.request
from urllib.parse import quote

FEEDS = {
    'es': ('Mundial 2026 FIFA', 'es-419', 'ES'),
    'en': ('World Cup 2026',     'en-US',  'US'),
    'tr': ('2026 Dünya Kupası',  'tr',     'TR'),
}

def fetch(q, hl, gl):
    url = f"https://news.google.com/rss/search?q={quote(q)}&hl={hl}&gl={gl}&ceid={gl}:{hl.split('-')[0]}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    xml = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'ignore')
    out = []
    for block in re.findall(r'<item>(.*?)</item>', xml, re.S)[:30]:
        def tag(t):
            m = re.search(rf'<{t}>(.*?)</{t}>', block, re.S)
            return m.group(1).strip() if m else ''
        title = html.unescape(re.sub(r'<[^>]+>', '', tag('title')))
        link  = tag('link')
        pub   = tag('pubDate')
        sm    = re.search(r'<source[^>]*>(.*?)</source>', block, re.S)
        src   = html.unescape(sm.group(1).strip()) if sm else ''
        if src and title.endswith(' - ' + src):
            title = title[:-(len(src) + 3)]
        try:
            date = int(email.utils.parsedate_to_datetime(pub).timestamp() * 1000)
        except Exception:
            date = 0
        if title and link:
            out.append({'title': title, 'link': link, 'src': src, 'date': date})
    return out

data = {'_generated': int(time.time() * 1000)}
for lang, (q, hl, gl) in FEEDS.items():
    try:
        data[lang] = fetch(q, hl, gl)
        print(f"{lang}: {len(data[lang])} headlines")
    except Exception as e:
        data[lang] = []
        print(f"{lang}: FAILED — {e}")

json.dump(data, open('data/news.json', 'w'), ensure_ascii=False, indent=0)
print("→ data/news.json written")
