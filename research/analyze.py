import json, statistics as st, math, csv
from datetime import datetime, timezone
tt=json.load(open('tiktok_raw.json')); ig=json.load(open('instagram_raw.json'))
NOW=datetime(2026,11,24,tzinfo=timezone.utc)
rows=[]
for q in sorted(set(x['searchQuery'] for x in tt)):
    v=[x for x in tt if x['searchQuery']==q and x.get('playCount')]
    # релевантность: только ролики 2025–2026 (отсекаем старьё, попавшее в поиск)
    v=[x for x in v if x['createTimeISO']>='2025-01-01']
    plays=[x['playCount'] for x in v]
    eng=[(x['diggCount']+x['commentCount']+x['shareCount'])/x['playCount'] for x in v]
    shr=[x['shareCount']/x['playCount'] for x in v]
    last90=[x for x in v if (NOW-datetime.fromisoformat(x['createTimeISO'].replace('Z','+00:00'))).days<=90]
    top=max(v,key=lambda x:x['playCount'])
    r=dict(meme=q,n=len(v),plays_total=sum(plays),plays_median=int(st.median(plays)),
           eng_median=round(st.median(eng)*100,1),share_median=round(st.median(shr)*100,2),
           fresh90=len(last90),fresh90_share=round(len(last90)/len(v)*100),
           p100k=sum(1 for p in plays if p>=100000),top_url=top['webVideoUrl'],top_plays=top['playCount'])
    if q in ig:
        ip=[a for a,b,c in ig[q]]; r['ig_n']=len(ip); r['ig_median']=int(st.median(ip)); r['ig_total']=sum(ip)
    rows.append(r)
# индекс: медиана просмотров (лог) 40% + доля репостов 30% + свежесть 30% — нормировка по максимуму
def norm(vals):
    m=max(vals); return [v/m if m else 0 for v in vals]
a=norm([math.log10(r['plays_median']+1) for r in rows]); b=norm([r['share_median'] for r in rows]); c=norm([r['fresh90_share'] for r in rows])
for r,x,y,z in zip(rows,a,b,c): r['index']=round(100*(.4*x+.3*y+.3*z))
rows.sort(key=lambda r:-r['index'])
json.dump(rows,open('meme_metrics.json','w'),ensure_ascii=False,indent=1)
with open('meme_metrics.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())+['ig_n','ig_median','ig_total'],extrasaction='ignore'); w.writeheader(); [w.writerow(r) for r in rows]
for r in rows: print(f"{r['index']:>3} {r['meme']:<24} n={r['n']:<3} med={r['plays_median']:>9,} total={r['plays_total']:>12,} eng={r['eng_median']:>5}% share={r['share_median']:>5}% fresh90={r['fresh90_share']:>3}% ig_med={r.get('ig_median','—')}")
