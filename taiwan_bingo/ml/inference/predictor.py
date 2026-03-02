import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.crud.bingo import get_all_numbers
from taiwan_bingo.db.crud.ml import log_prediction
from taiwan_bingo.ml.inference.model_registry import load_model
from taiwan_bingo.schemas.ml import ConfidenceDetail, PredictionResponse

MAX_NUM = 80
PICK_COUNT = 20


async def predict(
    session: AsyncSession,
    model_type: str = "ensemble",
    pick_count: int = PICK_COUNT,
) -> PredictionResponse | None:
    model = await load_model(session, model_type)
    if model is None:
        return None

    history = await get_all_numbers(session, limit=2000)
    if not history:
        return None

    probs = await model.get_probabilities(history)
    predicted = await model.predict(history, pick_count=pick_count)

    # Confidence details
    total_prob = probs[np.array(predicted) - 1].sum()
    expected_random = pick_count * pick_count / MAX_NUM

    details = []
    for num in predicted:
        p = float(probs[num - 1])
        percentile = float(np.sum(probs <= p) / MAX_NUM * 100)
        details.append(ConfidenceDetail(number=num, probability=round(p, 6), percentile=round(percentile, 1)))
    details.sort(key=lambda d: d.probability, reverse=True)

    # Log to DB
    await log_prediction(
        session,
        {
            "model_type": model_type,
            "predicted_numbers": predicted,
            "confidence_scores": [d.probability for d in details],
        },
    )

    return PredictionResponse(
        model_type=model_type,
        predicted_numbers=predicted,
        confidence_details=details,
        pick_count=pick_count,
        expected_random_hit=round(expected_random, 2),
    )
