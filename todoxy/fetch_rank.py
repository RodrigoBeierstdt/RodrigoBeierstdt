import json, re, html, urllib.request, datetime, os

OUT = os.path.join(os.path.dirname(__file__), 'rank.json')
UA = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}

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
    # Prefer the exact player's row / block when present.
    pos = tx.lower().find('xyd#zzzzz')
    area = tx[max(0,pos-250):pos+700] if pos >= 0 else tx
    m = re.search(r'\b(Challenger|GrandMaster|Grandmaster|Master|Diamond|Emerald|Platinum|Gold|Silver|Bronze|Iron)\b\s*(?:[IVX]+\s*)?([0-9][0-9.,]*)\s*(?:LP|League points|League punten|Ligapontok)', area, re.I)
    if not m:
        m = re.search(r'\b(Challenger|GrandMaster|Grandmaster|Master)\b[^0-9]{0,40}([0-9][0-9.,]*)\s*LP', area, re.I)
    if not m:
        raise ValueError('rank not found')
    tier = m.group(1)
    if tier.lower() == 'grandmaster': tier = 'GrandMaster'
    lp = int(float(m.group(2).replace('.','').replace(',','.')))
    wins = losses = winrate = None
    wm = re.search(r'(?:Wins|Vitórias|Vitorias|Zaferler)\s*:?\s*(\d+)', area, re.I)
    lm = re.search(r'(?:Losses|Derrotas|Kayıplar|Kayiplar)\s*:?\s*(\d+)', area, re.I)
    if wm and lm:
        wins, losses = int(wm.group(1)), int(lm.group(1))
        if wins + losses: winrate = round(wins/(wins+losses)*100,1)
    return {
        'riot_id':'xyd#zzzzz','region':'BR','queue':'Solo/Duo','tier':tier,'lp':lp,
        'challenger':tier.lower()=='challenger','wins':wins,'losses':losses,'winrate':winrate,
        'source':source,'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ok'
    }

def fetch():
    sources = [
        ('LeagueOfGraphs profile','https://www.leagueofgraphs.com/summoner/br/xyd-zzzzz'),
        ('LeagueOfGraphs Yasuo ranking','https://www.leagueofgraphs.com/overwolf/summoners/yasuo/br'),
        ('Jina + LeagueOfGraphs','https://r.jina.ai/http://www.leagueofgraphs.com/summoner/br/xyd-zzzzz'),
        ('Jina + Yasuo ranking','https://r.jina.ai/http://www.leagueofgraphs.com/overwolf/summoners/yasuo/br'),
    ]
    errs=[]
    for name,url in sources:
        try:
            return parse_text(get(url), name)
        except Exception as e:
            errs.append(f'{name}: {e}')
    # Preserve last good data instead of blanking the site.
    try:
        old=json.load(open(OUT,encoding='utf-8'))
    except Exception:
        old={'riot_id':'xyd#zzzzz','region':'BR','queue':'Solo/Duo','tier':'Indisponível','lp':None,'challenger':False}
    old['status']='stale'
    old['error']=' | '.join(errs)[-1000:]
    old['checked_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    return old

if __name__ == '__main__':
    data=fetch()
    with open(OUT,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    print(json.dumps(data,ensure_ascii=False))
