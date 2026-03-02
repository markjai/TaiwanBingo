from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from taiwan_bingo.db.engine import async_session_factory
from taiwan_bingo.scraper.bingo_scraper import BingoScraper
from taiwan_bingo.config import settings

_scheduler = AsyncIOScheduler()
_scraper = BingoScraper()


async def _scrape_latest():
    logger.info("Scheduled: fetching latest bingo draws")
    async with async_session_factory() as session:
        await _scraper.run_with_logging(session, action="latest")
        await session.commit()


def start_scheduler():
    interval = settings.BINGO_SCRAPE_INTERVAL_MINUTES
    _scheduler.add_job(
        _scrape_latest,
        "interval",
        minutes=interval,
        id="bingo_scrape",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(f"Scheduler started: every {interval} minutes")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
