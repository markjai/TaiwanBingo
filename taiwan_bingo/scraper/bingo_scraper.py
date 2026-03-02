"""
賓果賓果爬蟲 — 從台灣彩券官網抓取開獎資料

官方 API:
  https://www.taiwanlottery.com/bingo/bingoBingo/history.aspx
  (POST form or JSON endpoint depending on the page version)

此實作使用 aiohttp + BeautifulSoup 解析 HTML 表格。
"""

from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.crud.bingo import bulk_upsert
from taiwan_bingo.scraper.base import BaseScraper

_BASE_URL = (
    "https://www.taiwanlottery.com/bingo/bingoBingo/history.aspx"
)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9",
}


def _compute_features(numbers: list[int]) -> dict:
    sorted_nums = sorted(numbers)
    odd = sum(1 for n in sorted_nums if n % 2 == 1)
    sectors = [0, 0, 0, 0]
    for n in sorted_nums:
        sectors[(n - 1) // 20] += 1
    return {
        "numbers": sorted_nums,
        "sum_total": sum(sorted_nums),
        "odd_count": odd,
        "even_count": len(sorted_nums) - odd,
        "sector_1_count": sectors[0],
        "sector_2_count": sectors[1],
        "sector_3_count": sectors[2],
        "sector_4_count": sectors[3],
        "span": sorted_nums[-1] - sorted_nums[0],
    }


def _parse_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("table.table-bingo tr, table#tbl_history tr")
    draws: list[dict] = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 22:
            continue

        try:
            term = cells[0].get_text(strip=True)
            dt_str = cells[1].get_text(strip=True)  # e.g. "2024/03/01 08:00"
            draw_dt = datetime.strptime(dt_str, "%Y/%m/%d %H:%M")
            numbers = [int(cells[i].get_text(strip=True)) for i in range(2, 22)]
        except (ValueError, IndexError):
            continue

        if not term or len(numbers) != 20:
            continue

        draw = {
            "draw_term": term,
            "draw_datetime": draw_dt,
            **_compute_features(numbers),
        }
        draws.append(draw)

    return draws


class BingoScraper(BaseScraper):
    async def _get_html(self, year: int, month: int) -> str:
        params = {"year": year, "month": f"{month:02d}"}
        async with aiohttp.ClientSession(headers=_HEADERS) as sess:
            async with sess.get(
                _BASE_URL,
                params=params,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                return await resp.text(encoding="utf-8", errors="replace")

    async def fetch_latest(self, session: AsyncSession) -> int:
        now = datetime.now()
        return await self.fetch_by_month(session, now.year, now.month)

    async def fetch_by_month(self, session: AsyncSession, year: int, month: int) -> int:
        logger.info(f"BingoScraper: fetching {year}/{month:02d}")
        html = await self._get_html(year, month)
        draws = _parse_html(html)
        logger.info(f"BingoScraper: parsed {len(draws)} draws")
        inserted = await bulk_upsert(session, draws)
        logger.info(f"BingoScraper: inserted {inserted} draws")
        return inserted
