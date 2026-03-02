from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.api.deps import get_db
from taiwan_bingo.schemas.statistics import (
    NumberFrequency,
    HotColdAnalysis,
    GapAnalysis,
    SectorAnalysis,
    PairFrequency,
    BiasReport,
)
from taiwan_bingo.services.statistics_service import (
    get_number_frequency,
    get_hot_cold_analysis,
    get_gap_analysis,
    get_sector_analysis,
    get_pair_frequency,
    get_bias_report,
)

router = APIRouter()


@router.get("/frequency", response_model=list[NumberFrequency], summary="號碼出現頻率")
async def frequency(
    window: int = Query(100, ge=10, le=5000, description="最近 N 期"),
    db: AsyncSession = Depends(get_db),
):
    return await get_number_frequency(db, window=window)


@router.get("/hot-cold", response_model=HotColdAnalysis, summary="冷熱號分析")
async def hot_cold(
    window: int = Query(100, ge=10, le=5000),
    top_n: int = Query(10, ge=5, le=20),
    db: AsyncSession = Depends(get_db),
):
    return await get_hot_cold_analysis(db, window=window, top_n=top_n)


@router.get("/gaps", response_model=GapAnalysis, summary="遺漏值分析")
async def gaps(
    window: int = Query(100, ge=10, le=5000),
    db: AsyncSession = Depends(get_db),
):
    return await get_gap_analysis(db, window=window)


@router.get("/sectors", response_model=SectorAnalysis, summary="四區號碼分布")
async def sectors(
    window: int = Query(100, ge=10, le=5000),
    db: AsyncSession = Depends(get_db),
):
    return await get_sector_analysis(db, window=window)


@router.get("/pairs", response_model=list[PairFrequency], summary="號碼同期共現頻率")
async def pairs(
    window: int = Query(200, ge=50, le=5000),
    top_n: int = Query(20, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await get_pair_frequency(db, window=window, top_n=top_n)


@router.get("/bias", response_model=BiasReport, summary="卡方偏差檢定")
async def bias(
    window: int = Query(200, ge=50, le=5000),
    db: AsyncSession = Depends(get_db),
):
    return await get_bias_report(db, window=window)
