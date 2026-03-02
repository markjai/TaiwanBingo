from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from taiwan_bingo.db.base import Base


class BingoDraw(Base):
    """賓果賓果開獎記錄 (1-80 取 20 號)"""

    __tablename__ = "bingo_draws"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draw_term: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    draw_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # 20 drawn numbers (sorted)
    numbers: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)

    # Pre-computed features
    sum_total: Mapped[int] = mapped_column(Integer, nullable=False)
    odd_count: Mapped[int] = mapped_column(Integer, nullable=False)
    even_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Sector counts: 1-20, 21-40, 41-60, 61-80
    sector_1_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sector_2_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sector_3_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sector_4_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Span: max - min
    span: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<BingoDraw term={self.draw_term} sum={self.sum_total}>"
