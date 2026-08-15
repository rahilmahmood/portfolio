from __future__ import annotations
import hashlib,json,re,time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

TIMEOUT=35
UA='RahilEngineeringInternshipRadar/2.0'
BLUE_URL='https://blueorigin.wd5.myworkdayjobs.com/wday/cxs/blueorigin/BlueOrigin/jobs'
BLUE_FACETS={
 'jobFamily':('1aee286254b60124ba1012d4e8346abd','INT - Interns, Externs, & Scholars'),
 'workerSubType':('f3db39143e3e01ea6d86269150283618','Intern (Fixed Term)'),
 'jobFamilyGroup':('5f32d2b8465201b51255d2713817d845','Contingent, Temporary, & Intern'),
}
class SourceError(RuntimeError): pass

def fp(ids): return hashlib.sha256('\n'.join(sorted(set(map(str,ids)))).encode()).hexdigest()
def season(t):
    for p,n in [(r'winter\s*/\s*spring\s*2027','Winter/Spring 2027'),(r'spring\s*2027','Spring 2027'),(r'summer\s*2027','Summer 2027'),(r'fall\s*2027','Fall 2027'),(r'fall\s*2026','Fall 2026')]:
        if re.search(p,t,re.I): return n
    return None
def intern(t): return bool(re.search(r'\b(intern(ship)?|co[ -]?op|apprentice)\b',t,re.I))
def session():
    s=requests.Session(); s.headers.update({'User-Agent':UA,'Accept':'application/json,text/html;q=0.9,*/*;q=0.8'}); return s
def getj(s,u):
    r=s.get(u,timeout=TIMEOUT)
    if r.status_code!=200: raise SourceError(f'GET {u} -> {r.status_code}')
    try:return r.json()
    except Exception as e: raise SourceError(f'non-JSON GET {u}') from e
def postj(s,u,p):
    r=s.post(u,json=p,timeout=TIMEOUT,headers={'Content-Type':'application/json'})
    if r.status_code!=200: raise SourceError(f'POST {u} -> {r.status_code}')
    try:return r.json()
    except Exception as e: raise SourceError(f'non-JSON POST {u}') from e

def greenhouse(s,token):
    u=f'https://boards-api.greenhouse.io/v1/boards/{token}/jobs'; d=getj(s,u); raw=d.get('jobs'); total=int((d.get('meta') or {}).get('total',len(raw or [])))
    if not isinstance(raw,list) or len(raw)!=total: raise SourceError(f'{token}: Greenhouse total mismatch')
    seen={}
    for j in raw:
        jid=str(j.get('id','')).strip()
        if not jid: raise SourceError(f'{token}: missing job id')
        loc=j.get('location') or {}; loc=loc.get('name','') if isinstance(loc,dict) else str(loc); title=str(j.get('title','')).strip()
        seen[jid]={'id':jid,'title':title,'location':loc,'season':season(title),'url':j.get('absolute_url'),'updated_at':j.get('updated_at')}
    if len(seen)!=total: raise SourceError(f'{token}: duplicate job ids')
    jobs=[seen[k] for k in sorted(seen) if intern(seen[k]['title'])]; ids=[x['id'] for x in jobs]; board_ids=sorted(seen)
    return {'board_total':total,'board_fingerprint':fp(board_ids),'inventory_count':len(jobs),'inventory_ids':ids,'inventory_fingerprint':fp(ids),'jobs':jobs}

