import numpy as np

from taiwan_bingo.ml.models.base_model import BaseBingoModel
from taiwan_bingo.ml.models.frequency_model import FrequencyModel
from taiwan_bingo.ml.models.lstm_model import LSTMModel

MAX_NUM = 80
PICK_COUNT = 20


class EnsembleModel(BaseBingoModel):
    """Weighted ensemble of FrequencyModel + LSTMModel."""

    model_type = "ensemble"

    def __init__(
        self,
        max_num: int = MAX_NUM,
        pick_count: int = PICK_COUNT,
        weights: list[float] | None = None,
    ):
        self.max_num = max_num
        self.pick_count = pick_count
        self._freq = FrequencyModel(max_num, pick_count)
        self._lstm = LSTMModel(max_num, pick_count)
        self._weights = weights or [0.4, 0.6]  # freq, lstm

    async def train(self, history: list[list[int]], **kwargs) -> dict:
        freq_metrics = await self._freq.train(history, **kwargs)
        lstm_metrics = await self._lstm.train(history, **kwargs)
        return {
            "frequency": freq_metrics,
            "lstm": lstm_metrics,
            "ensemble_weights": self._weights,
        }

    async def get_probabilities(self, history: list[list[int]]) -> np.ndarray:
        p_freq = await self._freq.get_probabilities(history)
        try:
            p_lstm = await self._lstm.get_probabilities(history)
        except RuntimeError:
            # lstm not trained — fall back to frequency only
            return p_freq

        combined = self._weights[0] * p_freq + self._weights[1] * p_lstm
        return combined / combined.sum()
