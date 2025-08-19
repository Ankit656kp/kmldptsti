import uuid
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils.auth import auth
from utils.db import create_key

router = APIRouter()


# ✅ Input model (JSON body)
class CreateKeyRequest(BaseModel):
    username: str
    days: int
    limit: int
    is_admin: bool = False


@router.post("/create", response_class=JSONResponse)
async def create(data: CreateKeyRequest, admin_key: str = Query(...)):
    # ✅ Check admin auth
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
