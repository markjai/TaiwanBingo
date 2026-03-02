from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class BaseBingoModel(ABC):
    max_num: int = 80
    pick_count: int = 20
    model_type: str = "base"

    @abstractmethod
    async def train(self, history: list[list[int]], **kwargs) -> dict:
        """Train the model. Returns metrics dict."""

    @abstractmethod
    async def get_probabilities(self, history: list[list[int]]) -> np.ndarray:
        """Return probability array of shape (max_num,)."""

    async def predict(
        self, history: list[list[int]], pick_count: int | None = None
    ) -> list[int]:
        """Return sorted list of predicted numbers."""
        n = pick_count or self.pick_count
        probs = await self.get_probabilities(history)
        indices = np.argsort(probs)[::-1][:n]
        return sorted(int(i + 1) for i in indices)

    def save(self, path: Path) -> None:
        import pickle
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "BaseBingoModel":
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)
