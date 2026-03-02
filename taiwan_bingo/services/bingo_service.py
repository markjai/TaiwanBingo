from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.crud.bingo import bulk_upsert
from taiwan_bingo.db.models.scrape_log import ScrapeLog
from taiwan_bingo.scraper.bingo_scraper import BingoScraper
from taiwan_bingo.schemas.bingo import ScrapeStatusSchema

_scraper = BingoScraper()


async def trigger_scrape(session: AsyncSession) -> ScrapeStatusSchema:
    log = await _scraper.run_with_logging(session, action="latest")
    await session.commit()
    return ScrapeStatusSchema(
        status=log.status,
        records_found=log.records_found or 0,
        records_inserted=log.records_inserted or 0,
        error_message=log.error_message,
    )


async def backfill_scrape(
    session: AsyncSession,
    year_from: int,
    year_to: int,
) -> list[ScrapeStatusSchema]:
    """Backfill data year by year, all 12 months."""
    results: list[ScrapeStatusSchema] = []
    for year in range(year_from, year_to + 1):
        for month in range(1, 13):
            if year == datetime.now().year - 1911 and month > datetime.now().month:
                break
            log = await _scraper.run_with_logging(
                session, action="month", year=year, month=month
            )
            await session.commit()
            results.append(
                ScrapeStatusSchema(
                    status=log.status,
                    records_found=log.records_found or 0,
                    records_inserted=log.records_inserted or 0,
                    error_message=log.error_message,
                )
            )
    return results
