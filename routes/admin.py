import uuid
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from utils.db import is_admin_key, create_key, get_all_keys

router = APIRouter()
templates = Jinja2Templates(directory="templates")

class CreateKeyRequest(BaseModel):
    username: str
    days: int
    limit: int
    is_admin: bool = False

# Admin Panel page
@router.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request, admin_key: str = Query(None)):
    if not admin_key or not is_admin_key(admin_key):
        return HTMLResponse("<h1>Unauthorized ❌</h1>", status_code=401)

    keys = get_all_keys()
    return templates.TemplateResponse(
        "admin.html", {"request": request, "keys": keys, "admin_key": admin_key}
    )

# Create new key
@router.post("/create", response_class=JSONResponse)
async def create_key_api(data: CreateKeyRequest, admin_key: str = Query(None)):
    if not admin_key or not is_admin_key(admin_key):
        return JSONResponse({"status": False, "error": "Unauthorized"}, status_code=401)

    new_key = str(uuid.uuid4())
    doc = create_key(
        data.username,
        new_key,
        data.limit,
        data.days,
        is_admin=data.is_admin
    )
    return {
        "status": True,
        "key": new_key,
        "expires_at": doc["expires_at"].isoformat()
    }
