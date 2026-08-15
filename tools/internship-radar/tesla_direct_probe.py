import json, hashlib, re, time, urllib.request
URL='https://www.tesla.com/cua-api/apps/careers/state'

def fetch():
 req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151 Safari/537.36','Accept':'application/json,text/plain,*/*','Referer':'https://www.tesla.com/careers/search/'})
 with urllib.request.urlopen(req,timeout=60) as r:
  raw=r.read(); status=r.status
 print('HTTP',status,'BYTES',len(raw))
 d=json.loads(raw)
 locs=(d.get('lookup') or {}).get('locations') or {}
 listings=d.get('listings') or []
 if len(locs)<100 or len(listings)<1000: raise RuntimeError(f'schema bad locations={len(locs)} listings={len(listings)}')
 ids=sorted(str(x.get('id')) for x in listings if x.get('id'))
 if '279990' not in ids: raise RuntimeError('current req 279990 absent')
 ws=sorted(str(x['id']) for x in listings if x.get('id') and int(x.get('y',0) or 0)==3 and re.search(r'Winter\s*/\s*Spring\s*2027',str(x.get('t','')),re.I))
 fp=hashlib.sha256('\n'.join(ids).encode()).hexdigest()
 return {'jobs':len(listings),'fp':fp,'ws_global':len(ws),'ws_ids':ws}
a=fetch(); time.sleep(4); b=fetch(); print('PASS1',json.dumps(a,sort_keys=True)); print('PASS2',json.dumps(b,sort_keys=True));
if a!=b: raise SystemExit('two-pass mismatch')
print('TESLA_DIRECT_VERIFIED',json.dumps(b,sort_keys=True))
