from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.api.deps import get_db
from taiwan_bingo.db.crud import bingo as crud
from taiwan_bingo.schemas.bingo import BingoDrawSchema, PaginatedResponse

router = APIRouter()


@router.get("/latest", response_model=BingoDrawSchema, summary="最新一期開獎")
async def get_latest(db: AsyncSession = Depends(get_db)):
    draw = await crud.get_latest(db)
    if not draw:
        raise HTTPException(status_code=404, detail="No draws found")
    return draw


@router.get("", response_model=PaginatedResponse, summary="分頁查詢開獎紀錄")
async def get_draws(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=200, description="每頁筆數"),
    date_from: date | None = Query(None, description="起始日期 YYYY-MM-DD"),
    date_to: date | None = Query(None, description="結束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    draws, total = await crud.get_draws(
        db, page=page, page_size=page_size, date_from=date_from, date_to=date_to
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=[BingoDrawSchema.model_validate(d) for d in draws],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{term}", response_model=BingoDrawSchema, summary="依期別查詢")
async def get_by_term(term: str, db: AsyncSession = Depends(get_db)):
    draw = await crud.get_by_term(db, term)
    if not draw:
        raise HTTPException(status_code=404, detail=f"Draw term {term!r} not found")
    return draw
