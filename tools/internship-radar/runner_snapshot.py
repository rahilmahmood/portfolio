from __future__ import annotations
import hashlib, json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "internship-radar-state"
TIMEOUT = 35
UA = "RahilEngineeringInternshipRadar/1.1"

class SourceError(RuntimeError):
    pass

def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def fingerprint(ids):
    return hashlib.sha256("\n".join(sorted(set(map(str, ids)))).encode()).hexdigest()

def season(title):
    for pat, name in [
        (r"winter\s*/\s*spring\s*2027", "Winter/Spring 2027"),
        (r"spring\s*2027", "Spring 2027"),
        (r"summer\s*2027", "Summer 2027"),
        (r"fall\s*2027", "Fall 2027"),
        (r"fall\s*2026", "Fall 2026"),
    ]:
        if re.search(pat, title, re.I):
            return name
    return None

def is_intern(title):
    return bool(re.search(r"\b(intern(ship)?|co[ -]?op|apprentice)\b", title, re.I))

def sess():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json,text/html;q=0.9,*/*;q=0.8"})
    return s

def get_json(s, url):
    r = s.get(url, timeout=TIMEOUT)
    if r.status_code != 200:
        raise SourceError(f"GET {url} -> {r.status_code}")
    try:
        return r.json()
    except Exception as e:
        raise SourceError(f"non-JSON from {url}") from e

def post_json(s, url, payload):
    r = s.post(url, json=payload, timeout=TIMEOUT, headers={"Content-Type":"application/json"})
    if r.status_code != 200:
        raise SourceError(f"POST {url} -> {r.status_code}")
    try:
        return r.json()
    except Exception as e:
        raise SourceError(f"non-JSON from {url}") from e

def uniq(jobs):
    out = {}
    for j in jobs:
        jid = str(j.get("id", "")).strip()
        if not jid:
            raise SourceError("job without stable id")
        out[jid] = j
    return [out[k] for k in sorted(out)]

def cohort_map(jobs):
    out = {}
    for name in ("Winter/Spring 2027", "Spring 2027", "Summer 2027", "Fall 2026"):
        ids = sorted(j["id"] for j in jobs if j.get("season") == name)
        out[name] = {"count": len(ids), "ids": ids}
    return out

def greenhouse(s, company, token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    data = get_json(s, url)
    raw = data.get("jobs")
    total = int((data.get("meta") or {}).get("total", len(raw or [])))
    if not isinstance(raw, list) or len(raw) != total:
        raise SourceError(f"{company} Greenhouse raw count mismatch {len(raw or [])}!={total}")
    board = []
    for j in raw:
        loc = j.get("location") or {}
        loc = loc.get("name", "") if isinstance(loc, dict) else str(loc)
        title = str(j.get("title", "")).strip()
        board.append({
            "id": str(j.get("id", "")), "title": title, "location": loc,
            "season": season(title), "updated_at": j.get("updated_at"),
            "url": j.get("absolute_url") or f"https://job-boards.greenhouse.io/{token}/jobs/{j.get('id')}"
        })
    board = uniq(board)
    if len(board) != total:
        raise SourceError(f"{company} Greenhouse unique-ID mismatch {len(board)}!={total}")
    internships = [j for j in board if is_intern(j["title"])]
    board_ids = [j["id"] for j in board]
    inv_ids = [j["id"] for j in internships]
    return {
        "source": url, "source_type": "greenhouse_job_board_api", "board_token": token,
        "board_total": total, "board_ids": board_ids, "board_fingerprint": fingerprint(board_ids),
        "inventory_scope": "internship/co-op/apprentice titles", "inventory_count": len(internships),
        "inventory_ids": inv_ids, "inventory_fingerprint": fingerprint(inv_ids),
        "cohorts": cohort_map(internships), "jobs": internships,
    }

def workday_query_pass(s, term):
    url = "https://blueorigin.wd5.myworkdayjobs.com/wday/cxs/blueorigin/BlueOrigin/jobs"
    offset = 0
    expected = None
    raw = []
    while expected is None or offset < expected:
        d = post_json(s, url, {"appliedFacets":{}, "limit":20, "offset":offset, "searchText":term})
        total = int(d.get("total", -1))
        page = d.get("jobPostings")
        if total < 0 or not isinstance(page, list):
            raise SourceError(f"Blue Origin schema changed for query {term}")
        if expected is None:
            expected = total
        elif total != expected:
            return None, (expected, total)
        if not page and offset < expected:
            return None, (expected, total)
        raw.extend(page)
        offset += len(page)
    return raw, (expected, expected)

def workday_query(s, term):
    last = None
    for attempt in range(1, 4):
        raw, totals = workday_query_pass(s, term)
        last = totals
        if raw is None:
            time.sleep(0.8 * attempt)
            continue
        expected = totals[0]
        by_path = {}
        for p in raw:
            path = str(p.get("externalPath", ""))
            if not path:
                raise SourceError(f"Blue Origin missing externalPath for {term}")
            by_path[path] = p
        if len(by_path) != expected:
            time.sleep(0.8 * attempt)
            continue
        return list(by_path.values()), expected, attempt
    raise SourceError(f"Blue Origin query {term!r} inconsistent after 3 passes; totals={last}")

def blue_origin(s):
    url = "https://blueorigin.wd5.myworkdayjobs.com/wday/cxs/blueorigin/BlueOrigin/jobs"
    base = "https://blueorigin.wd5.myworkdayjobs.com/en-US/BlueOrigin/"
    terms = ["intern", "co-op", "apprentice"]
    merged = {}
    query_counts = {}
    query_attempts = {}
    for term in terms:
        raw, count, attempt = workday_query(s, term)
        query_counts[term] = count
        query_attempts[term] = attempt
        for p in raw:
            text = " ".join(map(str, [p.get("externalPath", ""), p.get("title", ""), p.get("bulletFields", "")]))
            m = re.search(r"(R\d{4,})", text)
            if not m:
                raise SourceError(f"Blue Origin stable requisition ID missing for {p.get('title')}")
            title = str(p.get("title", "")).strip()
            if not is_intern(title):
                continue
            rid = m.group(1)
            merged[rid] = {
                "id": rid, "title": title, "location": str(p.get("locationsText", "")),
                "season": season(title), "posted_on": p.get("postedOn"),
                "url": urljoin(base, str(p.get("externalPath", "")).lstrip("/")),
            }
    jobs = [merged[k] for k in sorted(merged)]
    ids = [j["id"] for j in jobs]
    if not jobs:
        raise SourceError("Blue Origin scoped internship inventory unexpectedly empty")
    return {
        "source": url, "source_type": "workday_cxs_scoped_queries",
        "inventory_scope": "union of authoritative Workday searchText=intern|co-op|apprentice, title-filtered",
        "query_counts": query_counts, "query_attempts": query_attempts,
        "inventory_count": len(jobs), "inventory_ids": ids, "inventory_fingerprint": fingerprint(ids),
        "cohorts": cohort_map(jobs), "jobs": jobs,
    }

def apple(s):
    base = "https://jobs.apple.com/en-us/search"
    found = {}
    total = None
    stagnant = 0
    for page in range(1, 15):
        r = s.get(base, params={"team":"internships-STDNT-INTRN", "page":page}, timeout=TIMEOUT)
        if r.status_code != 200:
            raise SourceError(f"Apple -> {r.status_code}")
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        m = re.search(r"([\d,]+)\s+Result\(s\)", text)
        if m and total is None:
            total = int(m.group(1).replace(",", ""))
        before = len(found)
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            m = re.search(r"/details/([^/]+)/", href)
            if not m:
                continue
            jid = m.group(1)
            slug = href.rstrip("/").split("/")[-1]
            title = " ".join(a.stripped_strings).strip()
            if not title or len(title) < 4 or title.lower().startswith(("share ", "see full", "submit ")):
                title = slug.replace("-", " ").title()
            found.setdefault(jid, {"id":jid, "title":title, "season":season(title), "url":urljoin("https://jobs.apple.com", href)})
        if total is not None and len(found) >= total:
            break
        stagnant = stagnant + 1 if len(found) == before else 0
        if stagnant >= 2:
            break
    if total is None or len(found) != total:
        raise SourceError(f"Apple unique-ID count mismatch {len(found)}!={total}")
    jobs = [found[k] for k in sorted(found)]
    ids = [j["id"] for j in jobs]
    return {
        "source": base + "?team=internships-STDNT-INTRN", "source_type":"apple_server_rendered_search",
        "board_total": total, "inventory_scope":"Apple Students: Internships",
        "inventory_count": total, "inventory_ids":ids, "inventory_fingerprint":fingerprint(ids),
        "cohorts":cohort_map(jobs), "jobs":jobs,
    }

def delta(prev, cur):
    p = set(map(str, (prev or {}).get("inventory_ids") or []))
    c = set(map(str, cur.get("inventory_ids") or []))
    out = {
        "inventory_count_before": (prev or {}).get("inventory_count"),
        "inventory_count_after": cur.get("inventory_count"),
        "inventory_added_ids": sorted(c-p), "inventory_removed_ids": sorted(p-c), "cohort_changes":{}
    }
    for name, cohort in cur.get("cohorts", {}).items():
        pc = ((prev or {}).get("cohorts", {}).get(name) or {})
        pi, ci = set(pc.get("ids", [])), set(cohort.get("ids", []))
        if pc.get("count") != cohort.get("count") or pi != ci:
            out["cohort_changes"][name] = {"count_before":pc.get("count"), "count_after":cohort.get("count"), "added_ids":sorted(ci-pi), "removed_ids":sorted(pi-ci)}
    return out

def main():
    STATE.mkdir(exist_ok=True)
    latest_path = STATE / "runner-latest.json"
    previous = json.loads(latest_path.read_text()) if latest_path.exists() else {"companies":{}}
    old = previous.get("companies", {})
    s = sess(); ts = now()
    fetchers = {
        "SpaceX": lambda: greenhouse(s, "SpaceX", "spacex"),
        "Anduril": lambda: greenhouse(s, "Anduril", "andurilindustries"),
        "Figure": lambda: greenhouse(s, "Figure", "figureai"),
        "Blue Origin": lambda: blue_origin(s),
        "Apple": lambda: apple(s),
    }
    companies, changes, status = {}, {}, {}
    for name, fn in fetchers.items():
        try:
            cur = fn(); cur.update({"fetched_at":ts, "source_status":"ok", "last_success":ts})
            companies[name] = cur; changes[name] = delta(old.get(name), cur)
            status[name] = {"ok":True, "last_success":ts, "inventory_count":cur.get("inventory_count"), "inventory_fingerprint":cur.get("inventory_fingerprint"), "board_total":cur.get("board_total"), "query_counts":cur.get("query_counts")}
        except Exception as e:
            if old.get(name):
                cur = dict(old[name]); cur.update({"source_status":"error", "last_attempt":ts, "source_error":f"{type(e).__name__}: {e}"}); companies[name] = cur
            status[name] = {"ok":False, "last_success":(old.get(name) or {}).get("last_success"), "last_attempt":ts, "error":f"{type(e).__name__}: {e}"}
            changes[name] = {"source_error":status[name]["error"], "changes_suppressed":True}
    run_status = "ok" if all(x["ok"] for x in status.values()) else "partial_failure"
    latest = {"schema_version":2, "fetched_at":ts, "run_status":run_status, "companies":companies, "note":"Tesla intentionally excluded from GitHub runner; monitor exact official Tesla state JSON via web-fetch transport."}
    latest_path.write_text(json.dumps(latest, indent=2, sort_keys=True)+"\n")
    (STATE/"runner-delta.json").write_text(json.dumps({"schema_version":2,"fetched_at":ts,"companies":changes}, indent=2, sort_keys=True)+"\n")
    (STATE/"runner-status.json").write_text(json.dumps({"schema_version":2,"fetched_at":ts,"run_status":run_status,"companies":status}, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"fetched_at":ts,"run_status":run_status,"companies":status}, indent=2))
    return 0 if run_status == "ok" else 2

if __name__ == "__main__":
    sys.exit(main())
