from __future__ import annotations
import hashlib,json,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]; STATE=ROOT/'internship-radar-state'
UA='RahilEngineeringInternshipRadar/1.0'; TIMEOUT=35
STATES={'Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','District Of Columbia','District of Columbia','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'}
AUSTIN={'Austin','Hutto','Round Rock','Pflugerville','Cedar Park','Leander','Georgetown','Taylor','Manor','Buda','Kyle','Bastrop'}
class SourceError(RuntimeError): pass

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def fp(ids): return hashlib.sha256('\n'.join(sorted(set(map(str,ids)))).encode()).hexdigest()
def season(t):
    for p,n in [(r'winter\s*/\s*spring\s*2027','Winter/Spring 2027'),(r'spring\s*2027','Spring 2027'),(r'summer\s*2027','Summer 2027'),(r'fall\s*2027','Fall 2027'),(r'fall\s*2026','Fall 2026')]:
        if re.search(p,t,re.I): return n
    return None
def intern(t): return bool(re.search(r'\b(intern(ship)?|co[ -]?op|apprentice|working student|werkstudent)\b',t,re.I))
def us(loc): return 'United States' in loc or any(loc.endswith(', '+s) for s in STATES)
def austin(loc): return loc.endswith(', Texas') and loc.split(',',1)[0].strip() in AUSTIN
def uniq(jobs):
    out={}
    for j in jobs:
        i=str(j.get('id','')).strip()
        if not i: raise SourceError('job without stable id')
        out[i]=j
    return [out[k] for k in sorted(out)]

def sess():
    s=requests.Session(); s.headers.update({'User-Agent':UA,'Accept':'application/json,text/html;q=0.9,*/*;q=0.8'}); return s
def getj(s,u):
    r=s.get(u,timeout=TIMEOUT)
    if r.status_code!=200: raise SourceError(f'GET {u} -> {r.status_code}')
    try:return r.json()
    except Exception as e: raise SourceError(f'non-JSON from {u}') from e
def postj(s,u,p):
    r=s.post(u,json=p,timeout=TIMEOUT,headers={'Content-Type':'application/json'})
    if r.status_code!=200: raise SourceError(f'POST {u} -> {r.status_code}')
    try:return r.json()
    except Exception as e: raise SourceError(f'non-JSON from {u}') from e

def tesla_arrays(data):
    best=[]; locs=None
    def walk(x):
        nonlocal best,locs
        if isinstance(x,dict):
            if locs is None and isinstance(x.get('locations'),dict) and len(x['locations'])>100: locs={str(k):str(v) for k,v in x['locations'].items()}
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            ds=[v for v in x if isinstance(v,dict)]
            if len(ds)>len(best) and ds and sum(all(k in d for k in ('id','t','y','l')) for d in ds)/len(ds)>.9: best=ds
            for v in x[:8]: walk(v)
    walk(data)
    if len(best)<500 or not locs: raise SourceError(f'Tesla schema validation failed (jobs={len(best)}, locations={0 if locs is None else len(locs)})')
    return best,locs

def tesla_state_via_browser():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
    except Exception as e: raise SourceError('selenium unavailable for Tesla browser fallback') from e
    opts=Options(); opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox'); opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--disable-gpu'); opts.add_argument('--window-size=1440,1200'); opts.add_argument('--lang=en-US')
    opts.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36')
    d=None
    try:
        d=webdriver.Chrome(options=opts); d.set_page_load_timeout(45); d.set_script_timeout(45)
        d.get('https://www.tesla.com/careers/search/?site=US&type=3')
        WebDriverWait(d,30).until(lambda x: x.execute_script('return document.readyState')=='complete')
        out=d.execute_async_script("""
          const cb=arguments[arguments.length-1];
          fetch('/cua-api/apps/careers/state',{credentials:'include',headers:{'accept':'application/json'}})
            .then(async r => cb({status:r.status,text:await r.text()}))
            .catch(e => cb({status:0,text:String(e)}));
        """)
        if not isinstance(out,dict) or int(out.get('status',0))!=200: raise SourceError(f"Tesla browser state fetch -> {(out or {}).get('status') if isinstance(out,dict) else 'invalid'}")
        try:return json.loads(out.get('text',''))
        except Exception as e: raise SourceError('Tesla browser returned non-JSON state') from e
    finally:
        if d is not None:
            try:d.quit()
            except Exception:pass

