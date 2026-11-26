import json, re, numpy as np, collections
from scipy import stats
rng=np.random.default_rng(42)
TH=json.load(open('themes_raw.json')); MM=json.load(open('tiktok_raw.json'))
Q={'душа компании мем':1,'люблю спорить мем':2,'перфекционист мем':3,'тревожность мем':4,'люблю необычное мем':5,'интроверт мем':6,'лучшая подруга поддержка мем':7,'забыла мем':8,'спокойствие мем':9,'классика не стареет мем':10}
def ok(x): return x.get('playCount',0)>=500 and x.get('createTimeISO','')>='2025-01-01'
def sr(x): return (x['shareCount']+x.get('collectCount',0))/x['playCount']  # «хочу переслать/сохранить»
def er(x): return (x['diggCount']+x['commentCount']+x['shareCount'])/x['playCount']
def boot_med(a,n=4000):
    a=np.asarray(a); b=np.median(rng.choice(a,(n,len(a))),axis=1); return np.percentile(b,[2.5,97.5])
out={}
# ---------- A. Темы вопросов: где пересылают чаще (Kruskal–Wallis)
th=[x for x in TH if ok(x) and x.get('textLanguage') in ('ru','un','uk','ky')]
groups={q:[sr(x) for x in th if x['searchQuery']==q] for q in Q}
H,p=stats.kruskal(*groups.values())
A=[]
for q,v in sorted(groups.items(),key=lambda kv:-np.median(kv[1])):
    lo,hi=boot_med(v); pl=[x['playCount'] for x in th if x['searchQuery']==q]
    A.append(dict(q=Q[q],theme=q.replace(' мем',''),n=len(v),share_med=round(100*np.median(v),2),ci=[round(100*lo,2),round(100*hi,2)],views_med=int(np.median(pl))))
out['themes']={'kruskal_H':round(H,1),'p':float(p),'rows':A}
print('A. Темы: Kruskal–Wallis H=%.1f p=%.2g'%(H,p))
for r in A: print('  Q%-2d %-28s n=%-3d пересылки+сохранения медиана %5.2f%% [95%% ДИ %s] просмотры %s'%(r['q'],r['theme'],r['n'],r['share_med'],r['ci'],r['views_med']))
# ---------- B. Форматы внутри тем: что повышает пересылки (Mann–Whitney, Холм)
FEAT={'жиза / узнаваемость':r'жиза|relatable|pov|когда ты|когда тво|я когда|типичн','кот / животные':r'\bкот|кош|cat\b|cats|собак|dog','анимация':r'анимац|animation|animationmeme|рисов','щитпост / абсурд':r'\bщп\b|щитпост|shitpost|абсурд|рофл','подруга / пара':r'подруг|bestie|лп\b|лучшаяподруга|парень|девушк|отношен','звук-тренд (capcut/memecut)':r'capcut|memecut|greenscreen'}
def blob(x):
    hs=' '.join((h.get('name','') if isinstance(h,dict) else str(h)) for h in (x.get('hashtags') or []))
    return (x.get('text','')+' '+hs).lower()
B=[]
for f,pat in FEAT.items():
    yes=[sr(x) for x in th if re.search(pat,blob(x))]; no=[sr(x) for x in th if not re.search(pat,blob(x))]
    if len(yes)<8: continue
    U,pp=stats.mannwhitneyu(yes,no,alternative='two-sided')
    rb=1-2*U/(len(yes)*len(no))  # rank-biserial (знак: >0 — у формата ниже? переводим ниже)
    B.append(dict(f=f,n=len(yes),med_yes=round(100*np.median(yes),2),med_no=round(100*np.median(no),2),p=pp,effect=round(-rb,2)))
B.sort(key=lambda r:r['p']); m=len(B)
for k,r in enumerate(B): r['p_holm']=min(1.0,r['p']*(m-k))
for k in range(1,m): B[k]['p_holm']=max(B[k]['p_holm'],B[k-1]['p_holm'])
out['formats']=B
print('\nB. Форматы (пересылки+сохранения, медиана; Mann–Whitney, поправка Холма):')
for r in B: print('  %-28s n=%-3d есть %5.2f%% vs нет %5.2f%%  эффект r=%+.2f  p_holm=%.3f'%(r['f'],r['n'],r['med_yes'],r['med_no'],r['effect'],r['p_holm']))
# ---------- C. Мемы: основной vs альтернативы по каждому вопросу
KEY={'Пиббл':'пиббл','Охаёшечки':'охаешечки','Могну':'я тебя могну','Бурмалда':'бурмалда','Собачка':'вот такие дела собачка','Можно, а зачем?':'можно а зачем','Черемша':'черемша мем','Пухосос':'пухосос','Воздухан':'воздухан','Сова':'сова на скакалке','Пингвин':'пингвин нигилист','Мой 2016':'мой 2016','6-7':'сикс севен','Бобр':'бобр за столом'}
PLAN={1:['Пиббл','Охаёшечки','Могну'],2:['Бурмалда','Собачка','Можно, а зачем?'],3:['Черемша','Пухосос',None],4:['Собачка','Воздухан','Сова'],5:['Черемша','Можно, а зачем?','Пухосос'],6:['Пингвин','Черемша','Мой 2016'],7:['Собачка','Пиббл','Мой 2016'],8:['Воздухан','Сова','6-7'],9:['Пиббл','Черемша','Бобр'],10:['Можно, а зачем?','Мой 2016','Пухосос']}
mm=[x for x in MM if ok(x)]
def vals(name): return [sr(x) for x in mm if x['searchQuery']==KEY[name]]
C={}
print('\nC. Мемы: медиана пересылок+сохранений [95% ДИ], n:')
memes={}
for nm in KEY:
    v=vals(nm); lo,hi=boot_med(v); memes[nm]=dict(n=len(v),med=round(100*np.median(v),2),ci=[round(100*lo,2),round(100*hi,2)])
    print('  %-16s n=%-2d %5.2f%% [%s]'%(nm,len(v),memes[nm]['med'],memes[nm]['ci']))
out['memes']=memes
print('\n   Вопрос: основной vs альт.1 / альт.2 (Mann–Whitney, двусторонний):')
for qn,(a,b1,b2) in PLAN.items():
    res=[]
    for b in (b1,b2):
        if not b: res.append(None); continue
        U,pp=stats.mannwhitneyu(vals(a),vals(b),alternative='two-sided'); res.append((b,round(pp,3)))
    C[qn]=dict(main=a,vs=res)
    print('  Q%-2d %-16s'%(qn,a),' | '.join(f'{b}: p={pp}' for b,pp in [r for r in res if r]))
out['main_vs_alt']=C
json.dump(out,open('stats_2026-11-26.json','w'),ensure_ascii=False,indent=1,default=float)
