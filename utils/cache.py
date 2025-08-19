import httpx
from datetime import datetime
from .db import cache
from .fetcher import hash_query
from config import BOT_TOKEN, CHANNEL_ID

def cache_get_by_url(url: str):
    return cache.find_one({"hash": hash_query(url)})

def cache_get(qhash: str):
    return cache.find_one({"hash": qhash})

def cache_put(record: dict):
    record["created_at"] = datetime.utcnow()
    cache.update_one({"hash": record["hash"]}, {"$set": record}, upsert=True)

async def upload_to_channel_audio(src_url: str, caption: str):
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(api_url, data={"chat_id": CHANNEL_ID, "caption": caption, "audio": src_url})
        j = r.json()
    if not j.get("ok"):
        raise RuntimeError(str(j))
    msg = j["result"]
    file_id = msg["audio"]["file_id"]
    message_id = msg["message_id"]
    return file_id, message_id

async def cache_audio_flow(query_url: str, meta: dict):
    qhash = hash_query(query_url)
    existing = cache_get(qhash)
    if existing:
        return {
            **meta,
            "cached": True,
            "file_id": existing.get("file_id"),
            "message_id": existing.get("message_id")
        }
    caption = f"{meta.get('title','Audio')}\n\nID: {qhash}"
    file_id, message_id = await upload_to_channel_audio(meta["src_url"], caption)
    rec = {
        "hash": qhash,
        "type": meta.get("type","audio"),
        "quality": meta.get("quality"),
        "title": meta.get("title"),
        "duration": meta.get("duration"),
        "src_url": meta.get("src_url"),
        "file_id": file_id,
        "message_id": message_id,
    }
    cache_put(rec)
    return {**meta, "cached": False, "file_id": file_id, "message_id": message_id}