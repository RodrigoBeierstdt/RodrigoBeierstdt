import json, re, html, urllib.request, datetime, os

OUT = os.path.join(os.path.dirname(__file__), 'rank.json')
RIOT_ID = 'todoxy#zuzu'
SLUG = 'todoxy-zuzu'
UA = {
    'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
    'Accept-Language':'pt-BR,pt;q=0.9,en;q=0.8'
}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode('utf-8', 'ignore')

def plain(s):
    s = re.sub(r'<script[\s\S]*?</script>', ' ', s, flags=re.I)
    s = re.sub(r'<style[\s\S]*?</style>', ' ', s, flags=re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()

def parse_text(t, source):
    tx = plain(t)
    needle = RIOT_ID.lower()
    pos = tx.lower().find(needle)
    area = tx[max(0,pos-350):pos+1100] if pos >= 0 else tx

    patterns = [
        r'\b(Challenger|GrandMaster|Grandmaster|Grão-Mestre|Grao-Mestre|Master|Mestre|Diamond|Diamante|Emerald|Esmeralda|Platinum|Platina|Gold|Ouro|Silver|Prata|Bronze|Iron|Ferro)\b\s*(?:[IVX]+\s*)?([0-9][0-9.,]*)\s*(?:LP|Pontos na Liga)',
        r'\b(Challenger|GrandMaster|Grandmaster|Grão-Mestre|Grao-Mestre|Master|Mestre)\b[^0-9]{0,45}([0-9][0-9.,]*)\s*(?:LP|Pontos na Liga)'
    ]
    m = None
    for pat in patterns:
        m = re.search(pat, area, re.I)
        if m: break
    if not m:
        raise ValueError('rank not found')

    tier_raw = m.group(1).lower()
    tier_map = {
        'grandmaster':'GrandMaster','grão-mestre':'GrandMaster','grao-mestre':'GrandMaster',
        'master':'Master','mestre':'Master','challenger':'Challenger',
        'diamond':'Diamond','diamante':'Diamond','emerald':'Emerald','esmeralda':'Emerald',
        'platinum':'Platinum','platina':'Platinum','gold':'Gold','ouro':'Gold',
        'silver':'Silver','prata':'Silver','bronze':'Bronze','iron':'Iron','ferro':'Iron'
    }
    tier = tier_map.get(tier_raw, m.group(1))
    lp = int(float(m.group(2).replace('.','').replace(',','.')))

    wins = losses = winrate = None
    wm = re.search(r'(?:Wins|Vitórias|Vitorias|W)\s*:?\s*(\d+)', area, re.I)
    lm = re.search(r'(?:Losses|Derrotas|L)\s*:?\s*(\d+)', area, re.I)
    if wm and lm:
        wins, losses = int(wm.group(1)), int(lm.group(1))
        if wins + losses:
            winrate = round(wins/(wins+losses)*100,1)

    return {
        'riot_id':RIOT_ID,'region':'BR','queue':'Solo/Duo','tier':tier,'lp':lp,
        'challenger':tier.lower()=='challenger','wins':wins,'losses':losses,'winrate':winrate,
        'source':source,'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ok'
    }

def fetch():
    sources = [
        ('LeagueOfGraphs','https://www.leagueofgraphs.com/summoner/br/' + SLUG),
        ('LeagueOfGraphs PT','https://www.leagueofgraphs.com/pt/summoner/br/' + SLUG),
        ('OP.GG','https://op.gg/pt/lol/summoners/br/' + SLUG),
        ('Jina + LeagueOfGraphs','https://r.jina.ai/http://www.leagueofgraphs.com/summoner/br/' + SLUG),
        ('Jina + OP.GG','https://r.jina.ai/http://op.gg/pt/lol/summoners/br/' + SLUG),
    ]
    errs=[]
    for name,url in sources:
        try:
            return parse_text(get(url), name)
        except Exception as e:
            errs.append(f'{name}: {e}')

    try:
        old=json.load(open(OUT,encoding='utf-8'))
    except Exception:
        old={'riot_id':RIOT_ID,'region':'BR','queue':'Solo/Duo','tier':'Indisponível','lp':None,'challenger':False}
    old['riot_id']=RIOT_ID
    old['status']='stale'
    old['error']=' | '.join(errs)[-1400:]
    old['checked_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    return old

if __name__ == '__main__':
    data=fetch()
    with open(OUT,'w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    print(json.dumps(data,ensure_ascii=False))
