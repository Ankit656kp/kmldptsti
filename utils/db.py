from datetime import datetime, date, timedelta
from pymongo import MongoClient, ASCENDING
from config import MONGO_URI, DB_NAME
import csv, io

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

keys = db["api_keys"]      # {key, username, limit, expires_at, is_admin, requests_today, last_reset, total_requests}
logs = db["api_logs"]      # {ts, key, endpoint, status, ms, query, error?}
cache = db["cache"]        # {hash, type, quality, title, duration, src_url, file_id, message_id, created_at}

# Indexes (idempotent)
keys.create_index([("key", ASCENDING)], unique=True)
cache.create_index([("hash", ASCENDING)], unique=True)
logs.create_index([("ts", ASCENDING)])

def ensure_daily_reset(k: dict):
    """Reset per-day counter at midnight."""
    today = date.today().isoformat()
    if k.get("last_reset") != today:
        keys.update_one({"key": k["key"]}, {"$set": {"last_reset": today, "requests_today": 0}})
        k["last_reset"] = today
        k["requests_today"] = 0
    return k

def get_key(key: str):
    k = keys.find_one({"key": key})
    if not k: return None
    k = ensure_daily_reset(k)
    # expiry check
    if k.get("expires_at") and datetime.utcnow() > k["expires_at"]:
        return "expired"
    return k

def inc_usage(key: str):
    keys.update_one({"key": key}, {"$inc": {"requests_today": 1, "total_requests": 1}}, upsert=False)

def create_key(username: str, key: str, limit: int, days: int, is_admin: bool=False):
    expires = datetime.utcnow() + timedelta(days=days)
    doc = {
        "username": username, "key": key, "limit": int(limit),
        "expires_at": expires, "is_admin": bool(is_admin),
        "requests_today": 0, "total_requests": 0,
        "last_reset": date.today().isoformat()
    }
    keys.insert_one(doc)
    return doc

def delete_key(key: str):
    keys.delete_one({"key": key})

def recent_logs(limit_n=20):
    cur = logs.find({}, {"_id":0}).sort("ts", -1).limit(limit_n)
    out = []
    for d in cur:
        d["ts"] = d["ts"].isoformat() if isinstance(d.get("ts"), datetime) else d.get("ts")
        out.append(d)
    return out

def add_log(key: str, endpoint: str, ok: bool, ms: int, query: dict, error: str|None=None):
    logs.insert_one({
        "ts": datetime.utcnow(), "key": key, "endpoint": endpoint,
        "status": ok, "ms": ms, "query": query, "error": error
    })

def stats_today():
    from datetime import date
    today = date.today().isoformat()
    total_today = list(keys.aggregate([
        {"$match": {"last_reset": today}},
        {"$group": {"_id": 1, "sum": {"$sum": "$requests_today"}}}
    ]))
    return total_today[0]["sum"] if total_today else 0

def totals():
    total_keys = keys.count_documents({})
    total_requests = list(keys.aggregate([{"$group":{"_id":1,"s":{"$sum":"$total_requests"}}}]))
    return total_keys, (total_requests[0]["s"] if total_requests else 0)

# ---- New aggregations ----
def error_rate_window(days: int = 7):
    """
    Returns error rate (%) in last `days` days.
    """
    since = datetime.utcnow() - timedelta(days=days)
    total = logs.count_documents({"ts": {"$gte": since}})
    errors = logs.count_documents({"ts": {"$gte": since}, "status": False})
    if total == 0:
        return 0.0
    return round((errors / total) * 100, 2)

def requests_over_week():
    """
    Returns a list of 7 points: Mon..Sun counts (UTC).
    """
    today = datetime.utcnow().date()
    res = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        start = datetime(d.year, d.month, d.day)
        end = start + timedelta(days=1)
        cnt = logs.count_documents({"ts": {"$gte": start, "$lt": end}})
        res.append({"day": d.strftime("%a"), "count": cnt})
    return res

def per_key_usage(limit:int=10):
    """
    Top keys usage distribution.
    """
    agg = list(keys.aggregate([
        {"$project": {"username":1,"key":1,"total_requests":1}},
        {"$sort": {"total_requests": -1}},
        {"$limit": limit}
    ]))
    return [{"label": a.get("username") or a.get("key")[:8], "value": a.get("total_requests",0)} for a in agg]

def export_logs_csv():
    """
    Returns CSV string of recent logs (all).
    """
    cur = logs.find({}).sort("ts", -1)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ts","key","endpoint","status","ms","query","error"])
    for r in cur:
        ts = r["ts"].isoformat() if isinstance(r.get("ts"), datetime) else r.get("ts")
        writer.writerow([ts, r.get("key"), r.get("endpoint"), r.get("status"), r.get("ms"), str(r.get("query")), r.get("error") or ""])
    return output.getvalue()