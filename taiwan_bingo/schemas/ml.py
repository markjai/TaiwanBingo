from datetime import datetime

from pydantic import BaseModel


class TrainRequest(BaseModel):
    model_type: str = "ensemble"   # frequency / lstm / ensemble
    pick_count: int = 20


class TrainResponse(BaseModel):
    model_id: int
    model_type: str
    version: str
    metrics: dict
    message: str


class ConfidenceDetail(BaseModel):
    number: int
    probability: float
    percentile: float


class PredictionResponse(BaseModel):
    model_type: str
    predicted_numbers: list[int]
    confidence_details: list[ConfidenceDetail]
    pick_count: int
    expected_random_hit: float


class ModelInfo(BaseModel):
    id: int
    model_type: str
    version: str
    is_active: bool
    metrics: dict | None
    trained_at: datetime


class EvaluateResponse(BaseModel):
    model_type: str | None
    total_predictions: int
    average_hits: float
    hit_distribution: dict[str, int]


class BacktestRequest(BaseModel):
    model_type: str = "ensemble"
    test_size: int = 50
    pick_count: int = 20
    win_threshold: int = 8


class BacktestSummary(BaseModel):
    period: str
    predicted: list[int]
    actual: list[int]
    hits: int
    win: bool


class BacktestResponse(BaseModel):
    model_type: str
    test_size: int
    win_threshold: int
    win_rate: float
    avg_hits: float
    results: list[BacktestSummary]
