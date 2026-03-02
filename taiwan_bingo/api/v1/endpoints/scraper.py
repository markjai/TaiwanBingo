from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.api.deps import get_db
from taiwan_bingo.schemas.bingo import ScrapeRequest, ScrapeStatusSchema
from taiwan_bingo.services.bingo_service import trigger_scrape, backfill_scrape

router = APIRouter()


@router.post("/run", response_model=ScrapeStatusSchema, summary="手動觸發爬取最新資料")
async def run_scraper(db: AsyncSession = Depends(get_db)):
    result = await trigger_scrape(db)
    return result


@router.post("/backfill", response_model=list[ScrapeStatusSchema], summary="補齊歷史資料")
async def backfill(
    request: ScrapeRequest,
    db: AsyncSession = Depends(get_db),
):
    if request.year_from > request.year_to:
        raise HTTPException(status_code=400, detail="year_from must be <= year_to")
    results = await backfill_scrape(db, request.year_from, request.year_to)
    return results
