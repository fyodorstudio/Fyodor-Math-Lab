"""Pre-Outcome Inventory and Eligibility Evaluator for US CPI and US NFP.

Produces:
- Release counts by year and cohort (2015-2025 Core, 2026 Partial, 2026 Post-Cutoff)
- Exact anchor event verification (CPI m/m 840030005, NFP 840030016; ZERO silent fallbacks)
- Dynamic raw constituent counts (558 for CPI, 560 for NFP)
- Same-time collision audit (Canadian Labour Force Survey, US Trade Balance, Jobless Claims)
- Timestamp-only Entry and Horizon coverage across the 7 active USD pairs
- Documented trading session gap policy enforcement (flagging/excluding multi-day weekday gaps like USDCHF 76h)
- Pre-release Wilder ATR(14) warmup (strictly bar_close < release_timestamp)
- Disjoint primary exclusions reconciling exactly to total observation denominators

Strictly PRE-OUTCOME: never computes price returns, ATR barrier hits, or trade PnL.
"""

import os
import csv
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict

from models import (
    CandleBar,
    CalendarRelease,
    ReleaseBundle,
    PairPathCoverage,
    PreOutcomeObservation,
)
from protocol_specs import (
    ACTIVE_USD_PAIRS,
    USD_BASE_PAIRS,
    USD_QUOTE_PAIRS,
    EVENT_ID_US_CPI_MM,
    EVENT_ID_US_CORE_CPI_MM,
    EVENT_ID_US_CPI_YY,
    EVENT_ID_US_CORE_CPI_YY,
    EVENT_ID_US_NONFARM_PAYROLLS,
    EVENT_ID_US_UNEMPLOYMENT_RATE,
    EVENT_ID_US_AVG_HOURLY_EARNINGS_MM,
    EVENT_ID_US_AVG_HOURLY_EARNINGS_YY,
    CORE_PANEL_START_TEXT,
    CORE_PANEL_END_TEXT,
    PARTIAL_PANEL_2026_END_TEXT,
    EVENT_ID_US_INITIAL_JOBLESS_CLAIMS,
    EVENT_ID_US_TRADE_BALANCE,
    EVENT_ID_CAD_EMPLOYMENT_CHANGE,
    EVENT_ID_CAD_UNEMPLOYMENT_RATE,
    compute_difference,
    classify_signal_state,
    invert_usd_direction_for_pair,
    assert_event_id_valid,
)
from data_loader import (
    load_candles,
    load_calendar_releases,
    load_all_releases_by_timestamp,
    create_release_bundles,
    DEFAULT_RAW_DIR,
)
from path_indexer import (
    find_entry_bar,
    calculate_pre_release_atr14,
    inspect_path_coverage,
    detect_path_weekday_gaps,
)


def determine_cohort(server_text: str) -> str:
    """Classifies release into chronological cohorts."""
    if server_text < CORE_PANEL_START_TEXT:
        return "PRE_2015"
    if server_text <= CORE_PANEL_END_TEXT:
        return "CORE_2015_2025"
    if server_text <= PARTIAL_PANEL_2026_END_TEXT:
        return "PARTIAL_2026"
    return "POST_CUTOFF_2026"


