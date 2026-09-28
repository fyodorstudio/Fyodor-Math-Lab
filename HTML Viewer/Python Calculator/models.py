"""Data models for Fyodor Macro Research (Pre-Outcome Pass).

Strictly typed data structures for calendar events, releases, bundles,
and H1 candle data. Contains zero simulated trade outcome fields.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class CandleBar:
    """Represents a single verified H1 candle bar."""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int
    symbol: str
    time_server_text: str
    complete_at_export: bool

    def validate_ohlc(self) -> bool:
        """Verifies geometric OHLC validity."""
        return (
            self.low <= min(self.open, self.close) + 1e-9
            and max(self.open, self.close) <= self.high + 1e-9
            and self.low >= 0.0
            and self.open > 0.0
            and self.high > 0.0
            and self.close > 0.0
        )


@dataclass(frozen=True)
class CalendarRelease:
    """Represents an individual economic calendar release observation."""
    event_id: str
    value_id: str
    timestamp: int
    timestamp_server_text: str
    currency: str
    country_code: str
    event_name: str
    importance: str
    actual: Optional[float]
    forecast: Optional[float]
    previous: Optional[float]
    revised_previous: Optional[float]
    period_server_text: str
    unit: str
    unit_code: int
    multiplier: str
    multiplier_code: int
    digits: int
    raw_actual_str: str
    raw_forecast_str: str
    raw_previous_str: str
    raw_revised_previous_str: str


@dataclass
class ReleaseBundle:
    """Represents an atomic same-time economic release bundle.
    
    Macro releases occurring at the identical timestamp are evaluated
    as a unified bundle, never as isolated uncoordinated rows.
    """
    timestamp: int
    timestamp_server_text: str
    currency: str
    family: str
    constituents: Dict[str, CalendarRelease] = field(default_factory=dict)
    coincident_releases: List[CalendarRelease] = field(default_factory=list)

    @property
    def bundle_id(self) -> str:
        return f"{self.currency}_{self.family}_{self.timestamp}"


@dataclass
class PairPathCoverage:
    """Path, entry, and horizon availability for an active pair."""
    pair: str
    has_entry: bool
    entry_bar_idx: Optional[int] = None
    entry_timestamp: Optional[int] = None
    entry_time_server_text: Optional[str] = None
    entry_delay_seconds: Optional[int] = None
    entry_open_price: Optional[float] = None
    has_valid_entry_delay: bool = False  # delay <= max_allowed_entry_delay (e.g. 3600s)
    
    # Pre-release ATR warmup (strictly bar_close < release_timestamp)
    has_atr_warmup: bool = False
    pre_release_atr: Optional[float] = None
    
    # Raw bar counts from entry
    has_h60_bars: bool = False
    has_h120_bars: bool = False
    has_h240_bars: bool = False
    remaining_bars_from_entry: int = 0
    
    # Gap policy per horizon
    max_weekday_gap_sec_h60: int = 0
    max_weekday_gap_sec_h120: int = 0
    max_weekday_gap_sec_h240: int = 0
    has_h60_path_gap_free: bool = False
    has_h120_path_gap_free: bool = False
    has_h240_path_gap_free: bool = False


@dataclass
class PreOutcomeObservation:
    """Atomic (bundle, pair) pre-outcome eligibility record.
    
    Exposes audit identifiers, same-time collisions, signals,
    entry, pre-release ATR, and horizon path gates.
    Contains zero simulated trade outcome or profit calculations.
    """
    bundle_id: str
    timestamp: int
    timestamp_server_text: str
    year: str
    cohort: str  # CORE_2015_2025, PARTIAL_2026, POST_CUTOFF_2026
    family: str
    pair: str
    usd_role: str  # BASE or QUOTE
    
    # Anchor & Bundle audit fields
    anchor_event_id: str
    anchor_event_name: str
    anchor_present: bool
    same_time_bundle_event_ids: str
    coincident_collision_ids: str
    has_cad_employment_collision: bool
    has_us_trade_balance_collision: bool
    has_us_jobless_claims_collision: bool
    
    # Raw values of anchor
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    revised_previous: Optional[float] = None
    
    # Signals (A-F and A-P)
    signal_af: Optional[float] = None
    signal_ap: Optional[float] = None
    signal_af_state: str = "MISSING"  # POSITIVE, NEGATIVE, ZERO, MISSING
    signal_ap_state: str = "MISSING"  # POSITIVE, NEGATIVE, ZERO, MISSING
    
    # Hypothesized direction
    usd_currency_direction_af: Optional[int] = None
    pair_direction_af: Optional[int] = None
    usd_currency_direction_ap: Optional[int] = None
    pair_direction_ap: Optional[int] = None
    
    # Physical path coverage
    coverage: Optional[PairPathCoverage] = None
    
    # Horizon-specific Candidate Eligibility flags
    is_candidate_eligible_h60_af: bool = False
    is_candidate_eligible_h120_af: bool = False
    is_candidate_eligible_h240_af: bool = False
    
    is_candidate_eligible_h60_ap: bool = False
    is_candidate_eligible_h120_ap: bool = False
    is_candidate_eligible_h240_ap: bool = False
    
    # Primary exclusion reasons (mutually disjoint priority hierarchy)
    primary_exclusion_reason_h60_af: Optional[str] = None
    primary_exclusion_reason_h120_af: Optional[str] = None
    primary_exclusion_reason_h240_af: Optional[str] = None
    
    primary_exclusion_reason_h60_ap: Optional[str] = None
    primary_exclusion_reason_h120_ap: Optional[str] = None
    primary_exclusion_reason_h240_ap: Optional[str] = None
