from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.api.deps import get_db
from taiwan_bingo.schemas.ml import (
    TrainRequest,
    TrainResponse,
    PredictionResponse,
    PickNPredictionResponse,
    ModelInfo,
    EvaluateResponse,
    BacktestRequest,
    BacktestResponse,
)
from taiwan_bingo.services.ml_service import (
    train_model,
    get_prediction,
    get_dqn_prediction,
    list_models,
    evaluate_model,
    backtest_model,
)

router = APIRouter()


@router.post("/train", response_model=TrainResponse, summary="訓練模型")
async def train(
    request: TrainRequest,
    db: AsyncSession = Depends(get_db),
):
    return await train_model(db, request.model_type, request.pick_count)


@router.get("/predict", response_model=PredictionResponse, summary="取得預測號碼")
async def predict(
    model_type: str = Query("ensemble", description="模型類型"),
    pick_count: int = Query(20, ge=5, le=20, description="預測號碼數量"),
    db: AsyncSession = Depends(get_db),
):
    result = await get_prediction(db, model_type=model_type, pick_count=pick_count)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No trained model found for model_type={model_type!r}. Train first.",
        )
    return result


@router.get("/models", response_model=list[ModelInfo], summary="已訓練模型清單")
async def get_models(db: AsyncSession = Depends(get_db)):
    return await list_models(db)


@router.post("/evaluate", response_model=EvaluateResponse, summary="評估預測準確率")
async def evaluate(
    model_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await evaluate_model(db, model_type=model_type)


@router.post("/backtest", response_model=BacktestResponse, summary="回測模型")
async def backtest(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db),
):
    return await backtest_model(db, request)


@router.get("/dqn-predict", response_model=PickNPredictionResponse, summary="DQN Pick-N 預測")
async def dqn_predict(
    pick_count: int = Query(3, ge=3, le=5, description="取幾個號碼 (3/4/5)"),
    db: AsyncSession = Depends(get_db),
):
    result = await get_dqn_prediction(db, pick_count=pick_count)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No trained DQN model found for pick_count={pick_count}. Train dqn_{pick_count} first.",
        )
    return result
