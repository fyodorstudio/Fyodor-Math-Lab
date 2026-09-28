"""Reusable Trade Outcome Simulation and Metrics Engine for Macro Research.

Implements strict OHLC barrier proxy evaluation per CALCULATION_AND_CANDIDATE_CONTRACT:
- 52-cell ATR grid (4 stop widths x 13 target widths)
- Three expiry horizons (H60, H120, H240)
- Dual-touch ambiguity resolution (STOP-FIRST primary, TARGET-FIRST sensitivity)
- Opening gap tracking (nominal threshold-touch proxy vs gap open price)
- Timeout at horizon close (Hmax)
- Excursion bounds (guaranteed pre-exit lower bound, OHLC upper bound, full-horizon counterfactual)
- Nearest-rank quantiles and even-N median
- Leave-one-year-out diagnostics and adjacent-cell stability
- Zero lookahead, zero synthetic returns, zero spread/slippage deductions (gross research).
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict

from models import CandleBar


GRID_STOP_WIDTHS: List[float] = [1.0, 2.0, 3.0, 4.0]
GRID_TARGET_WIDTHS: List[float] = [
    1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 3.75, 4.00
]
EXPLORATION_HORIZONS: List[int] = [60, 120, 240]


def get_pip_size(pair: str) -> float:
    """Returns pip size: 0.01 for JPY quote pairs, 0.0001 for all others."""
    if pair.endswith("JPY"):
        return 0.01
    return 0.0001


@dataclass(frozen=True)
class GridCell:
    """Defines a stop and target width in absolute ATR multiples."""
    stop_atr: float
    target_atr: float

    @property
    def label(self) -> str:
        s_str = f"{self.stop_atr:g}"
        t_str = f"{self.target_atr:g}"
        return f"{s_str}:{t_str}"

    @property
    def reward_risk_ratio(self) -> float:
        return self.target_atr / self.stop_atr


def generate_grid_cells() -> List[GridCell]:
    """Generates all 52 exploratory grid cells (4 stops x 13 targets)."""
    cells = []
    for s in GRID_STOP_WIDTHS:
        for t in GRID_TARGET_WIDTHS:
            cells.append(GridCell(stop_atr=s, target_atr=t))
    assert len(cells) == 52, f"Grid cell count mismatch: {len(cells)} != 52"
    return cells


ALL_GRID_CELLS: List[GridCell] = generate_grid_cells()


def get_adjacent_grid_cells(cell: GridCell) -> List[GridCell]:
    """Returns orthogonal adjacent cells in the 52-cell ATR grid.

    Grid structure:
    - Stop ATR: [1.0, 2.0, 3.0, 4.0] (step 1.0)
    - Target ATR: [1.00, 1.25, 1.50, 1.75, 2.00, 2.25, 2.50, 2.75, 3.00, 3.25, 3.50, 3.75, 4.00] (step 0.25)

    Adjacent cells are immediate neighbors along the stop axis (+/-1.0 ATR)
    and target axis (+/-0.25 ATR) within grid boundaries.
    Corner cells have 2 neighbors, edge cells have 3, interior cells have 4.
    """
    s = cell.stop_atr
    t = cell.target_atr
    neighbors = []

    # Stop axis neighbors (same target, stop +/- 1.0)
    s_idx = GRID_STOP_WIDTHS.index(s) if s in GRID_STOP_WIDTHS else -1
    if s_idx > 0:
        neighbors.append(GridCell(stop_atr=GRID_STOP_WIDTHS[s_idx - 1], target_atr=t))
    if s_idx >= 0 and s_idx < len(GRID_STOP_WIDTHS) - 1:
        neighbors.append(GridCell(stop_atr=GRID_STOP_WIDTHS[s_idx + 1], target_atr=t))

    # Target axis neighbors (same stop, target +/- 0.25)
    t_idx = -1
    for idx, tw in enumerate(GRID_TARGET_WIDTHS):
        if math.isclose(tw, t, abs_tol=1e-5):
            t_idx = idx
            break
    if t_idx > 0:
        neighbors.append(GridCell(stop_atr=s, target_atr=GRID_TARGET_WIDTHS[t_idx - 1]))
    if t_idx >= 0 and t_idx < len(GRID_TARGET_WIDTHS) - 1:
        neighbors.append(GridCell(stop_atr=s, target_atr=GRID_TARGET_WIDTHS[t_idx + 1]))

    return neighbors


def calculate_adjacent_cell_stability(
    target_cell_label: str,
    cell_mean_r_map: Dict[str, float]
) -> Dict[str, Any]:
    """Calculates adjacent-cell stability metrics for a cell within a given panel/cohort/horizon.

    Args:
        target_cell_label: Label of the cell, e.g. "1:2" or "2:2.5".
        cell_mean_r_map: Mapping from cell_label -> gross_mean_r for cells in that evaluation cohort.

    Returns:
        Dict with:
        - adj_cells_count: count of adjacent cells evaluated (2, 3, or 4)
        - adj_mean_gross_r: average gross_mean_r of adjacent cells
        - adj_delta_mean_r: cell's gross_mean_r - adj_mean_gross_r
        - adj_min_mean_r: minimum gross_mean_r among adjacent cells
        - adj_max_mean_r: maximum gross_mean_r among adjacent cells
        - adj_all_positive: True if all adjacent cells have gross_mean_r > 0
    """
    target_cell = next((c for c in ALL_GRID_CELLS if c.label == target_cell_label), None)
    if target_cell is None:
        raise ValueError(f"Unknown grid cell label: '{target_cell_label}'")

    neighbors = get_adjacent_grid_cells(target_cell)
    adj_r_values = []
    for n in neighbors:
        if n.label in cell_mean_r_map:
            adj_r_values.append(cell_mean_r_map[n.label])

    if not adj_r_values:
        return {
            "adj_cells_count": 0,
            "adj_mean_gross_r": None,
            "adj_delta_mean_r": None,
            "adj_min_mean_r": None,
            "adj_max_mean_r": None,
            "adj_all_positive": False,
        }

    adj_mean = sum(adj_r_values) / len(adj_r_values)
    cell_r = cell_mean_r_map.get(target_cell_label, 0.0)
    delta = cell_r - adj_mean

    return {
        "adj_cells_count": len(adj_r_values),
        "adj_mean_gross_r": adj_mean,
        "adj_delta_mean_r": delta,
        "adj_min_mean_r": min(adj_r_values),
        "adj_max_mean_r": max(adj_r_values),
        "adj_all_positive": all(r > 0.0 for r in adj_r_values),
    }


@dataclass
class TradeOutcome:
    """Complete, auditable execution record for a single (trade, horizon, grid cell) trial."""
    # Identification
    horizon_bars: int
    stop_atr: float
    target_atr: float
    cell_label: str
    reward_risk_ratio: float
    dual_touch_mode: str  # "STOP_FIRST" or "TARGET_FIRST"

    # Outcome Status
    exit_reason: str  # "TARGET", "STOP", "TARGET_GAP", "STOP_GAP", "TIMEOUT"
    is_win: bool
    is_loss: bool
    is_timeout: bool
    dual_touch: bool
    is_opening_gap: bool

    # Arithmetic Execution
    exit_price: float
    exit_bar_idx: int  # 1-indexed (Bar 1 is entry candle)
    exit_time_server_text: str
    bars_to_exit: int
    clock_seconds_to_exit_bar_open: int = 0  # Elapsed seconds: exit_bar.timestamp - entry_bar.timestamp
    clock_seconds_to_exit_bar_close: int = 0  # Elapsed seconds: (exit_bar.timestamp + 3600) - entry_bar.timestamp
    clock_seconds_bar_close_proxy: int = 0  # Bar-close proxy (exact for TIMEOUT, open for GAP, close proxy for intrabar touch)
    gross_r: float = 0.0
    signed_pips: float = 0.0

    # Opening Gap Sensitivity
    gap_open_price: Optional[float] = None
    gap_executable_gross_r: Optional[float] = None
    gap_executable_pips: Optional[float] = None

    # Excursions Through Exit (Guaranteed Lower Bound & OHLC Upper Bound)
    mfe_pips_lower: float = 0.0
    mfe_pips_upper: float = 0.0
    mae_pips_lower: float = 0.0
    mae_pips_upper: float = 0.0
    mfe_atr_lower: float = 0.0
    mfe_atr_upper: float = 0.0
    mae_atr_lower: float = 0.0
    mae_atr_upper: float = 0.0

    # Full Observed Horizon Counterfactual Excursions
    full_mfe_pips: float = 0.0
    full_mae_pips: float = 0.0
    full_mfe_atr: float = 0.0
    full_mae_atr: float = 0.0


def simulate_single_trade(
    entry_price: float,
    direction: int,  # +1 for Long, -1 for Short
    atr: float,
    stop_atr: float,
    target_atr: float,
    path_bars: List[CandleBar],  # Exactly horizon_bars observed bars, path_bars[0] is entry candle (Bar 1)
    pip_size: float,
    dual_touch_mode: str = "STOP_FIRST",
) -> TradeOutcome:
    """Evaluates OHLC threshold-touch proxy for a single trade trial.

    Args:
        entry_price: Open price of entry candle (Bar 1).
        direction: +1 (Long) or -1 (Short).
        atr: Pre-release H1 Wilder ATR(14).
        stop_atr: Stop width in ATR multiples.
        target_atr: Target width in ATR multiples.
        path_bars: Complete list of bars for this horizon (len == horizon_bars).
        pip_size: 0.01 for JPY quote, 0.0001 otherwise.
        dual_touch_mode: "STOP_FIRST" (primary) or "TARGET_FIRST" (sensitivity).
    """
    horizon = len(path_bars)
    stop_dist = stop_atr * atr
    target_dist = target_atr * atr
    cell_label = f"{stop_atr:g}:{target_atr:g}"
    rr_ratio = target_atr / stop_atr

    if direction == 1:  # LONG
        stop_price = entry_price - stop_dist
        target_price = entry_price + target_dist
    elif direction == -1:  # SHORT
        stop_price = entry_price + stop_dist
        target_price = entry_price - target_dist
    else:
        raise ValueError(f"Invalid direction {direction}; must be +1 (Long) or -1 (Short)")

    # Full-horizon counterfactual excursions (across all bars in horizon)
    if direction == 1:
        full_max_high = max(b.high for b in path_bars)
        full_min_low = min(b.low for b in path_bars)
        full_mfe_price = max(0.0, full_max_high - entry_price)
        full_mae_price = max(0.0, entry_price - full_min_low)
    else:
        full_max_high = max(b.high for b in path_bars)
        full_min_low = min(b.low for b in path_bars)
        full_mfe_price = max(0.0, entry_price - full_min_low)
        full_mae_price = max(0.0, full_max_high - entry_price)

    full_mfe_pips = full_mfe_price / pip_size
    full_mae_pips = full_mae_price / pip_size
    full_mfe_atr = full_mfe_price / atr if atr > 0 else 0.0
    full_mae_atr = full_mae_price / atr if atr > 0 else 0.0

    entry_timestamp = path_bars[0].timestamp

    # Scan bars from 1 to horizon
    prior_mfe_price = 0.0
    prior_mae_price = 0.0
    dual_touch = False

    for idx, bar in enumerate(path_bars):
        bar_num = idx + 1  # 1-indexed
        bar_open_sec = bar.timestamp - entry_timestamp
        bar_close_sec = (bar.timestamp + 3600) - entry_timestamp

        # 1. Opening Gap Check
        is_stop_gap = False
        is_target_gap = False
        if direction == 1:  # Long
            if bar.open <= stop_price:
                is_stop_gap = True
            elif bar.open >= target_price:
                is_target_gap = True
        else:  # Short
            if bar.open >= stop_price:
                is_stop_gap = True
            elif bar.open <= target_price:
                is_target_gap = True

        if is_stop_gap:
            # Primary threshold-touch proxy credits nominal Stop
            # Executable gap records actual open
            gap_open = bar.open
            gap_pips = direction * (gap_open - entry_price) / pip_size
            gap_gross_r = direction * (gap_open - entry_price) / stop_dist

            # Excursions up to bar open
            mfe_low = prior_mfe_price
            mfe_upp = prior_mfe_price
            mae_low = max(prior_mae_price, abs(entry_price - gap_open))
            mae_upp = max(prior_mae_price, abs(entry_price - gap_open))

            return TradeOutcome(
                horizon_bars=horizon,
                stop_atr=stop_atr,
                target_atr=target_atr,
                cell_label=cell_label,
                reward_risk_ratio=rr_ratio,
                dual_touch_mode=dual_touch_mode,
                exit_reason="STOP_GAP",
                is_win=False,
                is_loss=True,
                is_timeout=False,
                dual_touch=False,
                is_opening_gap=True,
                exit_price=stop_price,  # Primary nominal proxy
                exit_bar_idx=bar_num,
                exit_time_server_text=bar.time_server_text,
                bars_to_exit=bar_num,
                clock_seconds_to_exit_bar_open=bar_open_sec,
                clock_seconds_to_exit_bar_close=bar_close_sec,
                clock_seconds_bar_close_proxy=bar_open_sec,  # Opening gap triggers at bar open
                gross_r=-1.0,  # Nominal stop is -1R
                signed_pips=-stop_dist / pip_size,
                gap_open_price=gap_open,
                gap_executable_gross_r=gap_gross_r,
                gap_executable_pips=gap_pips,
                mfe_pips_lower=mfe_low / pip_size,
                mfe_pips_upper=mfe_upp / pip_size,
                mae_pips_lower=mae_low / pip_size,
                mae_pips_upper=mae_upp / pip_size,
                mfe_atr_lower=mfe_low / atr,
                mfe_atr_upper=mfe_upp / atr,
                mae_atr_lower=mae_low / atr,
                mae_atr_upper=mae_upp / atr,
                full_mfe_pips=full_mfe_pips,
                full_mae_pips=full_mae_pips,
                full_mfe_atr=full_mfe_atr,
                full_mae_atr=full_mae_atr,
            )

        if is_target_gap:
            gap_open = bar.open
            gap_pips = direction * (gap_open - entry_price) / pip_size
            gap_gross_r = direction * (gap_open - entry_price) / stop_dist

            mfe_low = max(prior_mfe_price, abs(gap_open - entry_price))
            mfe_upp = max(prior_mfe_price, abs(gap_open - entry_price))
            mae_low = prior_mae_price
            mae_upp = prior_mae_price

            return TradeOutcome(
                horizon_bars=horizon,
                stop_atr=stop_atr,
                target_atr=target_atr,
                cell_label=cell_label,
                reward_risk_ratio=rr_ratio,
                dual_touch_mode=dual_touch_mode,
                exit_reason="TARGET_GAP",
                is_win=True,
                is_loss=False,
                is_timeout=False,
                dual_touch=False,
                is_opening_gap=True,
                exit_price=target_price,  # Primary nominal proxy
                exit_bar_idx=bar_num,
                exit_time_server_text=bar.time_server_text,
                bars_to_exit=bar_num,
                clock_seconds_to_exit_bar_open=bar_open_sec,
                clock_seconds_to_exit_bar_close=bar_close_sec,
                clock_seconds_bar_close_proxy=bar_open_sec,  # Opening gap triggers at bar open
                gross_r=rr_ratio,  # Nominal target is +T/B R
                signed_pips=target_dist / pip_size,
                gap_open_price=gap_open,
                gap_executable_gross_r=gap_gross_r,
                gap_executable_pips=gap_pips,
                mfe_pips_lower=mfe_low / pip_size,
                mfe_pips_upper=mfe_upp / pip_size,
                mae_pips_lower=mae_low / pip_size,
                mae_pips_upper=mae_upp / pip_size,
                mfe_atr_lower=mfe_low / atr,
                mfe_atr_upper=mfe_upp / atr,
                mae_atr_lower=mae_low / atr,
                mae_atr_upper=mae_upp / atr,
                full_mfe_pips=full_mfe_pips,
                full_mae_pips=full_mae_pips,
                full_mfe_atr=full_mfe_atr,
                full_mae_atr=full_mae_atr,
            )

        # 2. Intrabar Touch Checks
        stop_touched = False
        target_touched = False

        if direction == 1:  # Long
            if bar.low <= stop_price:
                stop_touched = True
            if bar.high >= target_price:
                target_touched = True
            bar_mfe = max(0.0, bar.high - entry_price)
            bar_mae = max(0.0, entry_price - bar.low)
        else:  # Short
            if bar.high >= stop_price:
                stop_touched = True
            if bar.low <= target_price:
                target_touched = True
            bar_mfe = max(0.0, entry_price - bar.low)
            bar_mae = max(0.0, bar.high - entry_price)

        # 3. Resolve Touches
        if stop_touched and target_touched:
            dual_touch = True
            if dual_touch_mode == "STOP_FIRST":
                # Primary Conservative: STOP
                mfe_low = prior_mfe_price
                mfe_upp = max(prior_mfe_price, bar_mfe)
                mae_low = max(prior_mae_price, stop_dist)
                mae_upp = max(prior_mae_price, bar_mae)

                return TradeOutcome(
                    horizon_bars=horizon,
                    stop_atr=stop_atr,
                    target_atr=target_atr,
                    cell_label=cell_label,
                    reward_risk_ratio=rr_ratio,
                    dual_touch_mode=dual_touch_mode,
                    exit_reason="STOP",
                    is_win=False,
                    is_loss=True,
                    is_timeout=False,
                    dual_touch=True,
                    is_opening_gap=False,
                    exit_price=stop_price,
                    exit_bar_idx=bar_num,
                    exit_time_server_text=bar.time_server_text,
                    bars_to_exit=bar_num,
                    clock_seconds_to_exit_bar_open=bar_open_sec,
                    clock_seconds_to_exit_bar_close=bar_close_sec,
                    clock_seconds_bar_close_proxy=bar_close_sec,  # Upper-bound / bar-close proxy
                    gross_r=-1.0,
                    signed_pips=-stop_dist / pip_size,
                    mfe_pips_lower=mfe_low / pip_size,
                    mfe_pips_upper=mfe_upp / pip_size,
                    mae_pips_lower=mae_low / pip_size,
                    mae_pips_upper=mae_upp / pip_size,
                    mfe_atr_lower=mfe_low / atr,
                    mfe_atr_upper=mfe_upp / atr,
                    mae_atr_lower=mae_low / atr,
                    mae_atr_upper=mae_upp / atr,
                    full_mfe_pips=full_mfe_pips,
                    full_mae_pips=full_mae_pips,
                    full_mfe_atr=full_mfe_atr,
                    full_mae_atr=full_mae_atr,
                )
            else:
                # Sensitivity Optimistic: TARGET
                mfe_low = max(prior_mfe_price, target_dist)
                mfe_upp = max(prior_mfe_price, bar_mfe)
                mae_low = prior_mae_price
                mae_upp = max(prior_mae_price, bar_mae)

                return TradeOutcome(
                    horizon_bars=horizon,
                    stop_atr=stop_atr,
                    target_atr=target_atr,
                    cell_label=cell_label,
                    reward_risk_ratio=rr_ratio,
                    dual_touch_mode=dual_touch_mode,
                    exit_reason="TARGET",
                    is_win=True,
                    is_loss=False,
                    is_timeout=False,
                    dual_touch=True,
                    is_opening_gap=False,
                    exit_price=target_price,
                    exit_bar_idx=bar_num,
                    exit_time_server_text=bar.time_server_text,
                    bars_to_exit=bar_num,
                    clock_seconds_to_exit_bar_open=bar_open_sec,
                    clock_seconds_to_exit_bar_close=bar_close_sec,
                    clock_seconds_bar_close_proxy=bar_close_sec,  # Upper-bound / bar-close proxy
                    gross_r=rr_ratio,
                    signed_pips=target_dist / pip_size,
                    mfe_pips_lower=mfe_low / pip_size,
                    mfe_pips_upper=mfe_upp / pip_size,
                    mae_pips_lower=mae_low / pip_size,
                    mae_pips_upper=mae_upp / pip_size,
                    mfe_atr_lower=mfe_low / atr,
                    mfe_atr_upper=mfe_upp / atr,
                    mae_atr_lower=mae_low / atr,
                    mae_atr_upper=mae_upp / atr,
                    full_mfe_pips=full_mfe_pips,
                    full_mae_pips=full_mae_pips,
                    full_mfe_atr=full_mfe_atr,
                    full_mae_atr=full_mae_atr,
                )

        if stop_touched:
            mfe_low = prior_mfe_price
            mfe_upp = max(prior_mfe_price, bar_mfe)
            mae_low = max(prior_mae_price, stop_dist)
            mae_upp = max(prior_mae_price, bar_mae)

            return TradeOutcome(
                horizon_bars=horizon,
                stop_atr=stop_atr,
                target_atr=target_atr,
                cell_label=cell_label,
                reward_risk_ratio=rr_ratio,
                dual_touch_mode=dual_touch_mode,
                exit_reason="STOP",
                is_win=False,
                is_loss=True,
                is_timeout=False,
                dual_touch=False,
                is_opening_gap=False,
                exit_price=stop_price,
                exit_bar_idx=bar_num,
                exit_time_server_text=bar.time_server_text,
                bars_to_exit=bar_num,
                clock_seconds_to_exit_bar_open=bar_open_sec,
                clock_seconds_to_exit_bar_close=bar_close_sec,
                clock_seconds_bar_close_proxy=bar_close_sec,  # Upper-bound / bar-close proxy
                gross_r=-1.0,
                signed_pips=-stop_dist / pip_size,
                mfe_pips_lower=mfe_low / pip_size,
                mfe_pips_upper=mfe_upp / pip_size,
                mae_pips_lower=mae_low / pip_size,
                mae_pips_upper=mae_upp / pip_size,
                mfe_atr_lower=mfe_low / atr,
                mfe_atr_upper=mfe_upp / atr,
                mae_atr_lower=mae_low / atr,
                mae_atr_upper=mae_upp / atr,
                full_mfe_pips=full_mfe_pips,
                full_mae_pips=full_mae_pips,
                full_mfe_atr=full_mfe_atr,
                full_mae_atr=full_mae_atr,
            )

        if target_touched:
            mfe_low = max(prior_mfe_price, target_dist)
            mfe_upp = max(prior_mfe_price, bar_mfe)
            mae_low = prior_mae_price
            mae_upp = max(prior_mae_price, bar_mae)

            return TradeOutcome(
                horizon_bars=horizon,
                stop_atr=stop_atr,
                target_atr=target_atr,
                cell_label=cell_label,
                reward_risk_ratio=rr_ratio,
                dual_touch_mode=dual_touch_mode,
                exit_reason="TARGET",
                is_win=True,
                is_loss=False,
                is_timeout=False,
                dual_touch=False,
                is_opening_gap=False,
                exit_price=target_price,
                exit_bar_idx=bar_num,
                exit_time_server_text=bar.time_server_text,
                bars_to_exit=bar_num,
                clock_seconds_to_exit_bar_open=bar_open_sec,
                clock_seconds_to_exit_bar_close=bar_close_sec,
                clock_seconds_bar_close_proxy=bar_close_sec,  # Upper-bound / bar-close proxy
                gross_r=rr_ratio,
                signed_pips=target_dist / pip_size,
                mfe_pips_lower=mfe_low / pip_size,
                mfe_pips_upper=mfe_upp / pip_size,
                mae_pips_lower=mae_low / pip_size,
                mae_pips_upper=mae_upp / pip_size,
                mfe_atr_lower=mfe_low / atr,
                mfe_atr_upper=mfe_upp / atr,
                mae_atr_lower=mae_low / atr,
                mae_atr_upper=mae_upp / atr,
                full_mfe_pips=full_mfe_pips,
                full_mae_pips=full_mae_pips,
                full_mfe_atr=full_mfe_atr,
                full_mae_atr=full_mae_atr,
            )

        # Update prior complete bar excursions
        prior_mfe_price = max(prior_mfe_price, bar_mfe)
        prior_mae_price = max(prior_mae_price, bar_mae)

    # 4. Timeout Exit at Close of Bar Hmax
    last_bar = path_bars[-1]
    timeout_exit_price = last_bar.close
    signed_pips = direction * (timeout_exit_price - entry_price) / pip_size
    gross_r = direction * (timeout_exit_price - entry_price) / stop_dist

    # Entire last bar completed before timeout exit, so full extremes are exact
    mfe_low = prior_mfe_price
    mfe_upp = prior_mfe_price
    mae_low = prior_mae_price
    mae_upp = prior_mae_price

    timeout_open_sec = last_bar.timestamp - entry_timestamp
    timeout_close_sec = (last_bar.timestamp + 3600) - entry_timestamp

    return TradeOutcome(
        horizon_bars=horizon,
        stop_atr=stop_atr,
        target_atr=target_atr,
        cell_label=cell_label,
        reward_risk_ratio=rr_ratio,
        dual_touch_mode=dual_touch_mode,
        exit_reason="TIMEOUT",
        is_win=False,
        is_loss=False,
        is_timeout=True,
        dual_touch=False,
        is_opening_gap=False,
        exit_price=timeout_exit_price,
        exit_bar_idx=horizon,
        exit_time_server_text=last_bar.time_server_text,
        bars_to_exit=horizon,
        clock_seconds_to_exit_bar_open=timeout_open_sec,
        clock_seconds_to_exit_bar_close=timeout_close_sec,
        clock_seconds_bar_close_proxy=timeout_close_sec,  # Exact timeout duration at close of Hmax
        gross_r=gross_r,
        signed_pips=signed_pips,
        mfe_pips_lower=mfe_low / pip_size,
        mfe_pips_upper=mfe_upp / pip_size,
        mae_pips_lower=mae_low / pip_size,
        mae_pips_upper=mae_upp / pip_size,
        mfe_atr_lower=mfe_low / atr,
        mfe_atr_upper=mfe_upp / atr,
        mae_atr_lower=mae_low / atr,
        mae_atr_upper=mae_upp / atr,
        full_mfe_pips=full_mfe_pips,
        full_mae_pips=full_mae_pips,
        full_mfe_atr=full_mfe_atr,
        full_mae_atr=full_mae_atr,
    )


def calculate_median(values: List[float]) -> Optional[float]:
    """Calculates median with even-N average of middle two."""
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def calculate_quantile(values: List[float], q: float) -> Optional[float]:
    """Nearest-rank quantile using ceil(q * N), 1-indexed."""
    if not values:
        return None
    if not (0.0 <= q <= 1.0):
        raise ValueError(f"Quantile q must be between 0 and 1, got {q}")
    s = sorted(values)
    n = len(s)
    k = math.ceil(q * n)
    k = max(1, min(k, n))  # clamp to 1..N
    return float(s[k - 1])


def summarize_distribution(values: List[float]) -> Dict[str, Any]:
    """Returns distribution summary: count, mean, median, p75, p90, min, max."""
    if not values:
        return {
            "count": 0, "mean": None, "median": None,
            "p75": None, "p90": None, "min": None, "max": None
        }
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "median": calculate_median(values),
        "p75": calculate_quantile(values, 0.75),
        "p90": calculate_quantile(values, 0.90),
        "min": min(values),
        "max": max(values),
    }


def calculate_true_loyo(trials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes true Leave-One-Year-Out (LOYO) cross-validation aggregates.

    Per V2 Specification:
    - Iterates over each observed calendar year in Core (2015..2025).
    - Excludes that year completely from the sample.
    - Recalculates aggregate metrics on the remaining N observations:
      remaining N, wins, losses, timeouts, gross sum R, and gross mean R.
    - Partial year 2026 is strictly excluded from LOYO folds.
    - Empty years are not turned into zero-result folds.
    """
    # Identify unique core years (2015..2025) present in the trial sample
    core_years = sorted(list(set(
        str(r["year"]) for r in trials
        if str(r.get("year", "")) >= "2015" and str(r.get("year", "")) <= "2025"
    )))

    if not core_years:
        return {
            "loyo_total_folds": 0,
            "loyo_positive_years": 0,
            "loyo_min_mean_r": None,
            "loyo_max_mean_r": None,
            "loyo_min_sum_r": None,
            "loyo_max_sum_r": None,
            "loyo_folds": {},
        }

    folds = {}
    sum_r_list = []
    mean_r_list = []
    positive_count = 0

    for y in core_years:
        # Exclude year y, restrict to 2015..2025 core
        rem_trials = [
            r for r in trials
            if str(r["year"]) != y and str(r.get("year", "")) >= "2015" and str(r.get("year", "")) <= "2025"
        ]
        n_rem = len(rem_trials)
        if n_rem == 0:
            continue

        w_rem = sum(1 for r in rem_trials if r["is_win"])
        l_rem = sum(1 for r in rem_trials if r["is_loss"])
        t_rem = sum(1 for r in rem_trials if r["is_timeout"])
        sum_r_rem = sum(float(r["gross_r"]) for r in rem_trials)
        mean_r_rem = sum_r_rem / n_rem
        is_pos = (sum_r_rem > 0)

        if is_pos:
            positive_count += 1

        sum_r_list.append(sum_r_rem)
        mean_r_list.append(mean_r_rem)

        folds[y] = {
            "excluded_year": y,
            "remaining_n": n_rem,
            "wins": w_rem,
            "losses": l_rem,
            "timeouts": t_rem,
            "gross_sum_r": sum_r_rem,
            "gross_mean_r": mean_r_rem,
            "is_positive": is_pos,
        }

    return {
        "loyo_total_folds": len(folds),
        "loyo_positive_years": positive_count,
        "loyo_min_mean_r": min(mean_r_list) if mean_r_list else None,
        "loyo_max_mean_r": max(mean_r_list) if mean_r_list else None,
        "loyo_min_sum_r": min(sum_r_list) if sum_r_list else None,
        "loyo_max_sum_r": max(sum_r_list) if sum_r_list else None,
        "loyo_folds": folds,
    }


