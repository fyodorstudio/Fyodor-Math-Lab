"""
Pre-Price Strategy Viability Arithmetic & Scenario Definitions
Encapsulates trade execution arithmetic, 1-sample hypothesis testing,
and frozen decision gate classification.

Zero access to candidate prices or holdout outcomes.
"""

from typing import Dict, List, Any, Tuple, Optional
import math
import scipy.stats as stats

# Repository provenance constants (verified from FyodorResearchExport_v3 candle_symbols.csv)
EURUSD_DIGITS = 5
EURUSD_POINT = 0.00001           # 1 broker point = 10^-5
EURUSD_POINTS_PER_PIP = 10       # 1 pip = 0.00010 = 10 broker points

# Assumed Spread-Friction Sensitivity Scenarios (in broker points and EURUSD pips)
# NOTE: These are assumed sensitivity scenarios, NOT empirically established broker tiers.
# Spread-only deductions do not constitute all-in executable net profit.
# Scenario E (30 broker points / 3.0 pips) is a hypothetical combined-cost sensitivity,
# NOT an empirically established or verified all-in broker fee.
FROZEN_COST_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "Scenario_A_0pts": {
        "points": 0,
        "pips": 0.0,
        "price_cost": 0.00000,
        "coverage": "Frictionless theoretical benchmark (gross directional drift)"
    },
    "Scenario_B_5pts": {
        "points": 5,
        "pips": 0.5,
        "price_cost": 0.00005,
        "coverage": "Assumed minimal spread-only deduction (0.5 pips)"
    },
    "Scenario_C_10pts": {
        "points": 10,
        "pips": 1.0,
        "price_cost": 0.00010,
        "coverage": "Assumed moderate spread deduction (1.0 pip) - Primary Screening Hurdle"
    },
    "Scenario_D_20pts": {
        "points": 20,
        "pips": 2.0,
        "price_cost": 0.00020,
        "coverage": "Assumed conservative spread deduction (2.0 pips)"
    },
    "Scenario_E_30pts": {
        "points": 30,
        "pips": 3.0,
        "price_cost": 0.00030,
        "coverage": "Hypothetical combined-cost sensitivity (30 broker points / 3.0 pips; spread + assumed commission + execution slippage + swap buffer; unmeasured historical broker costs)"
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

    Input Validation:
    - Rejects non-finite values (NaN, Inf).
    - Rejects zero-variance samples (all identical values) where t-statistic is undefined.
    - Requires at least 2 observations.
    """
    if not isinstance(returns, (list, tuple)):
        raise TypeError("returns must be a list or tuple of numeric values")

    n = len(returns)
    if n < 2:
        raise ValueError(f"At least 2 observations required for t-distribution statistics, got {n}")

    for idx, r in enumerate(returns):
        if not isinstance(r, (int, float)):
            raise TypeError(f"Item at index {idx} is not numeric: {r}")
        if math.isnan(r) or math.isinf(r):
            raise ValueError(f"Item at index {idx} is non-finite (NaN or Inf): {r}")

    mean_ret = sum(returns) / n
    variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    std_dev = math.sqrt(variance)
    std_err = std_dev / math.sqrt(n)

    if std_err == 0.0 or variance == 0.0:
        raise ValueError(
            "Zero sample variance: all return observations are identical; t-statistic and p-value are undefined"
        )

    t_stat = mean_ret / std_err
    # 1-sided p-value for H1: mu > 0
    p_val_1sided = float(1.0 - stats.t.cdf(t_stat, df=n - 1))

    # 1-sided 95% lower confidence bound: [ci_95_1sided_lower, infinity)
    # Excludes zero if and only if p_val_1sided < 0.05
    crit_t_95_1sided = float(stats.t.ppf(0.95, df=n - 1))
    ci_95_1sided_lower = mean_ret - crit_t_95_1sided * std_err

    # 2-sided 95% confidence interval for mu (descriptive benchmark covering 2.5% in each tail)
    # May include zero when 0.025 <= p_val_1sided < 0.05
    crit_t_95_2sided = float(stats.t.ppf(0.975, df=n - 1))
    ci_95_2sided_lower = mean_ret - crit_t_95_2sided * std_err
    ci_95_2sided_upper = mean_ret + crit_t_95_2sided * std_err

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
        "ci_95_1sided_lower": ci_95_1sided_lower,
        "ci_95_2sided_lower": ci_95_2sided_lower,
        "ci_95_2sided_upper": ci_95_2sided_upper,
        "win_rate": win_rate
    }


def _validate_numeric(
    val: Any,
    name: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> float:
    """Validates that a numeric input is a real finite number within optional bounds."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(f"{name} must be a numeric value (int or float), got {type(val).__name__}: {val}")
    f_val = float(val)
    if math.isnan(f_val) or math.isinf(f_val):
        raise ValueError(f"{name} must be finite (not NaN or Inf), got {val}")
    if min_val is not None and f_val < min_val:
        raise ValueError(f"{name} must be >= {min_val}, got {val}")
    if max_val is not None and f_val > max_val:
        raise ValueError(f"{name} must be <= {max_val}, got {val}")
    return f_val


def classify_discovery_outcome(
    mean_net: float,
    p_val_1sided: float,
    win_rate: float,
    mean_net_friday: Optional[float] = None,
    mean_net_non_friday: Optional[float] = None
) -> str:
    """
    Classifies empirical results according to the pre-price decision gates.
    Uses Scenario C (Assumed 10-point / 1.0-pip spread friction) as the primary viability hurdle.

    Exhaustive Output Dispositions:
    1. DISCONFIRMED_ADVERSE:
       mean_net <= 0.0. The observed point estimate is flat or negative.
       The directional strategy hypothesis is disconfirmed.
    2. INCONCLUSIVE_UNDERPOWERED:
       mean_net > 0.0 but p_val_1sided >= 0.10.
       The point estimate is positive, but the data cannot distinguish drift from noise.
    3. INCONCLUSIVE_FRAGILE:
       mean_net > 0.0 and p_val_1sided < 0.10, BUT fails secondary consistency hurdles:
       - Marginally significant: 0.05 <= p_val_1sided < 0.10
       - Sub-hurdle win rate: win_rate < 0.53 (including < 0.50 and 50% to 52.9%)
       - Subgroup inconsistency: mean_net_friday <= 0.0 OR mean_net_non_friday <= 0.0
       - Missing subgroup verification: mean_net_friday is None OR mean_net_non_friday is None
    4. PROMISING_DISCOVERY_CANDIDATE:
       mean_net > 0.0 AND p_val_1sided < 0.05 AND win_rate >= 0.53
       AND mean_net_friday > 0.0 AND mean_net_non_friday > 0.0.
       Meets all pre-price discovery hurdles. Candidate for formal holdout verification.
       CRITICAL: This is NOT a registered setup.
    """
    mean_val = _validate_numeric(mean_net, "mean_net")
    p_val = _validate_numeric(p_val_1sided, "p_val_1sided", min_val=0.0, max_val=1.0)
    w_val = _validate_numeric(win_rate, "win_rate", min_val=0.0, max_val=1.0)

    fri_val: Optional[float] = None
    if mean_net_friday is not None:
        fri_val = _validate_numeric(mean_net_friday, "mean_net_friday")

    non_fri_val: Optional[float] = None
    if mean_net_non_friday is not None:
        non_fri_val = _validate_numeric(mean_net_non_friday, "mean_net_non_friday")

    # 1. Adverse point estimate (regardless of p-value or win rate)
    if mean_val <= 0.0:
        return "DISCONFIRMED_ADVERSE"

    # 2. Statistically underpowered (positive drift, but indistinguishable from zero)
    if p_val >= 0.10:
        return "INCONCLUSIVE_UNDERPOWERED"

    # 3. Check secondary hurdles for promising candidate
    # A. Marginal significance (0.05 <= p < 0.10)
    if p_val >= 0.05:
        return "INCONCLUSIVE_FRAGILE"

    # B. Win rate hurdle (< 53%, covering both < 50% and 50-52.9%)
    if w_val < 0.53:
        return "INCONCLUSIVE_FRAGILE"

    # C. Subgroup consistency (requires both Friday and Non-Friday means to be strictly positive)
    if fri_val is None or non_fri_val is None:
        return "INCONCLUSIVE_FRAGILE"

    if fri_val <= 0.0 or non_fri_val <= 0.0:
        return "INCONCLUSIVE_FRAGILE"

    # 4. Meets all discovery hurdles
    return "PROMISING_DISCOVERY_CANDIDATE"


def classify_holdout_outcome(
    n_holdout: int,
    mean_net: float,
    p_val_1sided: float,
    win_rate: float,
    discovery_mean_sign: int = 1
) -> str:
    """
    Classifies post-2022 holdout outcomes according to predeclared holdout decision gates.
    Uses Scenario C (Assumed 10-point / 1.0-pip friction) as the evaluation hurdle.

    Governance Rules:
    1. Sample adequacy (N_holdout >= 15) is evaluated FIRST. If N_holdout < 15, the sample
       is declared sample-deficient regardless of the observed mean or p-value.
    2. A holdout pass grants ELIGIBILITY FOR DEMO FORWARD VALIDATION ONLY.
       It does NOT constitute proof of a valid anomaly or executable profitability.

    Exhaustive Output Dispositions:
    1. HOLDOUT_SAMPLE_DEFICIENT:
       N_holdout < 15. The post-2022 holdout sample contains fewer than 15 eligible packages.
       The sample is underpowered for independent inference; descriptive metrics only.
    2. HOLDOUT_FAIL:
       N_holdout >= 15 AND mean_net <= 0.0.
       The out-of-sample directional point estimate is flat or negative.
       The candidate is permanently rejected as an in-sample discovery artifact.
    3. HOLDOUT_INCONCLUSIVE:
       N_holdout >= 15 AND mean_net > 0.0, BUT fails statistical or consistency hurdles:
       - p_val_1sided >= 0.05 (statistically insufficient to distinguish from noise)
       - win_rate < 0.50 (fewer than half of holdout trades profitable)
       - sign(mean_net) != discovery_mean_sign (directional flip)
       Candidate cannot be registered or advanced to demo trading.
    4. HOLDOUT_PASS_ELIGIBLE_FOR_DEMO:
       N_holdout >= 15 AND mean_net > 0.0 AND p_val_1sided < 0.05
       AND win_rate >= 0.50 AND sign(mean_net) == discovery_mean_sign.
       Candidate successfully replicates out-of-sample; eligible for demo forward validation.
    """
    if isinstance(n_holdout, bool) or not isinstance(n_holdout, int):
        raise TypeError(f"n_holdout must be an integer, got {type(n_holdout).__name__}: {n_holdout}")
    if n_holdout < 0:
        raise ValueError(f"n_holdout must be non-negative, got {n_holdout}")

    mean_val = _validate_numeric(mean_net, "mean_net")
    p_val = _validate_numeric(p_val_1sided, "p_val_1sided", min_val=0.0, max_val=1.0)
    w_val = _validate_numeric(win_rate, "win_rate", min_val=0.0, max_val=1.0)

    if isinstance(discovery_mean_sign, bool) or discovery_mean_sign not in (-1, 1):
        raise ValueError(f"discovery_mean_sign must be +1 or -1, got {discovery_mean_sign}")

    # Branch 1: Sample-deficient (first branch, evaluated regardless of observed mean)
    if n_holdout < 15:
        return "HOLDOUT_SAMPLE_DEFICIENT"

    # Branch 2: Point estimate flat or negative
    if mean_val <= 0.0:
        return "HOLDOUT_FAIL"

    # Branch 3: Inconclusive (positive drift, but fails statistical hurdle, win rate, or sign match)
    holdout_sign = 1 if mean_val > 0 else -1
    if p_val >= 0.05 or w_val < 0.50 or holdout_sign != discovery_mean_sign:
        return "HOLDOUT_INCONCLUSIVE"

    # Branch 4: Pass hurdles for demo forward validation
    return "HOLDOUT_PASS_ELIGIBLE_FOR_DEMO"

