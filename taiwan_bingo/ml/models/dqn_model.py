"""DQN (Deep Q-Network) model for Pick-N bingo prediction.

State: 80 numbers × 5 features = 400-dim vector
Q-net: FC 400→256→128→80 (Q-values per number)
Objective: maximize full-hit rate for pick-3/4/5
"""

from __future__ import annotations

import random
from collections import deque
from pathlib import Path
from typing import NamedTuple

import numpy as np

from taiwan_bingo.ml.models.base_model import BaseBingoModel

MAX_NUM = 80


class _Transition(NamedTuple):
    state: np.ndarray
    action: list[int]   # indices 0-79
    reward: float
    next_state: np.ndarray


class _QNet:
    """Simple NumPy-based Q-network (no external deep-learning dependency)."""

    def __init__(self, input_dim: int = 400, hidden1: int = 256, hidden2: int = 128, output_dim: int = 80):
        scale1 = np.sqrt(2.0 / input_dim)
        scale2 = np.sqrt(2.0 / hidden1)
        scale3 = np.sqrt(2.0 / hidden2)
        self.W1 = np.random.randn(input_dim, hidden1) * scale1
        self.b1 = np.zeros(hidden1)
        self.W2 = np.random.randn(hidden1, hidden2) * scale2
        self.b2 = np.zeros(hidden2)
        self.W3 = np.random.randn(hidden2, output_dim) * scale3
        self.b3 = np.zeros(output_dim)

    def forward(self, x: np.ndarray) -> np.ndarray:
        h1 = np.maximum(0.0, x @ self.W1 + self.b1)          # ReLU
        h2 = np.maximum(0.0, h1 @ self.W2 + self.b2)          # ReLU
        return h2 @ self.W3 + self.b3                          # linear

    def get_params(self) -> list[np.ndarray]:
        return [self.W1, self.b1, self.W2, self.b2, self.W3, self.b3]

    def set_params(self, params: list[np.ndarray]) -> None:
        self.W1, self.b1, self.W2, self.b2, self.W3, self.b3 = [p.copy() for p in params]

    def soft_update(self, other: "_QNet", tau: float = 0.01) -> None:
        for sp, op in zip(self.get_params(), other.get_params()):
            sp *= (1 - tau)
            sp += tau * op

    def update(self, x: np.ndarray, target_q: np.ndarray, lr: float = 1e-3) -> float:
        """Single-sample gradient descent. Returns MSE loss."""
        h1_pre = x @ self.W1 + self.b1
        h1 = np.maximum(0.0, h1_pre)
        h2_pre = h1 @ self.W2 + self.b2
        h2 = np.maximum(0.0, h2_pre)
        q_out = h2 @ self.W3 + self.b3

        delta = q_out - target_q
        loss = float(np.mean(delta ** 2))

        # Backprop
        dq = 2 * delta / MAX_NUM
        dW3 = np.outer(h2, dq)
        db3 = dq
        dh2 = dq @ self.W3.T
        dh2_pre = dh2 * (h2_pre > 0)
        dW2 = np.outer(h1, dh2_pre)
        db2 = dh2_pre
        dh1 = dh2_pre @ self.W2.T
        dh1_pre = dh1 * (h1_pre > 0)
        dW1 = np.outer(x, dh1_pre)
        db1 = dh1_pre

        # Gradient clipping
        for grad in [dW1, db1, dW2, db2, dW3, db3]:
            np.clip(grad, -1.0, 1.0, out=grad)

        self.W1 -= lr * dW1
        self.b1 -= lr * db1
        self.W2 -= lr * dW2
        self.b2 -= lr * db2
        self.W3 -= lr * dW3
        self.b3 -= lr * db3

        return loss


def _build_state(history: list[list[int]], window_short: int = 20, window_long: int = 100) -> np.ndarray:
    """Build 400-dim state vector from draw history."""
    recent = history[-window_short:] if len(history) >= window_short else history
    long = history[-window_long:] if len(history) >= window_long else history
    last5 = history[-5:] if len(history) >= 5 else history

    total_recent = len(recent)
    total_long = len(long)

    flat_recent = [n for draw in recent for n in draw]
    flat_long = [n for draw in long for n in draw]

    freq_recent = np.bincount(flat_recent, minlength=MAX_NUM + 1)[1:] / max(total_recent * 20, 1)
    freq_long = np.bincount(flat_long, minlength=MAX_NUM + 1)[1:] / max(total_long * 20, 1)

    last_seen = np.full(MAX_NUM, float(len(history)))
    for i, draw in enumerate(history):
        for n in draw:
            last_seen[n - 1] = i
    gap = (len(history) - last_seen) / max(len(history), 1)

    mean_f = freq_long.mean()
    std_f = freq_long.std() + 1e-8
    hot_cold = (freq_long - mean_f) / std_f

    last5_flat = set(n for draw in last5 for n in draw)
    recent5 = np.array([1.0 if (i + 1) in last5_flat else 0.0 for i in range(MAX_NUM)])

    return np.stack([freq_recent, freq_long, gap, hot_cold, recent5], axis=1).flatten()


