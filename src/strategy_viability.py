"""
Pre-Price Strategy Viability Arithmetic & Scenario Definitions
Encapsulates trade execution arithmetic, 1-sample hypothesis testing,
and frozen decision gate classification.

Zero access to candidate prices or holdout outcomes.
"""

from typing import Dict, List, Any, Tuple
import math
import scipy.stats as stats

# Repository provenance constants (verified from FyodorResearchExport_v3 candle_symbols.csv)
EURUSD_DIGITS = 5
EURUSD_POINT = 0.00001           # 1 broker point = 10^-5
EURUSD_POINTS_PER_PIP = 10       # 1 pip = 0.00010 = 10 broker points

# Frozen Cost-Sensitivity Scenarios (in broker points and EURUSD pips)
FROZEN_COST_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "Scenario_0_Gross": {
        "points": 0,
        "pips": 0.0,
        "price_cost": 0.0,
        "description": "Frictionless theoretical benchmark (gross drift)"
    },
    "Scenario_1_Prime": {
        "points": 5,
        "pips": 0.5,
        "price_cost": 0.00005,
        "description": "Best-case prime institutional / tight ECN execution"
    },
    "Scenario_2_Standard": {
        "points": 10,
        "pips": 1.0,
        "price_cost": 0.00010,
        "description": "Standard retail / median execution friction during normal hours"
    },
    "Scenario_3_Stressed": {
        "points": 20,
        "pips": 2.0,
        "price_cost": 0.00020,
        "description": "Stressed execution (wider post-announcement spread and slippage)"
    }
}


def compute_executable_trade_prices(
    entry_bid: float,
    exit_bid: float,
    direction: int,
    spread_points: int,
    point_size: float = EURUSD_POINT
) -> Tuple[float, float]:
    """
    Computes executable entry and exit prices under bid-ask mechanics.

    direction == +1 (Long EURUSD):
      - Enters at Ask: entry_bid + spread_points * point_size
      - Exits at Bid: exit_bid

    direction == -1 (Short EURUSD):
      - Enters at Bid: entry_bid
      - Exits at Ask: exit_bid + spread_points * point_size
    """
    spread_cost = spread_points * point_size
    if direction == 1:
        entry_price = entry_bid + spread_cost
        exit_price = exit_bid
    elif direction == -1:
        entry_price = entry_bid
        exit_price = exit_bid + spread_cost
    else:
        raise ValueError(f"Direction must be +1 (Long) or -1 (Short), got {direction}")

    return entry_price, exit_price


def compute_directional_log_return(
    entry_bid: float,
    exit_bid: float,
    direction: int,
    spread_points: int = 0,
    point_size: float = EURUSD_POINT
) -> float:
    """
    Computes directional log return for a single trade:
      Long (+1):  ln(exit_price / entry_price)
      Short (-1): ln(entry_price / exit_price) = -ln(exit_price / entry_price)
    """
    entry_price, exit_price = compute_executable_trade_prices(
        entry_bid, exit_bid, direction, spread_points, point_size
    )
    if entry_price <= 0 or exit_price <= 0:
        raise ValueError("Prices must be strictly positive")

    if direction == 1:
        return math.log(exit_price / entry_price)
    else:
        return math.log(entry_price / exit_price)


def compute_directional_profit_pips(
    entry_bid: float,
    exit_bid: float,
    direction: int,
    spread_points: int = 0,
    point_size: float = EURUSD_POINT,
    points_per_pip: int = EURUSD_POINTS_PER_PIP
) -> float:
    """
    Computes trade profit in standard EURUSD pips.
    """
    entry_price, exit_price = compute_executable_trade_prices(
        entry_bid, exit_bid, direction, spread_points, point_size
    )
    if direction == 1:
        point_diff = (exit_price - entry_price) / point_size
    else:
        point_diff = (entry_price - exit_price) / point_size

    return point_diff / points_per_pip


def compute_1sample_viability_statistics(returns: List[float]) -> Dict[str, Any]:
    """
    Computes 1-sample Student's t viability statistics for an empirical return vector.
    Tests H0: mu <= 0 vs H1: mu > 0 (1-sided).

    Assumptions:
    1. Independent observations across monthly episodes (~30 days apart).
    2. Finite variance; sample mean approximately normal via Central Limit Theorem.
    """
    n = len(returns)
    if n < 2:
        raise ValueError("At least 2 observations required for t-distribution statistics")

    mean_ret = sum(returns) / n
    variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    std_dev = math.sqrt(variance)
    std_err = std_dev / math.sqrt(n)

    if std_err == 0:
        t_stat = 0.0
        p_val_1sided = 0.5
    else:
        t_stat = mean_ret / std_err
        # 1-sided p-value for H1: mu > 0
        p_val_1sided = float(1.0 - stats.t.cdf(t_stat, df=n - 1))

    # 95% 2-sided confidence interval for mu
    crit_t = float(stats.t.ppf(0.975, df=n - 1))
    ci_lower = mean_ret - crit_t * std_err
    ci_upper = mean_ret + crit_t * std_err

    # Win rate (proportion of strictly positive returns)
    wins = sum(1 for r in returns if r > 0)
    win_rate = wins / n

    return {
        "sample_size": n,
        "mean_return": mean_ret,
        "std_dev": std_dev,
        "std_error": std_err,
        "t_statistic": t_stat,
        "p_value_1sided": p_val_1sided,
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "win_rate": win_rate
    }


def classify_discovery_outcome(
    mean_net_standard: float,
    p_val_1sided: float,
    win_rate: float,
    ci_lower: float
) -> str:
    """
    Classifies empirical results according to the frozen pre-price decision gates.
    Uses Scenario 2 (Standard retail 10-point / 1.0-pip friction) as the primary viability hurdle.

    Outcomes:
    - DISCONFIRMED_NEGATIVE: mean_net <= 0 OR p >= 0.10
    - INCONCLUSIVE_FRAGILE: mean_net > 0 and 0.05 <= p < 0.10, OR win_rate < 0.50
    - PROMISING_DISCOVERY_CANDIDATE_FOR_HOLDOUT: mean_net > 0, p < 0.05, win_rate >= 0.53
    """
    if mean_net_standard <= 0.0 or p_val_1sided >= 0.10:
        return "DISCONFIRMED_NEGATIVE"

    if p_val_1sided < 0.05 and mean_net_standard > 0.0 and win_rate >= 0.53:
        return "PROMISING_DISCOVERY_CANDIDATE_FOR_HOLDOUT"

    return "INCONCLUSIVE_FRAGILE"