def blue_facets(s):
    # One unfiltered request establishes current board total and confirms the named facet IDs still exist.
    root=postj(s,BLUE_URL,{'appliedFacets':{},'limit':20,'offset':0,'searchText':''}); board_total=int(root.get('total',-1)); facets=root.get('facets')
    if board_total<1 or not isinstance(facets,list): raise SourceError('Blue Origin root schema changed')
    advertised={}
    for f in facets:
        param=f.get('facetParameter')
        for v in f.get('values') or []:
            advertised[(param,str(v.get('id')))]={'descriptor':v.get('descriptor'),'count':int(v.get('count',0))}
        if param=='locationMainGroup':
            for sub in f.get('values') or []:
                p2=sub.get('facetParameter')
                for v in sub.get('values') or []: advertised[(p2,str(v.get('id')))]={'descriptor':v.get('descriptor'),'count':int(v.get('count',0))}
    sets=[]; detail={}; merged={}
    for param,(fid,expected_name) in BLUE_FACETS.items():
        meta=advertised.get((param,fid))
        if not meta or meta['descriptor']!=expected_name: raise SourceError(f'Blue Origin facet mapping changed: {param}')
        d=postj(s,BLUE_URL,{'appliedFacets':{param:[fid]},'limit':20,'offset':0,'searchText':''}); total=int(d.get('total',-1)); rows=d.get('jobPostings')
        if total!=meta['count'] or not isinstance(rows,list) or len(rows)!=total: raise SourceError(f'Blue Origin facet {param} count mismatch')
        ids=set()
        for p in rows:
            text=' '.join(map(str,[p.get('externalPath',''),p.get('title',''),p.get('bulletFields','')])); m=re.search(r'(R\d{4,})',text)
            if not m: raise SourceError('Blue Origin missing requisition ID')
            rid=m.group(1); ids.add(rid); title=str(p.get('title','')).strip(); merged[rid]={'id':rid,'title':title,'location':str(p.get('locationsText','')),'season':season(title),'posted_on':p.get('postedOn'),'url':urljoin('https://blueorigin.wd5.myworkdayjobs.com/en-US/BlueOrigin/',str(p.get('externalPath','')).lstrip('/'))}
        if len(ids)!=total: raise SourceError(f'Blue Origin facet {param} duplicate IDs')
        sets.append(ids); detail[param]={'count':total,'ids':sorted(ids),'descriptor':expected_name}
    # All three independently maintained Workday internship classifications should agree. Divergence is a coverage alarm, not silently unioned.
    if not sets or any(x!=sets[0] for x in sets[1:]): raise SourceError(f'Blue Origin internship facets diverged: {[sorted(x) for x in sets]}')
    ids=sorted(sets[0]); jobs=[merged[i] for i in ids]
    return {'board_total':board_total,'inventory_count':len(ids),'inventory_ids':ids,'inventory_fingerprint':fp(ids),'facet_reconciliation':detail,'jobs':jobs}

def apple(s):
    base='https://jobs.apple.com/en-us/search'; found={}; total=None; stagnant=0
    for page in range(1,20):
        r=s.get(base,params={'team':'internships-STDNT-INTRN','page':page},timeout=TIMEOUT)
        if r.status_code!=200: raise SourceError(f'Apple page {page} -> {r.status_code}')
        soup=BeautifulSoup(r.text,'html.parser'); txt=soup.get_text(' ',strip=True); m=re.search(r'([\d,]+)\s+Result\(s\)',txt)
        if m and total is None: total=int(m.group(1).replace(',',''))
        before=len(found)
        for a in soup.find_all('a',href=True):
            href=str(a['href']); m=re.search(r'/details/([^/]+)/',href)
            if not m: continue
            jid=m.group(1); title=' '.join(a.stripped_strings).strip() or href.rstrip('/').split('/')[-1].replace('-',' ')
            found.setdefault(jid,{'id':jid,'title':title,'season':season(title),'url':urljoin('https://jobs.apple.com',href)})
        if total is not None and len(found)>=total: break
        stagnant=stagnant+1 if len(found)==before else 0
        if stagnant>=2: break
    if total is None or len(found)!=total: raise SourceError(f'Apple count mismatch unique={len(found)} total={total}')
    ids=sorted(found); return {'board_total':total,'inventory_count':total,'inventory_ids':ids,'inventory_fingerprint':fp(ids),'jobs':[found[i] for i in ids]}

def one_pass():
    s=session()
    return {'SpaceX':greenhouse(s,'spacex'),'Anduril':greenhouse(s,'andurilindustries'),'Figure':greenhouse(s,'figureai'),'Blue Origin':blue_facets(s),'Apple':apple(s)}

def summary(x):
    return {k:{'board_total':v.get('board_total'),'inventory_count':v['inventory_count'],'inventory_fingerprint':v['inventory_fingerprint'],'inventory_ids':v['inventory_ids'],'facet_reconciliation':v.get('facet_reconciliation')} for k,v in x.items()}

def main():
    a=one_pass(); print('PASS1',json.dumps(summary(a),sort_keys=True)); time.sleep(5); b=one_pass(); print('PASS2',json.dumps(summary(b),sort_keys=True))
    for company in a:
        aa,bb=a[company],b[company]
        if aa['inventory_ids']!=bb['inventory_ids'] or aa.get('board_total')!=bb.get('board_total'):
            raise SourceError(f'{company}: two-pass reconciliation changed within 5 seconds')
    print('VERIFIED',json.dumps(summary(b),indent=2,sort_keys=True))
if __name__=='__main__': main()
