import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from taiwan_bingo.config import settings
from taiwan_bingo.db.engine import engine
from taiwan_bingo.db.base import Base

# Windows Python 3.13 asyncio fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Logging setup
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logger.add(
    log_dir / "app.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    encoding="utf-8",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    settings.MODEL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # Start scheduler if enabled
    if settings.SCRAPER_ENABLED:
        from taiwan_bingo.scraper.scheduler import start_scheduler
        start_scheduler()
        logger.info("Scraper scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if settings.SCRAPER_ENABLED:
        from taiwan_bingo.scraper.scheduler import stop_scheduler
        stop_scheduler()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# Static files & templates
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# API router
from taiwan_bingo.api.v1.router import api_router  # noqa: E402
app.include_router(api_router, prefix="/api/v1")


# ── Page routes ────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/history", include_in_schema=False)
async def history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/analysis", include_in_schema=False)
async def analysis(request: Request):
    return templates.TemplateResponse("analysis.html", {"request": request})


@app.get("/predictions", include_in_schema=False)
async def predictions(request: Request):
    return templates.TemplateResponse("predictions.html", {"request": request})
