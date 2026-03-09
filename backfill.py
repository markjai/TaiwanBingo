"""
賓果賓果歷史資料補齊腳本
用法: python backfill.py [year_from] [year_to]
預設從 2024 爬到今天
"""
import asyncio
import sys
from datetime import date, timedelta

# Windows asyncio fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, ".")

from loguru import logger
from taiwan_bingo.db.engine import async_session_factory
from taiwan_bingo.scraper.bingo_scraper import BingoScraper


async def run_backfill(year_from: int = 2024, year_to: int | None = None):
    today = date.today()
    if year_to is None:
        year_to = today.year

    start = date(year_from, 1, 1)
    end = today

    total_days = (end - start).days + 1
    total_inserted = 0
    total_failed = 0
    done = 0

    scraper = BingoScraper()
    logger.info("Starting backfill: {} -> {} ({} days)", start, end, total_days)

    current = start
    async with async_session_factory() as session:
        while current <= end:
            try:
                draws = await scraper._fetch_day(current)
                if draws:
                    from taiwan_bingo.db.crud.bingo import bulk_upsert
                    inserted = await bulk_upsert(session, draws)
                    await session.commit()
                    total_inserted += inserted
                    if inserted > 0:
                        logger.info("[{}/{}] {} -> {} new (total {})",
                                    done + 1, total_days, current, inserted, total_inserted)
                else:
                    logger.debug("[{}/{}] {} -> 0 draws", done + 1, total_days, current)
            except Exception as e:
                total_failed += 1
                logger.warning("[{}/{}] {} FAILED: {}", done + 1, total_days, current, e)
                try:
                    await session.rollback()
                except Exception:
                    pass

            done += 1
            current += timedelta(days=1)

            # Progress every 30 days
            if done % 30 == 0:
                pct = done / total_days * 100
                logger.info("--- Progress: {}/{} days ({:.1f}%), total_inserted={}, failed={} ---",
                            done, total_days, pct, total_inserted, total_failed)

    logger.info("=== Backfill complete: {} draws inserted, {} days failed ===",
                total_inserted, total_failed)
    return total_inserted


if __name__ == "__main__":
    year_from = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    year_to = int(sys.argv[2]) if len(sys.argv) > 2 else None
    asyncio.run(run_backfill(year_from, year_to))
