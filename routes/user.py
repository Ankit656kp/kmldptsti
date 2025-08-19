import time
from fastapi import APIRouter, Query, Response
from utils.db import get_key, inc_usage, add_log, keys
from utils.fetcher import fetch_audio_mp3, fetch_video_stream
from utils.cache import cache_audio_flow, cache_get_by_url

router = APIRouter()

@router.get("/media")
async def media(
    response: Response,
    url: str = Query(..., description="YouTube URL"),
    type: str = Query("audio", regex="^(audio|video)$"),
    key: str = Query(...),
    prefer: str | None = Query(None, description="Comma separated qualities e.g. 1080,720,360")
):
    t0, err = time.time(), None
    ladder = None
    if prefer:
        ladder = [q.strip() for q in prefer.split(",") if q.strip()]

    try:
        # key verify
        k = get_key(key)
        if not k:
            return {"status": False, "error": "Invalid API key"}
        if k == "expired":
            return {"status": False, "error": "API key expired"}

        # set Rate-Limit headers
        remaining = max(0, int(k.get("limit",0)) - int(k.get("requests_today",0)))
        response.headers["X-RateLimit-Limit"] = str(k.get("limit",0))
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        if k["requests_today"] >= int(k["limit"]):
            response.headers["X-RateLimit-Remaining"] = "0"
            return {"status": False, "error": "Daily limit exceeded"}

        # media fetch
        if type == "audio":
            meta = await fetch_audio_mp3(url)
            if not meta:
                return {"status": False, "error": "Upstream (audio) failed"}
            meta = await cache_audio_flow(url, meta)
        else:
            meta = await fetch_video_stream(url, preferred=ladder)
            if not meta:
                return {"status": False, "error": "Upstream (video) failed"}

        inc_usage(key)
        # update remaining after increment
        response.headers["X-RateLimit-Remaining"] = str(max(0, int(k.get("limit",0)) - (int(k.get("requests_today",0) + 1))))
        return {"status": True, "result": meta}

    except Exception as e:
        err = str(e)
        return {"status": False, "error": err}
    finally:
        ms = int((time.time() - t0) * 1000)
        add_log(key if 'key' in locals() else "unknown", "/api/media", err is None, ms, {"url": url, "type": type, "prefer": prefer}, err)

@router.get("/health")
async def health():
    total_keys = keys.count_documents({})
    return {"status": True, "service": "ok", "total_keys": total_keys}

@router.get("/usage")
async def usage(key: str = Query(...)):
    k = get_key(key)
    if not k:
        return {"status": False, "error": "Invalid API key"}
    if k == "expired":
        return {"status": False, "error": "API key expired"}
    return {
        "status": True,
        "key": k["key"],
        "username": k.get("username"),
        "today_used": k.get("requests_today", 0),
        "daily_limit": k.get("limit", 0),
        "total_requests": k.get("total_requests", 0),
        "expires_at": k.get("expires_at").isoformat() if k.get("expires_at") else None
    }

@router.get("/resolve_cache")
async def resolve_cache(url: str = Query(...), key: str = Query(...)):
    k = get_key(key)
    if not k or k == "expired":
        return {"status": False, "error": "Invalid or expired key"}
    doc = cache_get_by_url(url)
    if not doc:
        return {"status": True, "cached": False}
    return {"status": True, "cached": True, "file_id": doc.get("file_id"), "message_id": doc.get("message_id")}