def evaluate_pair_coverage_for_bundle(
    pair: str,
    bundle_ts: int,
    pair_candles: List[CandleBar],
    max_entry_delay_seconds: int = 3600,
    max_allowed_weekday_gap_seconds: int = 14400,  # 4 hours
    allow_scheduled_holidays: bool = True,
) -> PairPathCoverage:
    """Evaluates entry, ATR, and horizon coverage for an active pair at a release timestamp."""
    # Pre-release ATR(14) strictly using bars closing earlier than release
    has_atr, atr_val, pre_bars = calculate_pre_release_atr14(pair_candles, bundle_ts)
    
    # Entry bar: earliest complete H1 candle with bar_open > bundle_ts
    entry_idx, entry_bar, delay_sec = find_entry_bar(pair_candles, bundle_ts)
    
    if entry_idx is None or entry_bar is None:
        return PairPathCoverage(
            pair=pair,
            has_entry=False,
            has_atr_warmup=has_atr,
            pre_release_atr=atr_val,
        )
        
    path_info = inspect_path_coverage(pair_candles, entry_idx)
    valid_delay = (delay_sec is not None and delay_sec <= max_entry_delay_seconds)
    
    # Gap checks per horizon
    gaps_60, max_gap_60 = detect_path_weekday_gaps(
        pair_candles, entry_idx, 60, allow_scheduled_holidays=allow_scheduled_holidays
    )
    gaps_120, max_gap_120 = detect_path_weekday_gaps(
        pair_candles, entry_idx, 120, allow_scheduled_holidays=allow_scheduled_holidays
    )
    gaps_240, max_gap_240 = detect_path_weekday_gaps(
        pair_candles, entry_idx, 240, allow_scheduled_holidays=allow_scheduled_holidays
    )
    
    has_h60_gap_free = (max_gap_60 <= max_allowed_weekday_gap_seconds)
    has_h120_gap_free = (max_gap_120 <= max_allowed_weekday_gap_seconds)
    has_h240_gap_free = (max_gap_240 <= max_allowed_weekday_gap_seconds)
    
    return PairPathCoverage(
        pair=pair,
        has_entry=True,
        entry_bar_idx=entry_idx,
        entry_timestamp=entry_bar.timestamp,
        entry_time_server_text=entry_bar.time_server_text,
        entry_delay_seconds=delay_sec,
        entry_open_price=entry_bar.open,
        has_valid_entry_delay=valid_delay,
        has_atr_warmup=has_atr,
        pre_release_atr=atr_val,
        has_h60_bars=path_info["has_h60"],
        has_h120_bars=path_info["has_h120"],
        has_h240_bars=path_info["has_h240"],
        remaining_bars_from_entry=path_info["remaining_bars"],
        max_weekday_gap_sec_h60=max_gap_60,
        max_weekday_gap_sec_h120=max_gap_120,
        max_weekday_gap_sec_h240=max_gap_240,
        has_h60_path_gap_free=has_h60_gap_free,
        has_h120_path_gap_free=has_h120_gap_free,
        has_h240_path_gap_free=has_h240_gap_free,
    )


def determine_primary_exclusion(
    cohort: str,
    anchor_present: bool,
    missing_anchor_reason: str,
    signal_val: Optional[float],
    signal_missing_reason: str,
    signal_state: str,
    cov: PairPathCoverage,
    horizon_bars: int,
    has_horizon_bars: bool,
    has_horizon_gap_free: bool,
) -> Optional[str]:
    """Assigns exactly one primary exclusion reason using a strict non-overlapping priority hierarchy."""
    # 1. Post-2026 cutoff
    if cohort == "POST_CUTOFF_2026":
        return "excluded_post_2026_cutoff"
    # 2. Missing anchor
    if not anchor_present:
        return missing_anchor_reason
    # 3. Missing required signal input (forecast or previous)
    if signal_val is None:
        return signal_missing_reason
    # 4. Zero / neutral signal (abstain)
    if signal_state == "ZERO":
        return "excluded_zero_signal"
    # 5. Missing entry bar
    if not cov.has_entry:
        return "excluded_no_entry_candle"
    # 6. Entry delay cap exceeded
    if not cov.has_valid_entry_delay:
        return "excluded_entry_delay_exceeded"
    # 7. Insufficient ATR pre-release warmup
    if not cov.has_atr_warmup:
        return "excluded_insufficient_atr_warmup"
    # 8. Path weekday gap policy violation
    if not has_horizon_gap_free:
        return "excluded_path_gap_exceeded"
    # 9. Insufficient horizon bars
    if not has_horizon_bars:
        return "excluded_insufficient_horizon_bars"
        
    return None


