import json, re
from ats_scrapers.manifest import Manifest
from ats_scrapers import search

m=Manifest.fetch()
print('GENERATED_AT',m.generated_at.isoformat())
print('STATS',m.stats.model_dump())
print('HAS_TESLA','tesla' in m.by_ats)
if 'tesla' not in m.by_ats:
    raise SystemExit('Tesla source absent from hosted manifest')
e=m.by_ats['tesla']
print('TESLA_ARTIFACT',e.model_dump())
# Base search is per-source and does not require parquet extra. Pull a generous limit and validate unique IDs.
df=search(ats='tesla',limit=10000)
print('ROWS_RETURNED',len(df))
print('COLUMNS',list(df.columns))
if df.empty:
    raise SystemExit('Tesla dataset empty')
# Keep rows whose company is Tesla if that column is exposed.
if 'company' in df.columns:
    print('COMPANIES',df['company'].value_counts().head(10).to_dict())
# Detect stable requisition id from normalized fields / URLs.
id_col=next((c for c in ['ats_id','job_id','id'] if c in df.columns),None)
url_col=next((c for c in ['apply_url','url','job_url'] if c in df.columns),None)
if id_col:
    ids=df[id_col].astype(str).tolist()
elif url_col:
    ids=[]
    for u in df[url_col].astype(str):
        mm=re.search(r'(\d{6})(?:\D*$)',u)
        if mm: ids.append(mm.group(1))
else:
    raise SystemExit('No stable-id or URL column')
ids=sorted(set(ids))
print('UNIQUE_IDS',len(ids))
print('HAS_279990','279990' in ids)
# season counts from title if present
title_col=next((c for c in ['title','job_title'] if c in df.columns),None)
if title_col:
    titles=df[title_col].fillna('').astype(str)
    ws=df[titles.str.contains(r'Winter\s*/\s*Spring\s*2027',case=False,regex=True)]
    su=df[titles.str.contains(r'Summer\s*2027',case=False,regex=True)]
    print('WS_ROWS_GLOBAL',len(ws))
    print('SUMMER27_ROWS_GLOBAL',len(su))
    cols=[c for c in [id_col,title_col,'location',url_col] if c]
    print('WS_SAMPLE',json.dumps(ws[cols].head(100).to_dict(orient='records'),default=str))
# dump selected likely-US internship rows for independent reconciliation
if title_col:
    mask=titles.str.contains(r'Intern(ship)?|Apprentice|Co[- ]?op',case=False,regex=True)
    ints=df[mask]
    print('INTERNISH_GLOBAL',len(ints))
    cols=[c for c in [id_col,title_col,'location',url_col] if c]
    print('INTERNS',json.dumps(ints[cols].to_dict(orient='records'),default=str)[:200000])
