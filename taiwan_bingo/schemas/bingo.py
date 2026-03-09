from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BingoDrawSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    draw_term: str
    draw_datetime: datetime
    numbers: list[int]
    sum_total: int
    odd_count: int
    even_count: int
    sector_1_count: int
    sector_2_count: int
    sector_3_count: int
    sector_4_count: int
    span: int


class PaginatedResponse(BaseModel):
    items: list[BingoDrawSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class ScrapeRequest(BaseModel):
    year_from: int = 2024   # AD year 西元年
    year_to: int = 2026


class ScrapeStatusSchema(BaseModel):
    status: str
    records_found: int
    records_inserted: int
    error_message: str | None = None
