from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.models.bingo_draw import BingoDraw


async def get_latest(session: AsyncSession) -> BingoDraw | None:
    result = await session.execute(
        select(BingoDraw).order_by(BingoDraw.draw_datetime.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_by_term(session: AsyncSession, term: str) -> BingoDraw | None:
    result = await session.execute(
        select(BingoDraw).where(BingoDraw.draw_term == term)
    )
    return result.scalar_one_or_none()


async def get_draws(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[BingoDraw], int]:
    query = select(BingoDraw)
    if date_from:
        query = query.where(func.date(BingoDraw.draw_datetime) >= date_from)
    if date_to:
        query = query.where(func.date(BingoDraw.draw_datetime) <= date_to)
    query = query.order_by(BingoDraw.draw_datetime.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await session.execute(query)
    return list(result.scalars().all()), total


async def get_all_numbers(session: AsyncSession, limit: int = 5000) -> list[list[int]]:
    """Return list of number arrays ordered by draw_datetime ASC (for ML)."""
    result = await session.execute(
        select(BingoDraw.numbers)
        .order_by(BingoDraw.draw_datetime.asc())
        .limit(limit)
    )
    return [row[0] for row in result.all()]


async def bulk_upsert(session: AsyncSession, draws: list[dict]) -> int:
    """Insert draws, skip on conflict. Returns inserted count."""
    if not draws:
        return 0
    stmt = insert(BingoDraw).values(draws)
    stmt = stmt.on_conflict_do_nothing(index_elements=["draw_term"])
    result = await session.execute(stmt)
    return result.rowcount
