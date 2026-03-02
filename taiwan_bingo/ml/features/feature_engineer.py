"""
賓果賓果特徵工程
Max number: 80, Pick count: 20
"""

from collections import Counter, defaultdict

import numpy as np

MAX_NUM = 80
PICK_COUNT = 20
SECTOR_SIZE = 20
N_SECTORS = 4


class BingoFeatureEngineer:
    def __init__(self, max_num: int = MAX_NUM, pick_count: int = PICK_COUNT):
        self.max_num = max_num
        self.pick_count = pick_count

    # ── Frequency ────────────────────────────────────────────────────
    def compute_frequency(
        self, history: list[list[int]], windows: list[int] = (20, 50, 100)
    ) -> np.ndarray:
        """Shape: (max_num, len(windows))"""
        features = np.zeros((self.max_num, len(windows)), dtype=np.float32)
        for wi, w in enumerate(windows):
            subset = history[-w:]
            flat = [n for draw in subset for n in draw]
            counter = Counter(flat)
            total = max(len(flat), 1)
            for n in range(1, self.max_num + 1):
                features[n - 1, wi] = counter.get(n, 0) / total
        return features

    # ── Gap / 遺漏 ───────────────────────────────────────────────────
    def compute_gaps(self, history: list[list[int]]) -> np.ndarray:
        """Current gap for each number. Shape: (max_num,)"""
        last_seen = {}
        for i, draw in enumerate(history):
            for n in draw:
                last_seen[n] = i
        total = len(history)
        gaps = np.array(
            [total - last_seen.get(n, 0) for n in range(1, self.max_num + 1)],
            dtype=np.float32,
        )
        return gaps / max(total, 1)  # normalized

    # ── Hot / Cold ────────────────────────────────────────────────────
    def compute_hot_cold(
        self, history: list[list[int]], window: int = 50
    ) -> np.ndarray:
        """Z-score of frequency vs. long-term average. Shape: (max_num,)"""
        subset = history[-window:]
        counter = Counter(n for draw in subset for n in draw)
        expected = window * self.pick_count / self.max_num
        std = (expected * (1 - self.pick_count / self.max_num)) ** 0.5
        if std == 0:
            return np.zeros(self.max_num, dtype=np.float32)
        return np.array(
            [(counter.get(n, 0) - expected) / std for n in range(1, self.max_num + 1)],
            dtype=np.float32,
        )

    # ── Sector distribution ───────────────────────────────────────────
    def compute_sector_features(self, history: list[list[int]]) -> np.ndarray:
        """Average sector distribution. Shape: (N_SECTORS,)"""
        counts = np.zeros(N_SECTORS, dtype=np.float32)
        for draw in history:
            for n in draw:
                counts[(n - 1) // SECTOR_SIZE] += 1
        return counts / max(len(history), 1)

    # ── Odd/Even ratio ────────────────────────────────────────────────
    def compute_odd_even(self, history: list[list[int]]) -> np.ndarray:
        """Average odd ratio over history. Shape: (1,)"""
        ratios = [sum(1 for n in draw if n % 2) / len(draw) for draw in history if draw]
        return np.array([np.mean(ratios)], dtype=np.float32) if ratios else np.zeros(1)

    # ── Sum statistics ────────────────────────────────────────────────
    def compute_sum_stats(self, history: list[list[int]]) -> np.ndarray:
        """[mean_sum, std_sum] normalized. Shape: (2,)"""
        sums = [sum(draw) for draw in history]
        if not sums:
            return np.zeros(2, dtype=np.float32)
        mean_s = np.mean(sums)
        std_s = np.std(sums) or 1.0
        # Theoretical mean: pick_count * (max_num+1) / 2
        theo_mean = self.pick_count * (self.max_num + 1) / 2
        return np.array(
            [(mean_s - theo_mean) / theo_mean, std_s / theo_mean],
            dtype=np.float32,
        )

    # ── Pair co-occurrence ────────────────────────────────────────────
    def compute_pair_affinity(
        self, history: list[list[int]], window: int = 100
    ) -> dict[tuple[int, int], float]:
        """Lift-like co-occurrence score for pairs."""
        from itertools import combinations

        subset = history[-window:]
        pair_cnt: Counter[tuple[int, int]] = Counter()
        single_cnt: Counter[int] = Counter()
        for draw in subset:
            s = sorted(draw)
            single_cnt.update(s)
            for pair in combinations(s, 2):
                pair_cnt[pair] += 1
        total = len(subset)
        affinity = {}
        for (a, b), cnt in pair_cnt.items():
            p_a = single_cnt[a] / (total * self.pick_count)
            p_b = single_cnt[b] / (total * self.pick_count)
            expected = p_a * p_b * total
            affinity[(a, b)] = cnt / expected if expected > 0 else 1.0
        return affinity

    # ── Combined feature vector ────────────────────────────────────────
    def build_feature_vector(
        self, history: list[list[int]], windows: list[int] = (20, 50, 100)
    ) -> np.ndarray:
        """Build a per-number feature vector for scoring."""
        freq = self.compute_frequency(history, windows)        # (max_num, n_windows)
        gaps = self.compute_gaps(history)[:, None]             # (max_num, 1)
        hot = self.compute_hot_cold(history)[:, None]          # (max_num, 1)
        features = np.concatenate([freq, gaps, hot], axis=1)   # (max_num, n_windows+2)
        return features

    # ── Sequence features for LSTM ────────────────────────────────────
    def build_sequence(
        self, history: list[list[int]], seq_len: int = 30
    ) -> np.ndarray:
        """One-hot encode last seq_len draws. Shape: (seq_len, max_num)"""
        seq = history[-seq_len:]
        result = np.zeros((seq_len, self.max_num), dtype=np.float32)
        for i, draw in enumerate(seq[-seq_len:]):
            for n in draw:
                result[i, n - 1] = 1.0
        return result
