from pydantic import BaseModel


class PickNCombination(BaseModel):
    numbers: list[int]
    count: int
    percentage: float


class PickNHitAnalysis(BaseModel):
    pick_count: int
    window: int
    theoretical_full_hit_rate: float
    hot_numbers_used: list[int]
    hit_distribution: dict[str, int]
    full_hit_count: int
    full_hit_rate: float


class PickNRecommendation(BaseModel):
    pick_count: int
    recommended_numbers: list[int]
    scores: list[float]
    rationale: str


class PickNExpectedValue(BaseModel):
    pick_count: int
    theoretical_rate: float
    observed_rate: float
    improvement_ratio: float


class NumberFrequency(BaseModel):
    number: int
    count: int
    percentage: float
    rank: int


class HotNumber(BaseModel):
    number: int
    count: int
    streak: int


class ColdNumber(BaseModel):
    number: int
    count: int
    last_seen_draws_ago: int


class HotColdAnalysis(BaseModel):
    window: int
    hot_numbers: list[HotNumber]
    cold_numbers: list[ColdNumber]


class NumberGap(BaseModel):
    number: int
    current_gap: int
    avg_gap: float
    max_gap: int


class GapAnalysis(BaseModel):
    window: int
    gaps: list[NumberGap]


class SectorStats(BaseModel):
    sector: int
    range_start: int
    range_end: int
    avg_count: float
    std_count: float
    distribution: list[int]   # count per draw


class SectorAnalysis(BaseModel):
    window: int
    sectors: list[SectorStats]


class PairFrequency(BaseModel):
    number_a: int
    number_b: int
    count: int
    percentage: float


class BiasReport(BaseModel):
    window: int
    chi_square: float
    p_value: float
    is_biased: bool
    biased_numbers: list[int]
    expected_frequency: float
    actual_frequencies: list[int]
