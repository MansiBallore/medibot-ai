"""
MediBot AI — FastAPI Backend Entry Point
Production-level AI Healthcare Assistant
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import logging
import time
import os
from pathlib import Path

from api.chat import router as chat_router
from api.auth import router as auth_router
from api.diagnosis import router as diagnosis_router
from api.analytics import router as analytics_router
from api.ocr import router as ocr_router
from core.config import settings
from core.database import init_db

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/medibot.log", mode="a"),
    ],
)
logger = logging.getLogger("medibot")

# ─── App Init ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MediBot AI Healthcare Assistant",
    description="Advanced Generative AI Healthcare Assistant with RAG, ML predictions, and multi-modal support",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} [{duration}ms]")
    return response


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(chat_router,      prefix="/api/chat",      tags=["Chat & AI"])
app.include_router(diagnosis_router, prefix="/api/diagnosis", tags=["Diagnosis & ML"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ocr_router,       prefix="/api/ocr",       tags=["OCR & Documents"])

# ─── Static Files & Templates ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ─── Startup / Shutdown ───────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    await init_db()
    logger.info("🚀 MediBot AI started successfully")


@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 MediBot AI shutting down")


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "2.0.0", "service": "MediBot AI"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG,
        log_level="info",
    )
