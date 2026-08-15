import json,re,requests
URL='https://blueorigin.wd5.myworkdayjobs.com/wday/cxs/blueorigin/BlueOrigin/jobs'
FACETS={
 'jobFamily':['1aee286254b60124ba1012d4e8346abd'],
 'workerSubType':['f3db39143e3e01ea6d86269150283618'],
 'jobFamilyGroup':['5f32d2b8465201b51255d2713817d845'],
}
s=requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0','Content-Type':'application/json'})
for param,ids in FACETS.items():
 r=s.post(URL,json={'appliedFacets':{param:ids},'limit':20,'offset':0,'searchText':''},timeout=30)
 print(param,'HTTP',r.status_code)
 d=r.json(); print('TOTAL',d.get('total'))
 for p in d.get('jobPostings',[]):
  text=' '.join(map(str,[p.get('externalPath',''),p.get('title',''),p.get('bulletFields','')]))
  m=re.search(r'(R\d{4,})',text)
  print(json.dumps({'id':m.group(1) if m else None,'title':p.get('title'),'location':p.get('locationsText'),'path':p.get('externalPath'),'postedOn':p.get('postedOn')},sort_keys=True))