def fetch_tesla(s):
    u='https://www.tesla.com/cua-api/apps/careers/state'; method='direct_json'
    try:data=getj(s,u)
    except Exception as direct_err:
        data=tesla_state_via_browser(); method=f'browser_session_after_{type(direct_err).__name__}'
    raw,locs=tesla_arrays(data); jobs=[]; y3=ish=0
    for j in raw:
        if int(j.get('y',0) or 0)!=3: continue
        y3+=1; t=str(j.get('t','')).strip(); ish+=intern(t); l=locs.get(str(j.get('l','')),str(j.get('l','')))
        if us(l): jobs.append({'id':str(j['id']),'title':t,'location':l,'season':season(t),'deadline':j.get('pu'),'url':f"https://www.tesla.com/careers/search/job/{j['id']}"})
    if y3<20 or ish/y3<.45: raise SourceError(f'Tesla Intern/Apprentice taxonomy changed (y3={y3}, title_match={ish})')
    jobs=uniq(jobs); ids=[j['id'] for j in jobs]; cohorts={}
    for x in ('Winter/Spring 2027','Spring 2027','Summer 2027','Fall 2026'):
        q=sorted(j['id'] for j in jobs if j['season']==x); cohorts[x]={'count':len(q),'ids':q}
    q=sorted(j['id'] for j in jobs if j['season']=='Fall 2026' and austin(j['location']))
    return {'source':u,'source_type':'tesla_careers_state','fetch_method':method,'board_total':len(raw),'inventory_scope':'U.S. Intern/Apprentice','inventory_count':len(jobs),'inventory_ids':ids,'inventory_fingerprint':fp(ids),'cohorts':cohorts,'austin_fall_2026':{'count':len(q),'ids':q},'jobs':jobs}

def fetch_gh(s,company,token,optional=False):
    u=f'https://boards-api.greenhouse.io/v1/boards/{token}/jobs'
    try:d=getj(s,u)
    except Exception:
        if optional:return {'source':u,'available':False,'optional':True}
        raise
    raw=d.get('jobs'); total=int((d.get('meta') or {}).get('total',len(raw or [])))
    if not isinstance(raw,list) or total!=len(raw): raise SourceError(f'{company} Greenhouse count mismatch raw={0 if raw is None else len(raw)} total={total}')
    board=[]; ints=[]
    for j in raw:
        t=str(j.get('title','')).strip(); l=j.get('location') or {}; l=l.get('name','') if isinstance(l,dict) else str(l)
        x={'id':str(j.get('id','')),'title':t,'location':l,'season':season(t),'url':j.get('absolute_url') or f'https://job-boards.greenhouse.io/{token}/jobs/{j.get("id")}', 'updated_at':j.get('updated_at')}; board.append(x)
        if intern(t): ints.append(x)
    board=uniq(board); ints=uniq(ints)
    if len(board)!=total: raise SourceError(f'{company} Greenhouse unique-ID mismatch unique={len(board)} total={total}')
    b=[j['id'] for j in board]; ii=[j['id'] for j in ints]; cohorts={}
    for x in ('Winter/Spring 2027','Spring 2027','Summer 2027','Fall 2026'):
        q=sorted(j['id'] for j in ints if j['season']==x); cohorts[x]={'count':len(q),'ids':q}
    return {'source':u,'source_type':'greenhouse_job_board_api','board_token':token,'board_total':total,'board_ids':b,'board_fingerprint':fp(b),'inventory_scope':'internship/co-op titles','inventory_count':len(ints),'inventory_ids':ii,'inventory_fingerprint':fp(ii),'cohorts':cohorts,'jobs':ints}

