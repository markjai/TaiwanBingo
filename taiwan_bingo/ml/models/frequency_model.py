from collections import Counter

import numpy as np

from taiwan_bingo.ml.models.base_model import BaseBingoModel

MAX_NUM = 80
PICK_COUNT = 20


class FrequencyModel(BaseBingoModel):
    """Simple weighted frequency model with recency bias."""

    model_type = "frequency"

    def __init__(self, max_num: int = MAX_NUM, pick_count: int = PICK_COUNT):
        self.max_num = max_num
        self.pick_count = pick_count
        self._weights: np.ndarray | None = None

    async def train(self, history: list[list[int]], **kwargs) -> dict:
        n = len(history)
        if n == 0:
            self._weights = np.ones(self.max_num, dtype=np.float32) / self.max_num
            return {"trained_on": 0}

        weights = np.zeros(self.max_num, dtype=np.float64)
        # Recency weighting: more recent draws count more
        for i, draw in enumerate(history):
            recency = (i + 1) / n   # 0..1, older=lower
            for num in draw:
                weights[num - 1] += recency

        weights = weights / weights.sum()
        self._weights = weights.astype(np.float32)
        return {"trained_on": n, "entropy": float(-np.sum(weights * np.log(weights + 1e-10)))}

    async def get_probabilities(self, history: list[list[int]]) -> np.ndarray:
        if self._weights is None:
            await self.train(history)
        return self._weights  # type: ignore[return-value]
