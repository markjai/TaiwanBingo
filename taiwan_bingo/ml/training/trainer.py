from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.config import settings
from taiwan_bingo.db.crud.bingo import get_all_numbers
from taiwan_bingo.db.crud.ml import create_model_record, deactivate_model_type
from taiwan_bingo.db.models.ml_record import MLModelRecord
from taiwan_bingo.ml.models.ensemble import EnsembleModel
from taiwan_bingo.ml.models.frequency_model import FrequencyModel
from taiwan_bingo.ml.models.lstm_model import LSTMModel

MODEL_MAP = {
    "frequency": FrequencyModel,
    "lstm": LSTMModel,
    "ensemble": EnsembleModel,
}


async def train(
    session: AsyncSession,
    model_type: str = "ensemble",
    pick_count: int = 20,
) -> tuple["BaseBingoModel", dict, int]:  # type: ignore[name-defined]
    history = await get_all_numbers(session, limit=5000)
    if len(history) < 50:
        raise ValueError(f"Insufficient data: only {len(history)} draws available")

    logger.info(f"Training {model_type} on {len(history)} draws")

    cls = MODEL_MAP.get(model_type)
    if cls is None:
        raise ValueError(f"Unknown model_type: {model_type!r}. Choose from {list(MODEL_MAP)}")

    model = cls(pick_count=pick_count)
    metrics = await model.train(history)

    # Save artifact
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifact_dir = settings.MODEL_ARTIFACTS_DIR / model_type
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{version}.pkl"
    model.save(artifact_path)
    logger.info(f"Model saved: {artifact_path}")

    # Deactivate old records & create new
    await deactivate_model_type(session, model_type)
    record = await create_model_record(
        session,
        {
            "model_type": model_type,
            "version": version,
            "artifact_path": str(artifact_path),
            "metrics": metrics,
            "is_active": True,
        },
    )
    logger.info(f"Model record created: id={record.id}")
    return model, metrics, record.id
