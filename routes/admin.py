import uuid
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from utils.auth import auth
from utils.db import create_key, get_all_keys

router = APIRouter()

# ✅ Templates load
templates = Jinja2Templates(directory="templates")


# ✅ Input model (JSON body)
class CreateKeyRequest(BaseModel):
    username: str
    days: int
    limit: int
    is_admin: bool = False


# 🌐 Admin Panel Page
@router.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request, admin_key: str = Query(...)):
    # ✅ Auth check
    if not auth(admin_key):
        return HTMLResponse("<h1>Unauthorized</h1>", status_code=401)

    # ✅ DB से सभी keys ले आओ
    keys = get_all_keys()

    # ✅ Render template with keys
    return templates.TemplateResponse(
        "admin.html", {
            "request": request,
            "keys": keys,
            "admin_key": admin_key
        }
    )


# 🌐 Key Create API (JSON)
@router.post("/create", response_class=JSONResponse)
async def create(data: CreateKeyRequest, admin_key: str = Query(...)):
    # ✅ Auth check
    if not auth(admin_key):
        return JSONResponse({"status": False, "error": "Unauthorized"}, status_code=401)

    # ✅ Generate new key
    k = str(uuid.uuid4())
    doc = create_key(
        data.username,
        k,
        data.limit,
        data.days,
        is_admin=data.is_admin
    )

    return {
        "status": True,
        "key": k,
        "expires_at": doc["expires_at"].isoformat()
                            }
