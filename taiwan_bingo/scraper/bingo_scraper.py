"""
賓果賓果爬蟲 — 使用台灣彩券官方 JSON API

API endpoint: https://api.taiwanlottery.com/TLCAPIWeB/Lottery/BingoResult
- 需要 Accept: application/json 與 Origin header
- 參數: openDate (YYYY-MM-DD), pageNum, pageSize
- 回傳: {content: {bingoQueryResult: [...], totalSize: N}}
- 每期 bigShowOrder: 20 個已排序號碼 (字串)
- drawTerm: 期別 (整數)
"""

import ssl
from datetime import date, datetime, timedelta

import aiohttp
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.crud.bingo import bulk_upsert
from taiwan_bingo.scraper.base import BaseScraper

BINGO_API_URL = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/BingoResult"
PAGE_SIZE = 100  # max per request

# 賓果賓果每日首期 09:00，每 5 分鐘一期
FIRST_DRAW_HOUR = 9
FIRST_DRAW_MIN = 0
INTERVAL_MIN = 5


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


def _parse_item(item: dict, draw_date: date, first_term: int) -> dict | None:
    try:
        draw_term_raw = item.get("drawTerm", "")
        draw_term = str(draw_term_raw)
        if not draw_term:
            return None

        big_show = item.get("bigShowOrder", [])
        numbers = [int(n) for n in big_show if str(n).strip().isdigit()]
        if len(numbers) < 20:
            return None
        numbers = numbers[:20]

        # 計算開獎時間（從首期起算）
        draw_index = int(draw_term_raw) - first_term
        base_time = datetime(
            draw_date.year, draw_date.month, draw_date.day,
            FIRST_DRAW_HOUR, FIRST_DRAW_MIN,
        )
        draw_datetime = base_time + timedelta(minutes=draw_index * INTERVAL_MIN)

        return {
            "draw_term": draw_term,
            "draw_datetime": draw_datetime,
            **_compute_features(numbers),
        }
    except Exception as e:
        logger.debug("Failed to parse bingo item: {}", e)
        return None


def _make_connector_and_headers():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    conn = aiohttp.TCPConnector(ssl=ssl_ctx)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.taiwanlottery.com/",
        "Origin": "https://www.taiwanlottery.com",
    }
    return conn, headers


class BingoScraper(BaseScraper):
    async def _fetch_day(self, target_date: date) -> list[dict]:
        """Fetch all bingo draws for a specific date (handles pagination)."""
        conn, headers = _make_connector_and_headers()
        raw_items: list[dict] = []

        async with aiohttp.ClientSession(connector=conn) as client:
            page = 1
            while True:
                params = {
                    "openDate": target_date.strftime("%Y-%m-%d"),
                    "pageNum": page,
                    "pageSize": PAGE_SIZE,
                }
                try:
                    async with client.get(
                        BINGO_API_URL,
                        params=params,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status != 200:
                            logger.warning("Bingo API {} for {}", resp.status, target_date)
                            break
                        data = await resp.json()
                        content = data.get("content", {})
                        results = content.get("bingoQueryResult", [])
                        total_size = content.get("totalSize") or 0
                        raw_items.extend(results)
                        if len(results) < PAGE_SIZE or len(raw_items) >= total_size:
                            break
                        page += 1
                except Exception as e:
                    logger.warning("Bingo fetch error for {}: {}", target_date, e)
                    break

        if not raw_items:
            return []

        first_term = min(int(item.get("drawTerm", 0)) for item in raw_items)
        return [p for item in raw_items if (p := _parse_item(item, target_date, first_term))]

    async def fetch_latest(self, session: AsyncSession) -> int:
        today = date.today()
        draws = await self._fetch_day(today)
        if not draws:
            draws = await self._fetch_day(today - timedelta(days=1))
        if not draws:
            return 0
        return await bulk_upsert(session, draws)

    async def fetch_by_month(self, session: AsyncSession, year: int, month: int) -> int:
        """year: AD 西元年"""
        today = date.today()
        start = date(year, month, 1)
        end = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year + 1, 1, 1) - timedelta(days=1)
        if end > today:
            end = today

        total = 0
        current = start
        while current <= end:
            draws = await self._fetch_day(current)
            if draws:
                inserted = await bulk_upsert(session, draws)
                total += inserted
                logger.info("[bingo] {} -> {} inserted", current, inserted)
            current += timedelta(days=1)
        return total