def evaluate_cpi_pre_outcome(
    raw_dir: str = DEFAULT_RAW_DIR,
    max_entry_delay_seconds: int = 3600,
    max_allowed_weekday_gap_seconds: int = 14400,
    allow_scheduled_holidays: bool = True,
) -> Tuple[List[ReleaseBundle], List[PreOutcomeObservation], int]:
    """Evaluates pre-outcome eligibility for US CPI m/m across the 7 active USD pairs.
    
    Anchor: CPI m/m (840030005) STRICTLY. ZERO silent fallback to y/y.
    """
    assert_event_id_valid(EVENT_ID_US_CPI_MM, raw_dir)
    assert_event_id_valid(EVENT_ID_US_INITIAL_JOBLESS_CLAIMS, raw_dir)
    assert_event_id_valid(EVENT_ID_US_TRADE_BALANCE, raw_dir)
    assert_event_id_valid(EVENT_ID_CAD_EMPLOYMENT_CHANGE, raw_dir)
    assert_event_id_valid(EVENT_ID_CAD_UNEMPLOYMENT_RATE, raw_dir)

    cpi_target_ids = {
        EVENT_ID_US_CPI_MM,
        EVENT_ID_US_CORE_CPI_MM,
        EVENT_ID_US_CPI_YY,
        EVENT_ID_US_CORE_CPI_YY,
    }
    usd_releases = load_calendar_releases("USD", raw_dir=raw_dir)
    all_by_ts = load_all_releases_by_timestamp(raw_dir=raw_dir)
    bundles = create_release_bundles("CPI", cpi_target_ids, usd_releases, all_by_ts)
    
    # Count raw constituent rows dynamically
    raw_constituent_count = sum(len(b.constituents) for b in bundles)
    
    candles = {p: load_candles(p, raw_dir=raw_dir) for p in ACTIVE_USD_PAIRS}
    observations: List[PreOutcomeObservation] = []
    
    for b in bundles:
        ts = b.timestamp
        txt = b.timestamp_server_text
        yr = txt[:4]
        cohort = determine_cohort(txt)
        
        # STRICT Anchor: CPI m/m (840030005) - NO FALLBACK TO Y/Y!
        anchor_rel = b.constituents.get(EVENT_ID_US_CPI_MM)
        anchor_present = (anchor_rel is not None)
        
        bundle_eids = ",".join(sorted(b.constituents.keys()))
        coincident_eids = "|".join(
            f"{c.currency}_{c.event_id}:{c.event_name}" for c in b.coincident_releases
        )
        
        has_cad_jobs = any(
            c.currency == "CAD" and c.event_id in (EVENT_ID_CAD_EMPLOYMENT_CHANGE, EVENT_ID_CAD_UNEMPLOYMENT_RATE)
            for c in b.coincident_releases
        )
        has_trade = any(
            c.currency == "USD" and c.event_id == EVENT_ID_US_TRADE_BALANCE
            for c in b.coincident_releases
        )
        has_claims = any(
            c.currency == "USD" and c.event_id == EVENT_ID_US_INITIAL_JOBLESS_CLAIMS
            for c in b.coincident_releases
        )
        
        actual_val = anchor_rel.actual if anchor_present else None
        forecast_val = anchor_rel.forecast if anchor_present else None
        previous_val = anchor_rel.previous if anchor_present else None
        rev_prev_val = anchor_rel.revised_previous if anchor_present else None
        
        sig_af = compute_difference(actual_val, forecast_val)
        sig_ap = compute_difference(actual_val, previous_val)
        
        af_state = classify_signal_state(sig_af)
        ap_state = classify_signal_state(sig_ap)
        
        usd_dir_af = 1 if af_state == "POSITIVE" else (-1 if af_state == "NEGATIVE" else None)
        usd_dir_ap = 1 if ap_state == "POSITIVE" else (-1 if ap_state == "NEGATIVE" else None)
        
        for pair in ACTIVE_USD_PAIRS:
            cov = evaluate_pair_coverage_for_bundle(
                pair, ts, candles[pair],
                max_entry_delay_seconds=max_entry_delay_seconds,
                max_allowed_weekday_gap_seconds=max_allowed_weekday_gap_seconds,
                allow_scheduled_holidays=allow_scheduled_holidays,
            )
            
            usd_role = "BASE" if pair in USD_BASE_PAIRS else "QUOTE"
            pair_dir_af = invert_usd_direction_for_pair(usd_dir_af, pair) if usd_dir_af is not None else None
            pair_dir_ap = invert_usd_direction_for_pair(usd_dir_ap, pair) if usd_dir_ap is not None else None
            
            # Exclusion reasons for each horizon under A-F
            ex_h60_af = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_cpi_mm",
                sig_af, "excluded_missing_forecast", af_state, cov,
                60, cov.has_h60_bars, cov.has_h60_path_gap_free
            )
            ex_h120_af = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_cpi_mm",
                sig_af, "excluded_missing_forecast", af_state, cov,
                120, cov.has_h120_bars, cov.has_h120_path_gap_free
            )
            ex_h240_af = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_cpi_mm",
                sig_af, "excluded_missing_forecast", af_state, cov,
                240, cov.has_h240_bars, cov.has_h240_path_gap_free
            )
            
            # Exclusion reasons for each horizon under A-P
            ex_h60_ap = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_cpi_mm",
                sig_ap, "excluded_missing_previous", ap_state, cov,
                60, cov.has_h60_bars, cov.has_h60_path_gap_free
            )
            ex_h120_ap = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_cpi_mm",
                sig_ap, "excluded_missing_previous", ap_state, cov,
                120, cov.has_h120_bars, cov.has_h120_path_gap_free
            )
            ex_h240_ap = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_cpi_mm",
                sig_ap, "excluded_missing_previous", ap_state, cov,
                240, cov.has_h240_bars, cov.has_h240_path_gap_free
            )
            
            obs = PreOutcomeObservation(
                bundle_id=b.bundle_id,
                timestamp=ts,
                timestamp_server_text=txt,
                year=yr,
                cohort=cohort,
                family="CPI",
                pair=pair,
                usd_role=usd_role,
                anchor_event_id=EVENT_ID_US_CPI_MM,
                anchor_event_name="CPI m/m",
                anchor_present=anchor_present,
                same_time_bundle_event_ids=bundle_eids,
                coincident_collision_ids=coincident_eids,
                has_cad_employment_collision=has_cad_jobs,
                has_us_trade_balance_collision=has_trade,
                has_us_jobless_claims_collision=has_claims,
                actual=actual_val,
                forecast=forecast_val,
                previous=previous_val,
                revised_previous=rev_prev_val,
                signal_af=sig_af,
                signal_ap=sig_ap,
                signal_af_state=af_state,
                signal_ap_state=ap_state,
                usd_currency_direction_af=usd_dir_af,
                pair_direction_af=pair_dir_af,
                usd_currency_direction_ap=usd_dir_ap,
                pair_direction_ap=pair_dir_ap,
                coverage=cov,
                is_candidate_eligible_h60_af=(ex_h60_af is None),
                is_candidate_eligible_h120_af=(ex_h120_af is None),
                is_candidate_eligible_h240_af=(ex_h240_af is None),
                is_candidate_eligible_h60_ap=(ex_h60_ap is None),
                is_candidate_eligible_h120_ap=(ex_h120_ap is None),
                is_candidate_eligible_h240_ap=(ex_h240_ap is None),
                primary_exclusion_reason_h60_af=ex_h60_af,
                primary_exclusion_reason_h120_af=ex_h120_af,
                primary_exclusion_reason_h240_af=ex_h240_af,
                primary_exclusion_reason_h60_ap=ex_h60_ap,
                primary_exclusion_reason_h120_ap=ex_h120_ap,
                primary_exclusion_reason_h240_ap=ex_h240_ap,
            )
            observations.append(obs)
            
    return bundles, observations, raw_constituent_count