def blue_pass(s):
    u='https://blueorigin.wd5.myworkdayjobs.com/wday/cxs/blueorigin/BlueOrigin/jobs'; off=0; expected=None; raw=[]; totals=[]
    while expected is None or off<expected:
        d=postj(s,u,{'appliedFacets':{},'limit':20,'offset':off,'searchText':''}); t=int(d.get('total',-1)); page=d.get('jobPostings'); totals.append(t)
        if t<0 or not isinstance(page,list): raise SourceError('Blue Origin Workday schema changed')
        if expected is None: expected=t
        if t!=expected: return None,totals
        if not page and off<expected: return None,totals
        raw+=page; off+=len(page)
    return raw,totals

def fetch_blue(s):
    u='https://blueorigin.wd5.myworkdayjobs.com/wday/cxs/blueorigin/BlueOrigin/jobs'; base='https://blueorigin.wd5.myworkdayjobs.com/en-US/BlueOrigin/'; last=[]
    for attempt in range(1,6):
        raw,totals=blue_pass(s); last=totals
        if raw is None:
            time.sleep(.8*attempt); continue
        total=totals[0] if totals else 0; jobs=[]
        for p in raw:
            text=' '.join(map(str,[p.get('externalPath',''),p.get('title',''),p.get('bulletFields','')])); m=re.search(r'(R\d{4,})',text)
            if not m: raise SourceError('Blue Origin requisition id missing')
            t=str(p.get('title','')).strip(); jobs.append({'id':m.group(1),'title':t,'location':str(p.get('locationsText','')),'season':season(t),'url':urljoin(base,str(p.get('externalPath','')).lstrip('/')),'posted_on':p.get('postedOn')})
        board=uniq(jobs)
        if len(board)!=total:
            time.sleep(.8*attempt); continue
        ints=[j for j in board if intern(j['title'])]; b=[j['id'] for j in board]; ii=[j['id'] for j in ints]; cohorts={}
        for x in ('Winter/Spring 2027','Spring 2027','Summer 2027','Fall 2026'):
            q=sorted(j['id'] for j in ints if j['season']==x); cohorts[x]={'count':len(q),'ids':q}
        return {'source':u,'source_type':'workday_cxs','snapshot_attempt':attempt,'board_total':total,'board_ids':b,'board_fingerprint':fp(b),'inventory_scope':'internship/co-op titles','inventory_count':len(ints),'inventory_ids':ii,'inventory_fingerprint':fp(ii),'cohorts':cohorts,'jobs':ints}
    raise SourceError(f'Blue Origin could not obtain internally consistent pass after 5 attempts; totals={last}')

def fetch_apple(s):
    base='https://jobs.apple.com/en-us/search'; found={}; total=None; stagnant=0
    for page in range(1,15):
        r=s.get(base,params={'team':'internships-STDNT-INTRN','page':page},timeout=TIMEOUT)
        if r.status_code!=200: raise SourceError(f'Apple -> {r.status_code}')
        soup=BeautifulSoup(r.text,'html.parser'); text=soup.get_text(' ',strip=True); m=re.search(r'([\d,]+)\s+Result\(s\)',text)
        if m and total is None: total=int(m.group(1).replace(',',''))
        before=len(found)
        for a in soup.find_all('a',href=True):
            h=str(a['href']); m=re.search(r'/details/([^/]+)/',h)
            if not m: continue
            i=m.group(1); slug=h.rstrip('/').split('/')[-1]; t=' '.join(a.stripped_strings).strip()
            if not t or len(t)<4 or t.lower().startswith(('share ','see full','submit ')): t=slug.replace('-',' ').title()
            found.setdefault(i,{'id':i,'title':t,'url':urljoin('https://jobs.apple.com',h),'season':season(t)})
        if total is not None and len(found)>=total: break
        stagnant=stagnant+1 if len(found)==before else 0
        if stagnant>=2: break
    if total is None or len(found)!=total: raise SourceError(f'Apple count {total} != unique IDs {len(found)}')
    jobs=[found[k] for k in sorted(found)]; ids=[j['id'] for j in jobs]
    return {'source':base+'?team=internships-STDNT-INTRN','source_type':'apple_server_rendered_search','board_total':total,'inventory_scope':'Apple Students: Internships','inventory_count':total,'inventory_ids':ids,'inventory_fingerprint':fp(ids),'jobs':jobs}

