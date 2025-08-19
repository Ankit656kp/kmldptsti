from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from routes import user, admin

app = FastAPI(title="Komal API", description="Super Fast Music API 🚀", version="1.0.0")

# templates
templates = Jinja2Templates(directory="templates")

# include routers
app.include_router(user.router, prefix="/api", tags=["User API"])
app.include_router(admin.router, prefix="/admin", tags=["Admin Panel"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Komal API"})