class DQNBingoModel(BaseBingoModel):
    """Deep Q-Network model for Pick-N bingo prediction."""

    model_type: str = "dqn"

    def __init__(self, pick_count: int = 3, buffer_size: int = 10_000, gamma: float = 0.9):
        self.pick_count = pick_count
        self.model_type = f"dqn_{pick_count}"
        self._buffer: deque[_Transition] = deque(maxlen=buffer_size)
        self._online = _QNet()
        self._target = _QNet()
        self._target.set_params(self._online.get_params())
        self._gamma = gamma
        self._trained = False

    async def get_probabilities(self, history: list[list[int]]) -> np.ndarray:
        if not self._trained:
            return np.ones(MAX_NUM) / MAX_NUM
        state = _build_state(history)
        q_vals = self._online.forward(state)
        # Softmax to turn Q-values into probabilities
        q_shifted = q_vals - q_vals.max()
        exp_q = np.exp(q_shifted)
        return exp_q / exp_q.sum()

    async def train(self, history: list[list[int]], **kwargs) -> dict:
        epochs: int = kwargs.get("epochs", 50)
        lr: float = kwargs.get("lr", 1e-3)
        batch_size: int = kwargs.get("batch_size", 32)
        eps_start: float = 0.9
        eps_end: float = 0.05
        update_target_every: int = 100

        min_history = max(30, self.pick_count + 10)
        if len(history) < min_history:
            raise ValueError(f"Insufficient data: need ≥{min_history} draws, got {len(history)}")

        total_steps = 0
        total_loss = 0.0
        loss_count = 0

        for epoch in range(epochs):
            eps = eps_start - (eps_start - eps_end) * epoch / max(epochs - 1, 1)

            for t in range(len(history) - 1):
                state = _build_state(history[: t + 1])

                q_vals = self._online.forward(state)
                if random.random() < eps:
                    action = random.sample(range(MAX_NUM), self.pick_count)
                else:
                    action = list(np.argsort(q_vals)[::-1][: self.pick_count])

                actual = set(n - 1 for n in history[t + 1])
                hits = len(set(action) & actual)
                reward = hits / self.pick_count

                next_state = _build_state(history[: t + 2])
                self._buffer.append(_Transition(state, action, reward, next_state))
                total_steps += 1

                if len(self._buffer) >= batch_size:
                    batch = random.sample(self._buffer, batch_size)
                    for trans in batch:
                        q_cur = self._online.forward(trans.state)
                        q_next = self._target.forward(trans.next_state)
                        target_q = q_cur.copy()
                        best_next = float(np.max(q_next))
                        for idx in trans.action:
                            target_q[idx] = trans.reward + self._gamma * best_next
                        loss = self._online.update(trans.state, target_q, lr=lr)
                        total_loss += loss
                        loss_count += 1

                if total_steps % update_target_every == 0:
                    self._target.soft_update(self._online, tau=0.01)

        self._trained = True
        avg_loss = round(total_loss / max(loss_count, 1), 6)
        return {
            "model_type": self.model_type,
            "pick_count": self.pick_count,
            "epochs": epochs,
            "trained_on": len(history),
            "avg_loss": avg_loss,
        }

    async def predict(self, history: list[list[int]], pick_count: int | None = None) -> list[int]:
        n = pick_count or self.pick_count
        if not self._trained:
            from collections import Counter
            flat = [num for draw in history[-200:] for num in draw]
            cnt = Counter(flat)
            top = [num for num, _ in cnt.most_common(n)]
            return sorted(top)
        state = _build_state(history)
        q_vals = self._online.forward(state)
        indices = list(np.argsort(q_vals)[::-1][:n])
        return sorted(int(i + 1) for i in indices)

    def get_q_values(self, history: list[list[int]]) -> np.ndarray:
        state = _build_state(history)
        return self._online.forward(state)
