import json, urllib.parse, requests, hashlib, re, time
TARGET='https://www.tesla.com/cua-api/apps/careers/state'
RELAYS={
'allorigins':'https://api.allorigins.win/raw?url='+urllib.parse.quote(TARGET,safe=''),
'corsproxy':'https://corsproxy.io/?url='+urllib.parse.quote(TARGET,safe=''),
'codetabs':'https://api.codetabs.com/v1/proxy?quest='+urllib.parse.quote(TARGET,safe=''),
'isomorphic-git':'https://cors.isomorphic-git.org/'+TARGET,
}
def validate(raw):
 d=json.loads(raw)
 if not isinstance(d,dict) or 'lookup' not in d: raise ValueError('missing lookup')
 locs=(d.get('lookup') or {}).get('locations')
 if not isinstance(locs,dict) or len(locs)<100: raise ValueError('bad locations')
 best=[]
 def walk(x):
  nonlocal best
  if isinstance(x,dict):
   for v in x.values(): walk(v)
  elif isinstance(x,list):
   ds=[v for v in x if isinstance(v,dict)]
   if len(ds)>len(best) and ds and sum(all(k in z for k in ('id','t','y','l')) for z in ds)/len(ds)>.9: best=ds
   for v in x[:5]: walk(v)
 walk(d)
 if len(best)<1000: raise ValueError(f'bad jobs {len(best)}')
 ids=[str(j['id']) for j in best]
 if '279990' not in ids: raise ValueError('known-current canary 279990 absent')
 ws=[str(j['id']) for j in best if int(j.get('y',0) or 0)==3 and re.search(r'Winter\s*/\s*Spring\s*2027',str(j.get('t','')),re.I)]
 su=[str(j['id']) for j in best if int(j.get('y',0) or 0)==3 and re.search(r'Summer\s*2027',str(j.get('t','')),re.I)]
 return {'bytes':len(raw),'all_jobs':len(best),'all_fp':hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest(),'ws_count_global':len(ws),'ws_fp':hashlib.sha256('\n'.join(sorted(ws)).encode()).hexdigest(),'summer27_count_global':len(su)}
for name,url in RELAYS.items():
 try:
  vals=[]
  for n in range(2):
   r=requests.get(url,timeout=75,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json,*/*'})
   print(name,'pass',n+1,'http',r.status_code,'bytes',len(r.content))
   if r.status_code!=200: raise RuntimeError(f'HTTP {r.status_code}')
   vals.append(validate(r.text)); time.sleep(2)
  if vals[0]!=vals[1]: raise RuntimeError(f'two-pass mismatch: {vals}')
  print('RELAY_VERIFIED',name,json.dumps(vals[1],sort_keys=True))
 except Exception as e:
  print('RELAY_FAILED',name,type(e).__name__,str(e))
