from datetime import date

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

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
    """Backfill data year by year (AD years), all 12 months."""
    results: list[ScrapeStatusSchema] = []
    today = date.today()

    for year in range(year_from, year_to + 1):
        for month in range(1, 13):
            if date(year, month, 1) > today:
                break
            logger.info("Backfill: {}/{}", year, month)
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
