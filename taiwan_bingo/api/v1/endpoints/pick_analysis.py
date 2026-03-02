"""Pick-N analysis API endpoints (n = 3, 4, 5)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.api.deps import get_db
from taiwan_bingo.schemas.statistics import (
    PickNCombination,
    PickNExpectedValue,
    PickNHitAnalysis,
    PickNRecommendation,
)
from taiwan_bingo.services.statistics_service import (
    get_pick_n_expected_value,
    get_pick_n_hit_analysis,
    get_pick_n_hot_combinations,
    get_pick_n_recommend,
)

router = APIRouter()

_VALID_N = {3, 4, 5}


def _check_n(n: int) -> None:
    if n not in _VALID_N:
        raise HTTPException(status_code=422, detail=f"n must be 3, 4, or 5 (got {n})")


@router.get("/{n}/hit-analysis", response_model=PickNHitAnalysis, summary="Pick-N 命中率分析")
async def hit_analysis(
    n: int,
    window: int = Query(1000, ge=50, le=5000),
    db: AsyncSession = Depends(get_db),
):
    _check_n(n)
    return await get_pick_n_hit_analysis(db, pick_count=n, window=window)


@router.get("/{n}/hot-combinations", response_model=list[PickNCombination], summary="Pick-N 熱門組合")
async def hot_combinations(
    n: int,
    window: int = Query(500, ge=50, le=500),
    top_n: int = Query(20, ge=5, le=50),
    db: AsyncSession = Depends(get_db),
):
    _check_n(n)
    return await get_pick_n_hot_combinations(db, pick_count=n, window=window, top_n=top_n)


@router.get("/{n}/recommend", response_model=PickNRecommendation, summary="Pick-N AI 推薦號碼")
async def recommend(
    n: int,
    window: int = Query(200, ge=50, le=2000),
    db: AsyncSession = Depends(get_db),
):
    _check_n(n)
    return await get_pick_n_recommend(db, pick_count=n, window=window)


@router.get("/{n}/expected-value", response_model=PickNExpectedValue, summary="Pick-N 期望值分析")
async def expected_value(
    n: int,
    window: int = Query(1000, ge=50, le=5000),
    db: AsyncSession = Depends(get_db),
):
    _check_n(n)
    return await get_pick_n_expected_value(db, pick_count=n, window=window)
