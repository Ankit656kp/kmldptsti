import httpx
from hashlib import md5

def hash_query(q: str) -> str:
    return md5(q.strip().encode()).hexdigest()

# ---------- AUDIO (MP3) ----------
async def fetch_audio_mp3(youtube_url: str):
    """
    Worker from your brief. Fixed at 128kbps (as their API returns).
    """
    endpoint = "https://jerrycoder.oggyapi.workers.dev/ytmp3"
    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.get(endpoint, params={"url": youtube_url})
        j = r.json()
    if j.get("status"):
        return {
            "type": "audio",
            "quality": j.get("quality", "128 kbps"),
            "title": j.get("title"),
            "duration": j.get("duration"),
            "src_url": j.get("url")
        }
    return None

# ---------- VIDEO (QUALITY LADDER + FALLBACKS) ----------
async def _try_generic_provider(base_url: str, youtube_url: str, quality: str|None):
    params = {"url": youtube_url}
    if quality:
        params["quality"] = quality
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(base_url, params=params)
        j = r.json()
    if j.get("status"):
        res = j.get("result", {})
        return {
            "type": "video",
            "quality": res.get("quality") or quality or "auto",
            "title": res.get("title"),
            "duration": res.get("duration"),
            "src_url": res.get("url")
        }
    return None

async def fetch_video_stream(youtube_url: str, preferred:list[str]|None=None):
    """
    Quality ladder: 1080 -> 720 -> 480 -> 360 -> 240
    Fallback over multiple providers (add your working providers below).
    Replace 'https://xxxxxxxxxxx' with your real provider URLs.
    """
    ladder = preferred or ["1080","720","480","360","240"]

    providers = [
        # PRIMARY (you provided example schema)
        "https://xxxxxxxxxxx",
        # You can add more providers below that follow the same schema:
        # "https://your-second-provider.example/api",
    ]

    for q in ladder:
        for p in providers:
            try:
                data = await _try_generic_provider(p, youtube_url, q)
                if data and data.get("src_url"):
                    return data
            except Exception:
                continue

    # last attempt: providers with no quality param
    for p in providers:
        try:
            data = await _try_generic_provider(p, youtube_url, None)
            if data and data.get("src_url"):
                return data
        except Exception:
            continue

    return None