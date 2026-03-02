from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.crud.ml import get_active_model
from taiwan_bingo.ml.models.base_model import BaseBingoModel

_cache: dict[str, BaseBingoModel] = {}


async def load_model(session: AsyncSession, model_type: str) -> BaseBingoModel | None:
    if model_type in _cache:
        return _cache[model_type]

    record = await get_active_model(session, model_type)
    if record is None:
        return None

    path = Path(record.artifact_path)
    if not path.exists():
        return None

    model = BaseBingoModel.load(path)
    _cache[model_type] = model
    return model


def invalidate_cache(model_type: str) -> None:
    _cache.pop(model_type, None)
