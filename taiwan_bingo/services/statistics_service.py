from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession

from taiwan_bingo.db.crud.bingo import get_all_numbers
from taiwan_bingo.schemas.statistics import (
    BiasReport,
    ColdNumber,
    GapAnalysis,
    HotColdAnalysis,
    HotNumber,
    NumberFrequency,
    NumberGap,
    PairFrequency,
    SectorAnalysis,
    SectorStats,
)

MAX_NUM = 80
PICK_COUNT = 20


async def get_number_frequency(
    session: AsyncSession, window: int = 100
) -> list[NumberFrequency]:
    history = await get_all_numbers(session, limit=window)
    flat = [n for draw in history for n in draw]
    counter = Counter(flat)
    total = len(flat)

    result = []
    for num in range(1, MAX_NUM + 1):
        cnt = counter.get(num, 0)
        result.append(
            NumberFrequency(
                number=num,
                count=cnt,
                percentage=round(cnt / total * 100, 2) if total else 0.0,
                rank=0,
            )
        )
    result.sort(key=lambda x: x.count, reverse=True)
    for i, item in enumerate(result):
        item.rank = i + 1
    return result


async def get_hot_cold_analysis(
    session: AsyncSession, window: int = 100, top_n: int = 10
) -> HotColdAnalysis:
    history = await get_all_numbers(session, limit=window)
    counter: Counter[int] = Counter()
    last_seen: dict[int, int] = {}  # number -> draws_ago

    for i, draw in enumerate(reversed(history)):
        for n in draw:
            counter[n] += 1
            if n not in last_seen:
                last_seen[n] = i

    hot = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:top_n]
    cold = sorted(
        [(n, counter.get(n, 0)) for n in range(1, MAX_NUM + 1)],
        key=lambda x: x[1],
    )[:top_n]

    return HotColdAnalysis(
        window=window,
        hot_numbers=[
            HotNumber(number=n, count=c, streak=0) for n, c in hot
        ],
        cold_numbers=[
            ColdNumber(
                number=n,
                count=c,
                last_seen_draws_ago=last_seen.get(n, len(history)),
            )
            for n, c in cold
        ],
    )


async def get_gap_analysis(
    session: AsyncSession, window: int = 100
) -> GapAnalysis:
    history = await get_all_numbers(session, limit=window)
    last_draw_idx: dict[int, int] = {}
    gaps_list: dict[int, list[int]] = defaultdict(list)

    for idx, draw in enumerate(history):
        for n in range(1, MAX_NUM + 1):
            if n in draw:
                if n in last_draw_idx:
                    gaps_list[n].append(idx - last_draw_idx[n])
                last_draw_idx[n] = idx

    current_idx = len(history) - 1
    result = []
    for n in range(1, MAX_NUM + 1):
        g = gaps_list[n]
        current_gap = current_idx - last_draw_idx.get(n, 0) if n in last_draw_idx else current_idx
        result.append(
            NumberGap(
                number=n,
                current_gap=current_gap,
                avg_gap=round(float(np.mean(g)), 2) if g else 0.0,
                max_gap=int(np.max(g)) if g else 0,
            )
        )

    return GapAnalysis(window=window, gaps=result)


async def get_sector_analysis(
    session: AsyncSession, window: int = 100
) -> SectorAnalysis:
    history = await get_all_numbers(session, limit=window)
    sector_draws = [[], [], [], []]  # 4 sectors

    for draw in history:
        counts = [0, 0, 0, 0]
        for n in draw:
            counts[(n - 1) // 20] += 1
        for i in range(4):
            sector_draws[i].append(counts[i])

    sectors = []
    for i in range(4):
        data = sector_draws[i]
        sectors.append(
            SectorStats(
                sector=i + 1,
                range_start=i * 20 + 1,
                range_end=(i + 1) * 20,
                avg_count=round(float(np.mean(data)), 2) if data else 0.0,
                std_count=round(float(np.std(data)), 2) if data else 0.0,
                distribution=data,
            )
        )

    return SectorAnalysis(window=window, sectors=sectors)


async def get_pair_frequency(
    session: AsyncSession, window: int = 200, top_n: int = 20
) -> list[PairFrequency]:
    history = await get_all_numbers(session, limit=window)
    counter: Counter[tuple[int, int]] = Counter()

    for draw in history:
        for pair in combinations(sorted(draw), 2):
            counter[pair] += 1

    total = len(history)
    top = counter.most_common(top_n)
    return [
        PairFrequency(
            number_a=pair[0],
            number_b=pair[1],
            count=cnt,
            percentage=round(cnt / total * 100, 2) if total else 0.0,
        )
        for pair, cnt in top
    ]


async def get_bias_report(
    session: AsyncSession, window: int = 200
) -> BiasReport:
    history = await get_all_numbers(session, limit=window)
    total_draws = len(history)
    flat = [n for draw in history for n in draw]
    counter = Counter(flat)

    expected = total_draws * PICK_COUNT / MAX_NUM
    observed = [counter.get(n, 0) for n in range(1, MAX_NUM + 1)]
    expected_arr = [expected] * MAX_NUM

    chi2, p_value = stats.chisquare(observed, f_exp=expected_arr)
    is_biased = bool(p_value < 0.05)

    biased = [
        n + 1
        for n, obs in enumerate(observed)
        if abs(obs - expected) > 2 * (expected**0.5)
    ]

    return BiasReport(
        window=window,
        chi_square=round(float(chi2), 4),
        p_value=round(float(p_value), 6),
        is_biased=is_biased,
        biased_numbers=biased,
        expected_frequency=round(expected, 2),
        actual_frequencies=observed,
    )
