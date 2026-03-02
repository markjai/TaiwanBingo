from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.crud import ml as ml_crud
from taiwan_bingo.ml.inference.model_registry import invalidate_cache
from taiwan_bingo.ml.inference.predictor import predict as do_predict
from taiwan_bingo.ml.training.trainer import train as do_train
from taiwan_bingo.schemas.ml import (
    BacktestRequest,
    BacktestResponse,
    BacktestSummary,
    EvaluateResponse,
    ModelInfo,
    PickNPredictionResponse,
    PredictionResponse,
    TrainResponse,
)
from taiwan_bingo.db.crud.bingo import get_all_numbers


async def train_model(
    session: AsyncSession,
    model_type: str = "ensemble",
    pick_count: int = 20,
) -> TrainResponse:
    model, metrics, model_id = await do_train(session, model_type=model_type, pick_count=pick_count)
    invalidate_cache(model_type)
    return TrainResponse(
        model_id=model_id,
        model_type=model_type,
        version=metrics.get("version", ""),
        metrics=metrics,
        message=f"Model '{model_type}' trained successfully on {metrics.get('trained_on', '?')} draws.",
    )


async def get_prediction(
    session: AsyncSession,
    model_type: str = "ensemble",
    pick_count: int = 20,
) -> PredictionResponse | None:
    return await do_predict(session, model_type=model_type, pick_count=pick_count)


async def list_models(session: AsyncSession) -> list[ModelInfo]:
    records = await ml_crud.list_models(session)
    return [
        ModelInfo(
            id=r.id,
            model_type=r.model_type,
            version=r.version,
            is_active=r.is_active,
            metrics=r.metrics,
            trained_at=r.trained_at,
        )
        for r in records
    ]


async def evaluate_model(
    session: AsyncSession,
    model_type: str | None = None,
) -> EvaluateResponse:
    predictions = await ml_crud.get_predictions(session, model_type=model_type)
    evaluated = [p for p in predictions if p.hit_count is not None]

    if not evaluated:
        return EvaluateResponse(
            model_type=model_type,
            total_predictions=len(predictions),
            average_hits=0.0,
            hit_distribution={},
        )

    hits = [p.hit_count for p in evaluated]
    dist: dict[str, int] = {}
    for h in hits:
        key = str(h)
        dist[key] = dist.get(key, 0) + 1

    return EvaluateResponse(
        model_type=model_type,
        total_predictions=len(evaluated),
        average_hits=round(sum(hits) / len(hits), 2),
        hit_distribution=dist,
    )


async def get_dqn_prediction(
    session: AsyncSession,
    pick_count: int = 3,
) -> PickNPredictionResponse | None:
    from taiwan_bingo.ml.inference.model_registry import load_model
    from taiwan_bingo.ml.models.dqn_model import DQNBingoModel

    model_type = f"dqn_{pick_count}"
    model = await load_model(session, model_type)
    if model is None or not isinstance(model, DQNBingoModel):
        return None

    history = await get_all_numbers(session, limit=2000)
    if not history:
        return None

    recommended = await model.predict(history, pick_count=pick_count)
    q_all = model.get_q_values(history)
    q_vals = [round(float(q_all[n - 1]), 6) for n in recommended]

    from math import comb
    theoretical = comb(20, pick_count) / comb(80, pick_count)

    return PickNPredictionResponse(
        pick_count=pick_count,
        model_type=model_type,
        recommended_numbers=recommended,
        q_values=q_vals,
        full_hit_probability_estimate=round(theoretical, 8),
    )


async def backtest_model(
    session: AsyncSession,
    request: BacktestRequest,
) -> BacktestResponse:
    from taiwan_bingo.ml.training.trainer import train as do_train
    from taiwan_bingo.ml.models.base_model import BaseBingoModel

    history = await get_all_numbers(session, limit=5000)
    if len(history) < request.test_size + 50:
        return BacktestResponse(
            model_type=request.model_type,
            test_size=0,
            win_threshold=request.win_threshold,
            win_rate=0.0,
            avg_hits=0.0,
            results=[],
        )

    train_history = history[: -(request.test_size)]
    test_history = history[-(request.test_size):]

    from taiwan_bingo.ml.models.ensemble import EnsembleModel
    from taiwan_bingo.ml.models.frequency_model import FrequencyModel
    from taiwan_bingo.ml.models.lstm_model import LSTMModel

    MODEL_MAP = {"frequency": FrequencyModel, "lstm": LSTMModel, "ensemble": EnsembleModel}
    cls = MODEL_MAP.get(request.model_type, EnsembleModel)
    model = cls(pick_count=request.pick_count)
    await model.train(train_history)

    results = []
    wins = 0
    total_hits = 0

    for i, actual in enumerate(test_history):
        ctx = train_history + test_history[:i]
        predicted = await model.predict(ctx, pick_count=request.pick_count)
        hits = len(set(predicted) & set(actual))
        win = hits >= request.win_threshold
        if win:
            wins += 1
        total_hits += hits
        results.append(
            BacktestSummary(
                period=str(i + 1),
                predicted=predicted,
                actual=sorted(actual),
                hits=hits,
                win=win,
            )
        )

    n = len(results)
    return BacktestResponse(
        model_type=request.model_type,
        test_size=n,
        win_threshold=request.win_threshold,
        win_rate=round(wins / n, 4) if n else 0.0,
        avg_hits=round(total_hits / n, 2) if n else 0.0,
        results=results,
    )