def summarize_exit_distributions(trials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes separate bars-to-exit and elapsed-seconds distributions for TP (wins), SL (losses), and overall.

    Trading bar duration: bars_to_exit (integer H1 observed bars).
    Wall-clock duration proxy: clock_seconds_bar_close_proxy, which differs by exit type:
    - Opening-gap exits (TARGET_GAP, STOP_GAP): execution is at bar open (exact); both
      clock_seconds_to_bar_open and clock_seconds_bar_close_proxy equal bar_open_sec.
    - Intrabar touch exits (TARGET, STOP): exact sub-hour timestamp unknown; clock_seconds_to_bar_open
      is the lower bound and clock_seconds_bar_close_proxy is the upper-bound proxy (bar_close_sec).
    - Timeout exit: exact at close of Hmax bar; clock_seconds_bar_close_proxy = bar_close_sec (exact).

    Empty distributions return None for all quantiles and extremes.
    """
    tp_bars = [float(r["bars_to_exit"]) for r in trials if r["is_win"]]
    sl_bars = [float(r["bars_to_exit"]) for r in trials if r["is_loss"]]
    to_bars = [float(r["bars_to_exit"]) for r in trials if r["is_timeout"]]
    all_bars = [float(r["bars_to_exit"]) for r in trials]

    def _get_trial_proxy_seconds(r: Dict[str, Any]) -> float:
        if "clock_seconds_bar_close_proxy" in r and r["clock_seconds_bar_close_proxy"] is not None and str(r["clock_seconds_bar_close_proxy"]) != "":
            return float(r["clock_seconds_bar_close_proxy"])
        if "clock_seconds_to_exit_bar_close" in r and r["clock_seconds_to_exit_bar_close"] is not None and str(r["clock_seconds_to_exit_bar_close"]) != "":
            return float(r["clock_seconds_to_exit_bar_close"])
        if "elapsed_seconds" in r and r["elapsed_seconds"] is not None and str(r["elapsed_seconds"]) != "":
            return float(r["elapsed_seconds"])
        return float(r["bars_to_exit"]) * 3600.0

    tp_secs = [_get_trial_proxy_seconds(r) for r in trials if r["is_win"]]
    sl_secs = [_get_trial_proxy_seconds(r) for r in trials if r["is_loss"]]
    to_secs = [_get_trial_proxy_seconds(r) for r in trials if r["is_timeout"]]
    all_secs = [_get_trial_proxy_seconds(r) for r in trials]

    tp_median_bars = calculate_median(tp_bars)
    tp_p75_bars = calculate_quantile(tp_bars, 0.75) if tp_bars else None
    tp_p90_bars = calculate_quantile(tp_bars, 0.90) if tp_bars else None
    tp_max_bars = max(tp_bars) if tp_bars else None

    tp_median_secs = calculate_median(tp_secs)
    tp_p75_secs = calculate_quantile(tp_secs, 0.75) if tp_secs else None
    tp_p90_secs = calculate_quantile(tp_secs, 0.90) if tp_secs else None
    tp_max_secs = max(tp_secs) if tp_secs else None

    sl_median_bars = calculate_median(sl_bars)
    sl_p75_bars = calculate_quantile(sl_bars, 0.75) if sl_bars else None
    sl_p90_bars = calculate_quantile(sl_bars, 0.90) if sl_bars else None
    sl_max_bars = max(sl_bars) if sl_bars else None

    sl_median_secs = calculate_median(sl_secs)
    sl_p75_secs = calculate_quantile(sl_secs, 0.75) if sl_secs else None
    sl_p90_secs = calculate_quantile(sl_secs, 0.90) if sl_secs else None
    sl_max_secs = max(sl_secs) if sl_secs else None

    overall_median_bars = calculate_median(all_bars)
    overall_p75_bars = calculate_quantile(all_bars, 0.75) if all_bars else None
    overall_p90_bars = calculate_quantile(all_bars, 0.90) if all_bars else None
    overall_max_bars = max(all_bars) if all_bars else None

    overall_median_secs = calculate_median(all_secs)
    overall_p75_secs = calculate_quantile(all_secs, 0.75) if all_secs else None
    overall_p90_secs = calculate_quantile(all_secs, 0.90) if all_secs else None
    overall_max_secs = max(all_secs) if all_secs else None

    return {
        # Win (TP) distribution
        "tp_n": len(tp_bars),
        "tp_median_bars": tp_median_bars,
        "tp_p75_bars": tp_p75_bars,
        "tp_p90_bars": tp_p90_bars,
        "tp_max_bars": tp_max_bars,
        "tp_bar_close_proxy_seconds_median": tp_median_secs,
        "tp_bar_close_proxy_seconds_p75": tp_p75_secs,
        "tp_bar_close_proxy_seconds_p90": tp_p90_secs,
        "tp_bar_close_proxy_seconds_max": tp_max_secs,
        # Backward-compatible aliases
        "tp_median_seconds": tp_median_secs,
        "tp_p75_seconds": tp_p75_secs,
        "tp_p90_seconds": tp_p90_secs,
        "tp_max_seconds": tp_max_secs,

        # Loss (SL) distribution
        "sl_n": len(sl_bars),
        "sl_median_bars": sl_median_bars,
        "sl_p75_bars": sl_p75_bars,
        "sl_p90_bars": sl_p90_bars,
        "sl_max_bars": sl_max_bars,
        "sl_bar_close_proxy_seconds_median": sl_median_secs,
        "sl_bar_close_proxy_seconds_p75": sl_p75_secs,
        "sl_bar_close_proxy_seconds_p90": sl_p90_secs,
        "sl_bar_close_proxy_seconds_max": sl_max_secs,
        # Backward-compatible aliases
        "sl_median_seconds": sl_median_secs,
        "sl_p75_seconds": sl_p75_secs,
        "sl_p90_seconds": sl_p90_secs,
        "sl_max_seconds": sl_max_secs,

        # Timeout distribution
        "to_n": len(to_bars),
        "to_bars": to_bars[0] if to_bars else None,
        "to_exact_seconds_median": calculate_median(to_secs),

        # Overall distribution
        "overall_n": len(all_bars),
        "overall_median_bars": overall_median_bars,
        "overall_p75_bars": overall_p75_bars,
        "overall_p90_bars": overall_p90_bars,
        "overall_max_bars": overall_max_bars,
        "overall_bar_close_proxy_seconds_median": overall_median_secs,
        "overall_bar_close_proxy_seconds_p75": overall_p75_secs,
        "overall_bar_close_proxy_seconds_p90": overall_p90_secs,
        "overall_bar_close_proxy_seconds_max": overall_max_secs,
        # Backward-compatible aliases
        "overall_median_seconds": overall_median_secs,
        "overall_p75_seconds": overall_p75_secs,
        "overall_p90_seconds": overall_p90_secs,
        "overall_max_seconds": overall_max_secs,
    }


def summarize_annual_breakdown(trials: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Computes exact annual performance breakdown for each observed calendar year."""
    by_year = defaultdict(list)
    for r in trials:
        by_year[str(r["year"])].append(r)

    annual = {}
    for y in sorted(by_year.keys()):
        yr_trials = by_year[y]
        n = len(yr_trials)
        w = sum(1 for r in yr_trials if r["is_win"])
        l = sum(1 for r in yr_trials if r["is_loss"])
        t = sum(1 for r in yr_trials if r["is_timeout"])
        s_r = sum(float(r["gross_r"]) for r in yr_trials)
        m_r = s_r / n if n > 0 else 0.0
        wr = w / n if n > 0 else 0.0
        cohort = "PARTIAL_2026" if y == "2026" else "CORE_2015_2025"

        annual[y] = {
            "year": y,
            "cohort": cohort,
            "n": n,
            "wins": w,
            "losses": l,
            "timeouts": t,
            "win_rate": wr,
            "gross_sum_r": s_r,
            "gross_mean_r": m_r,
        }
    return annual


def format_optional_float(val: Optional[float], spec: str = ".4f", missing: str = "") -> str:
    """Formats float with specification string, or returns missing string if None.

    Guarantees that empty distributions or missing statistics serialize as empty
    strings rather than misleading 0.0 or 0 values.
    """
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return missing
    return f"{val:{spec}}"


ACTIVE_USD_PAIRS: List[str] = ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"]


def get_expected_summary_keys(family_name: str) -> Set[Tuple[str, str, str, str, int, str]]:
    """Generates the complete set of expected primary keys for summary_grid_results.csv.

    Primary Key: (panel, pair, signal_type, cohort_filter, horizon_bars, cell_label)
    """
    signals = ["af", "ap"]
    horizons = EXPLORATION_HORIZONS
    cohorts = ["ALL_ELIGIBLE", "COMMON_H240"]
    cell_labels = [c.label for c in ALL_GRID_CELLS]

    if family_name == "CPI":
        panel_pairs = []
        for pan in ["JOBLESS_CLAIMS_CLEAN", "FULL_PANEL"]:
            for pr in ACTIVE_USD_PAIRS + ["ALL_PAIRS_COMBINED"]:
                panel_pairs.append((pan, pr))
    elif family_name == "NFP":
        panel_pairs = []
        for pan in ["PRIMARY_PANEL", "FULL_PANEL"]:
            for pr in ACTIVE_USD_PAIRS + ["ALL_PAIRS_COMBINED"]:
                panel_pairs.append((pan, pr))
        panel_pairs.append(("USDCAD_CAD_JOBS_CLEAN", "USDCAD"))
        panel_pairs.append(("USDCAD_FULL", "USDCAD"))
    else:
        raise ValueError(f"Unknown family: {family_name}")

    keys = set()
    for pan, pr in panel_pairs:
        for sig in signals:
            for ch in cohorts:
                for h in horizons:
                    for cell in cell_labels:
                        keys.add((pan, pr, sig, ch, h, cell))
    return keys


def index_trial_records(
    trials: List[Dict[str, Any]],
    family_name: str
) -> Dict[Tuple[str, str, str, str, int, str], List[Dict[str, Any]]]:
    """Indexes trial records once by (panel, pair, signal_type, cohort_filter, horizon_bars, cell_label).

    Eliminates redundant linear rescanning across ~240k-270k rows while preserving exact arithmetic.
    """
    indexed = defaultdict(list)

    for r in trials:
        sig = r["signal_type"]
        h = int(r["horizon_bars"]) if "horizon_bars" in r else int(r["horizon"])
        cell = r["cell_label"]
        pair = r["pair"]

        claims_col = r.get("has_us_jobless_claims_collision", r.get("claims_collision", False))
        if isinstance(claims_col, str):
            claims_col = claims_col.strip().lower() in ("true", "1")
        else:
            claims_col = bool(claims_col)

        cad_col = r.get("has_cad_employment_collision", r.get("cad_collision", False))
        if isinstance(cad_col, str):
            cad_col = cad_col.strip().lower() in ("true", "1")
        else:
            cad_col = bool(cad_col)

        is_h240 = r.get("is_common_h240", r.get("h240_complete", False))
        if isinstance(is_h240, str):
            is_h240 = is_h240.strip().lower() in ("true", "1")
        else:
            is_h240 = bool(is_h240)

        # Panel membership
        if family_name == "CPI":
            panels = ["FULL_PANEL"]
            if not claims_col:
                panels.append("JOBLESS_CLAIMS_CLEAN")
        elif family_name == "NFP":
            panels = ["FULL_PANEL"]
            if pair != "USDCAD" or not cad_col:
                panels.append("PRIMARY_PANEL")
            if pair == "USDCAD":
                panels.append("USDCAD_FULL")
                if not cad_col:
                    panels.append("USDCAD_CAD_JOBS_CLEAN")
        else:
            raise ValueError(f"Unknown family: {family_name}")

        # Cohort membership
        cohorts = ["ALL_ELIGIBLE"]
        if is_h240:
            cohorts.append("COMMON_H240")

        # Map to matching groups
        for pan in panels:
            if pan in ("USDCAD_FULL", "USDCAD_CAD_JOBS_CLEAN"):
                pair_keys = ["USDCAD"]
            else:
                pair_keys = [pair, "ALL_PAIRS_COMBINED"]

            for pr in pair_keys:
                for ch in cohorts:
                    indexed[(pan, pr, sig, ch, h, cell)].append(r)

    return indexed
