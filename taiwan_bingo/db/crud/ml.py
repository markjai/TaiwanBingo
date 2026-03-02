from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.models.ml_record import MLModelRecord, MLPrediction


async def create_model_record(session: AsyncSession, data: dict) -> MLModelRecord:
    record = MLModelRecord(**data)
    session.add(record)
    await session.flush()
    return record


async def get_active_model(session: AsyncSession, model_type: str) -> MLModelRecord | None:
    result = await session.execute(
        select(MLModelRecord)
        .where(MLModelRecord.model_type == model_type, MLModelRecord.is_active == True)  # noqa: E712
        .order_by(MLModelRecord.trained_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_models(session: AsyncSession) -> list[MLModelRecord]:
    result = await session.execute(
        select(MLModelRecord).order_by(MLModelRecord.trained_at.desc())
    )
    return list(result.scalars().all())


async def deactivate_model_type(session: AsyncSession, model_type: str) -> None:
    await session.execute(
        update(MLModelRecord)
        .where(MLModelRecord.model_type == model_type)
        .values(is_active=False)
    )


async def log_prediction(session: AsyncSession, data: dict) -> MLPrediction:
    pred = MLPrediction(**data)
    session.add(pred)
    await session.flush()
    return pred


async def get_predictions(
    session: AsyncSession,
    model_type: str | None = None,
    limit: int = 100,
) -> list[MLPrediction]:
    query = select(MLPrediction).order_by(MLPrediction.created_at.desc()).limit(limit)
    if model_type:
        query = query.where(MLPrediction.model_type == model_type)
    result = await session.execute(query)
    return list(result.scalars().all())
