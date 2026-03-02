import numpy as np
import torch
import torch.nn as nn

from taiwan_bingo.ml.features.feature_engineer import BingoFeatureEngineer
from taiwan_bingo.ml.models.base_model import BaseBingoModel

MAX_NUM = 80
PICK_COUNT = 20
SEQ_LEN = 30


class _BingoLSTM(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, output_size: int):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, dropout=0.2 if num_layers > 1 else 0.0
        )
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return torch.sigmoid(self.fc(out[:, -1, :]))


class LSTMModel(BaseBingoModel):
    model_type = "lstm"

    def __init__(
        self,
        max_num: int = MAX_NUM,
        pick_count: int = PICK_COUNT,
        hidden_size: int = 128,
        num_layers: int = 2,
        seq_len: int = SEQ_LEN,
        epochs: int = 30,
        lr: float = 1e-3,
    ):
        self.max_num = max_num
        self.pick_count = pick_count
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.seq_len = seq_len
        self.epochs = epochs
        self.lr = lr
        self._net: _BingoLSTM | None = None
        self._fe = BingoFeatureEngineer(max_num, pick_count)

    def _build_net(self) -> _BingoLSTM:
        return _BingoLSTM(self.max_num, self.hidden_size, self.num_layers, self.max_num)

    async def train(self, history: list[list[int]], **kwargs) -> dict:
        if len(history) < self.seq_len + 1:
            return {"error": "insufficient data", "trained_on": len(history)}

        device = torch.device("cpu")
        net = self._build_net().to(device)
        optimizer = torch.optim.Adam(net.parameters(), lr=self.lr)
        criterion = nn.BCELoss()

        # Build (X, y) pairs
        xs, ys = [], []
        for i in range(self.seq_len, len(history)):
            seq = self._fe.build_sequence(history[:i], self.seq_len)  # (seq_len, max_num)
            target = np.zeros(self.max_num, dtype=np.float32)
            for n in history[i]:
                target[n - 1] = 1.0
            xs.append(seq)
            ys.append(target)

        X = torch.tensor(np.stack(xs), dtype=torch.float32)
        Y = torch.tensor(np.stack(ys), dtype=torch.float32)

        net.train()
        losses = []
        batch_size = 32
        for epoch in range(self.epochs):
            perm = torch.randperm(len(X))
            epoch_loss = 0.0
            for i in range(0, len(X), batch_size):
                idx = perm[i:i + batch_size]
                xb, yb = X[idx].to(device), Y[idx].to(device)
                optimizer.zero_grad()
                pred = net(xb)
                loss = criterion(pred, yb)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            losses.append(epoch_loss)

        self._net = net
        return {
            "trained_on": len(history),
            "epochs": self.epochs,
            "final_loss": round(float(losses[-1]), 6),
        }

    async def get_probabilities(self, history: list[list[int]]) -> np.ndarray:
        if self._net is None:
            raise RuntimeError("LSTM model not trained yet")
        seq = self._fe.build_sequence(history, self.seq_len)
        x = torch.tensor(seq[None], dtype=torch.float32)
        self._net.eval()
        with torch.no_grad():
            probs = self._net(x).squeeze(0).numpy()
        return probs