def ids(c,key='inventory_ids'): return set(map(str,(c or {}).get(key) or []))
def delta(prev,cur):
    pb=ids(prev,'board_ids') or ids(prev); cb=ids(cur,'board_ids') or ids(cur); pi=ids(prev); ci=ids(cur); out={'board_total_before':(prev or {}).get('board_total'),'board_total_after':cur.get('board_total'),'inventory_count_before':(prev or {}).get('inventory_count'),'inventory_count_after':cur.get('inventory_count'),'board_added_ids':sorted(cb-pb),'board_removed_ids':sorted(pb-cb),'inventory_added_ids':sorted(ci-pi),'inventory_removed_ids':sorted(pi-ci),'cohort_changes':{}}
    for n,c in cur.get('cohorts',{}).items():
        p=((prev or {}).get('cohorts',{}).get(n) or {}); pids=set(p.get('ids',[])); cids=set(c.get('ids',[]))
        if p.get('count')!=c.get('count') or pids!=cids: out['cohort_changes'][n]={'count_before':p.get('count'),'count_after':c.get('count'),'added_ids':sorted(cids-pids),'removed_ids':sorted(pids-cids)}
    return out

def main():
    STATE.mkdir(exist_ok=True); latestp=STATE/'latest.json'; prev=json.loads(latestp.read_text()) if latestp.exists() else {'companies':{}}; old=prev.get('companies',{}); s=sess(); ts=now()
    fs={'Tesla':lambda:fetch_tesla(s),'SpaceX':lambda:fetch_gh(s,'SpaceX','spacex'),'Anduril':lambda:fetch_gh(s,'Anduril','andurilindustries'),'Figure':lambda:fetch_gh(s,'Figure','figureai'),'Blue Origin':lambda:fetch_blue(s),'Apple':lambda:fetch_apple(s)}; companies={}; changes={}; status={}
    for n,f in fs.items():
        try:
            c=f(); c.update({'fetched_at':ts,'source_status':'ok','last_success':ts}); companies[n]=c; changes[n]=delta(old.get(n),c); status[n]={'ok':True,'last_success':ts,'board_total':c.get('board_total'),'inventory_count':c.get('inventory_count'),'inventory_fingerprint':c.get('inventory_fingerprint'),'fetch_method':c.get('fetch_method'),'snapshot_attempt':c.get('snapshot_attempt')}
        except Exception as e:
            if old.get(n): c=dict(old[n]); c.update({'source_status':'error','last_attempt':ts,'source_error':f'{type(e).__name__}: {e}'}); companies[n]=c
            status[n]={'ok':False,'last_success':(old.get(n) or {}).get('last_success'),'last_attempt':ts,'error':f'{type(e).__name__}: {e}'}; changes[n]={'source_error':status[n]['error'],'changes_suppressed':True}
    alt=fetch_gh(s,'SpaceX Global','spacexglobal',True); run='ok' if all(v['ok'] for v in status.values()) else 'partial_failure'
    latest={'schema_version':1,'fetched_at':ts,'run_status':run,'companies':companies,'canaries':{'SpaceX alternate board spacexglobal':alt}}; d={'schema_version':1,'fetched_at':ts,'companies':changes}; st={'schema_version':1,'fetched_at':ts,'run_status':run,'companies':status}
    latestp.write_text(json.dumps(latest,indent=2,sort_keys=True)+'\n'); (STATE/'delta.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n'); (STATE/'status.json').write_text(json.dumps(st,indent=2,sort_keys=True)+'\n'); print(json.dumps(st,indent=2)); return 0 if run=='ok' else 2
if __name__=='__main__': sys.exit(main())
