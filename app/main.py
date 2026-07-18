from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import ensure_data_dirs
from app.routers import api, pages

ensure_data_dirs()

app = FastAPI(title="Homelab Index", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages.router)
app.include_router(api.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
