from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.models.scrape_log import ScrapeLog


class BaseScraper(ABC):
    @abstractmethod
    async def fetch_latest(self, session: AsyncSession) -> int:
        """Fetch and store the latest draws. Returns inserted count."""

    @abstractmethod
    async def fetch_by_month(self, session: AsyncSession, year: int, month: int) -> int:
        """Fetch draws for a specific year/month. Returns inserted count."""

    async def run_with_logging(
        self,
        session: AsyncSession,
        action: str = "latest",
        **kwargs,
    ) -> ScrapeLog:
        log = ScrapeLog(status="running", started_at=datetime.now())
        session.add(log)
        await session.flush()

        try:
            if action == "latest":
                inserted = await self.fetch_latest(session)
            else:
                inserted = await self.fetch_by_month(
                    session, kwargs["year"], kwargs["month"]
                )
            log.status = "success"
            log.records_inserted = inserted
        except Exception as e:
            log.status = "error"
            log.error_message = str(e)
        finally:
            log.finished_at = datetime.now()

        return log