def evaluate_nfp_pre_outcome(
    raw_dir: str = DEFAULT_RAW_DIR,
    max_entry_delay_seconds: int = 3600,
    max_allowed_weekday_gap_seconds: int = 14400,
    allow_scheduled_holidays: bool = True,
) -> Tuple[List[ReleaseBundle], List[PreOutcomeObservation], int]:
    """Evaluates pre-outcome eligibility for US NFP across the 7 active USD pairs.
    
    Anchor: Nonfarm Payrolls (840030016).
    """
    assert_event_id_valid(EVENT_ID_US_NONFARM_PAYROLLS, raw_dir)
    assert_event_id_valid(EVENT_ID_US_INITIAL_JOBLESS_CLAIMS, raw_dir)
    assert_event_id_valid(EVENT_ID_US_TRADE_BALANCE, raw_dir)
    assert_event_id_valid(EVENT_ID_CAD_EMPLOYMENT_CHANGE, raw_dir)
    assert_event_id_valid(EVENT_ID_CAD_UNEMPLOYMENT_RATE, raw_dir)

    nfp_target_ids = {
        EVENT_ID_US_NONFARM_PAYROLLS,
        EVENT_ID_US_UNEMPLOYMENT_RATE,
        EVENT_ID_US_AVG_HOURLY_EARNINGS_MM,
        EVENT_ID_US_AVG_HOURLY_EARNINGS_YY,
    }
    usd_releases = load_calendar_releases("USD", raw_dir=raw_dir)
    all_by_ts = load_all_releases_by_timestamp(raw_dir=raw_dir)
    bundles = create_release_bundles("NFP", nfp_target_ids, usd_releases, all_by_ts)
    
    raw_constituent_count = sum(len(b.constituents) for b in bundles)
    
    candles = {p: load_candles(p, raw_dir=raw_dir) for p in ACTIVE_USD_PAIRS}
    observations: List[PreOutcomeObservation] = []
    
    for b in bundles:
        ts = b.timestamp
        txt = b.timestamp_server_text
        yr = txt[:4]
        cohort = determine_cohort(txt)
        
        anchor_rel = b.constituents.get(EVENT_ID_US_NONFARM_PAYROLLS)
        anchor_present = (anchor_rel is not None)
        
        bundle_eids = ",".join(sorted(b.constituents.keys()))
        coincident_eids = "|".join(
            f"{c.currency}_{c.event_id}:{c.event_name}" for c in b.coincident_releases
        )
        
        has_cad_jobs = any(
            c.currency == "CAD" and c.event_id in (EVENT_ID_CAD_EMPLOYMENT_CHANGE, EVENT_ID_CAD_UNEMPLOYMENT_RATE)
            for c in b.coincident_releases
        )
        has_trade = any(
            c.currency == "USD" and c.event_id == EVENT_ID_US_TRADE_BALANCE
            for c in b.coincident_releases
        )
        has_claims = any(
            c.currency == "USD" and c.event_id == EVENT_ID_US_INITIAL_JOBLESS_CLAIMS
            for c in b.coincident_releases
        )
        
        actual_val = anchor_rel.actual if anchor_present else None
        forecast_val = anchor_rel.forecast if anchor_present else None
        previous_val = anchor_rel.previous if anchor_present else None
        rev_prev_val = anchor_rel.revised_previous if anchor_present else None
        
        sig_af = compute_difference(actual_val, forecast_val)
        sig_ap = compute_difference(actual_val, previous_val)
        
        af_state = classify_signal_state(sig_af)
        ap_state = classify_signal_state(sig_ap)
        
        usd_dir_af = 1 if af_state == "POSITIVE" else (-1 if af_state == "NEGATIVE" else None)
        usd_dir_ap = 1 if ap_state == "POSITIVE" else (-1 if ap_state == "NEGATIVE" else None)
        
        for pair in ACTIVE_USD_PAIRS:
            cov = evaluate_pair_coverage_for_bundle(
                pair, ts, candles[pair],
                max_entry_delay_seconds=max_entry_delay_seconds,
                max_allowed_weekday_gap_seconds=max_allowed_weekday_gap_seconds,
                allow_scheduled_holidays=allow_scheduled_holidays,
            )
            
            usd_role = "BASE" if pair in USD_BASE_PAIRS else "QUOTE"
            pair_dir_af = invert_usd_direction_for_pair(usd_dir_af, pair) if usd_dir_af is not None else None
            pair_dir_ap = invert_usd_direction_for_pair(usd_dir_ap, pair) if usd_dir_ap is not None else None
            
            ex_h60_af = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_nfp",
                sig_af, "excluded_missing_forecast", af_state, cov,
                60, cov.has_h60_bars, cov.has_h60_path_gap_free
            )
            ex_h120_af = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_nfp",
                sig_af, "excluded_missing_forecast", af_state, cov,
                120, cov.has_h120_bars, cov.has_h120_path_gap_free
            )
            ex_h240_af = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_nfp",
                sig_af, "excluded_missing_forecast", af_state, cov,
                240, cov.has_h240_bars, cov.has_h240_path_gap_free
            )
            
            ex_h60_ap = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_nfp",
                sig_ap, "excluded_missing_previous", ap_state, cov,
                60, cov.has_h60_bars, cov.has_h60_path_gap_free
            )
            ex_h120_ap = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_nfp",
                sig_ap, "excluded_missing_previous", ap_state, cov,
                120, cov.has_h120_bars, cov.has_h120_path_gap_free
            )
            ex_h240_ap = determine_primary_exclusion(
                cohort, anchor_present, "excluded_missing_anchor_nfp",
                sig_ap, "excluded_missing_previous", ap_state, cov,
                240, cov.has_h240_bars, cov.has_h240_path_gap_free
            )
            
            obs = PreOutcomeObservation(
                bundle_id=b.bundle_id,
                timestamp=ts,
                timestamp_server_text=txt,
                year=yr,
                cohort=cohort,
                family="NFP",
                pair=pair,
                usd_role=usd_role,
                anchor_event_id=EVENT_ID_US_NONFARM_PAYROLLS,
                anchor_event_name="Nonfarm Payrolls",
                anchor_present=anchor_present,
                same_time_bundle_event_ids=bundle_eids,
                coincident_collision_ids=coincident_eids,
                has_cad_employment_collision=has_cad_jobs,
                has_us_trade_balance_collision=has_trade,
                has_us_jobless_claims_collision=has_claims,
                actual=actual_val,
                forecast=forecast_val,
                previous=previous_val,
                revised_previous=rev_prev_val,
                signal_af=sig_af,
                signal_ap=sig_ap,
                signal_af_state=af_state,
                signal_ap_state=ap_state,
                usd_currency_direction_af=usd_dir_af,
                pair_direction_af=pair_dir_af,
                usd_currency_direction_ap=usd_dir_ap,
                pair_direction_ap=pair_dir_ap,
                coverage=cov,
                is_candidate_eligible_h60_af=(ex_h60_af is None),
                is_candidate_eligible_h120_af=(ex_h120_af is None),
                is_candidate_eligible_h240_af=(ex_h240_af is None),
                is_candidate_eligible_h60_ap=(ex_h60_ap is None),
                is_candidate_eligible_h120_ap=(ex_h120_ap is None),
                is_candidate_eligible_h240_ap=(ex_h240_ap is None),
                primary_exclusion_reason_h60_af=ex_h60_af,
                primary_exclusion_reason_h120_af=ex_h120_af,
                primary_exclusion_reason_h240_af=ex_h240_af,
                primary_exclusion_reason_h60_ap=ex_h60_ap,
                primary_exclusion_reason_h120_ap=ex_h120_ap,
                primary_exclusion_reason_h240_ap=ex_h240_ap,
            )
            observations.append(obs)
            
    return bundles, observations, raw_constituent_count
