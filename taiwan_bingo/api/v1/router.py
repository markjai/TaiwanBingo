from fastapi import APIRouter

from taiwan_bingo.api.v1.endpoints import draws, scraper, statistics, ml

api_router = APIRouter()

api_router.include_router(draws.router, prefix="/draws", tags=["開獎資料"])
api_router.include_router(scraper.router, prefix="/scraper", tags=["爬蟲"])
api_router.include_router(statistics.router, prefix="/stats", tags=["統計分析"])
api_router.include_router(ml.router, prefix="/ml", tags=["ML 預測"])
