import uuid
from datetime import datetime
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from config import ADMIN_KEY, PROJECT_NAME
from utils.db import create_key, delete_key, keys, totals, stats_today, recent_logs
from utils.db import error_rate_window, requests_over_week, per_key_usage, export_logs_csv

templates = Jinja2Templates(directory="templates")
router = APIRouter()

def auth(admin_key: str):
    return admin_key == ADMIN_KEY

@router.get("/", response_class=HTMLResponse)
async def admin_home(request: Request, admin_key: str = Query(...)):
    if not auth(admin_key):
        return HTMLResponse("<h3>Unauthorized</h3>", status_code=401)

    total_keys_count, total_requests = totals()
    today = stats_today()
    active = keys.count_documents({"expires_at": {"$gt": datetime.utcnow()}})
    error_rate = error_rate_window(7)
    logs = recent_logs(20)
    weekly = requests_over_week()
    perkey = per_key_usage(10)

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "project": PROJECT_NAME,
        "total_requests": total_requests,
        "today_requests": today,
        "active_keys": active,
        "error_rate": error_rate,
        "logs": logs,
        "admin_key": admin_key,
        "weekly": weekly,
        "perkey": perkey
    })

@router.post("/create", response_class=JSONResponse)
async def create(username: str, days: int, limit: int, admin_key: str = Query(...), is_admin: bool=False):
    if not auth(admin_key):
        return JSONResponse({"status": False, "error": "Unauthorized"}, status_code=401)
    k = str(uuid.uuid4())
    doc = create_key(username, k, limit, days, is_admin=is_admin)
    return {"status": True, "key": k, "expires_at": doc["expires_at"].isoformat()}

@router.post("/delete", response_class=JSONResponse)
async def delete(target_key: str, admin_key: str = Query(...)):
    if not auth(admin_key):
        return JSONResponse({"status": False, "error": "Unauthorized"}, status_code=401)
    delete_key(target_key)
    return {"status": True}

@router.get("/keys", response_class=JSONResponse)
async def list_keys(admin_key: str = Query(...)):
    if not auth(admin_key):
        return JSONResponse({"status": False, "error": "Unauthorized"}, status_code=401)
    data = []
    for k in keys.find({}, {"_id":0}):
        k["expires_at"] = k["expires_at"].isoformat() if k.get("expires_at") else None
        data.append(k)
    return {"status": True, "keys": data}

@router.get("/stats", response_class=JSONResponse)
async def stats(admin_key: str = Query(...)):
    if not auth(admin_key):
        return JSONResponse({"status": False, "error": "Unauthorized"}, status_code=401)
    return {
        "status": True,
        "error_rate": error_rate_window(7),
        "weekly": requests_over_week(),
        "perkey": per_key_usage(20)
    }

@router.get("/export_logs", response_class=PlainTextResponse)
async def export_logs(admin_key: str = Query(...)):
    if not auth(admin_key):
        return PlainTextResponse("Unauthorized", status_code=401)
    csv_data = export_logs_csv()
    headers = {"Content-Disposition": 'attachment; filename="api_logs.csv"'}
    return PlainTextResponse(content=csv_data, media_type="text/csv", headers=headers)