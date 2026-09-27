"""
Audited CPI simulation ledger loader and presentation metrics formatting.
Fails closed on missing, malformed, or inconsistent ledger data.
Never uses silent zero/empty numeric fallbacks.
"""

import json
import os
from typing import Dict, Any, Optional

from .config import CPI_LEDGER_PATH


def get_r_stat_class(val: float) -> str:
    """Returns CSS class for R multiple coloring."""
    if val > 0.0001:
        return "stat-pos"
    elif val < -0.0001:
        return "stat-neg"
    return "stat-zero"


def format_trial_r_html(r_val: float, is_bold: bool = False) -> str:
    """Formats a trial R multiple with span tag and 2 decimal places."""
    cls = get_r_stat_class(r_val)
    val_str = f"{r_val:+.2f} R"
    if is_bold:
        return f'<span class="{cls}"><strong>{val_str}</strong></span>'
    return f'<span class="{cls}">{val_str}</span>'


def format_subgroup_r_html(r_val: float) -> str:
    """Formats subgroup R multiple (integer if whole, otherwise 1 decimal place)."""
    cls = get_r_stat_class(r_val)
    if abs(r_val - round(r_val)) < 0.0001:
        if abs(r_val) < 0.0001:
            val_str = "0 R"
        else:
            val_str = f"{r_val:+.0f} R"
    else:
        val_str = f"{r_val:+.1f} R"
    return f'<span class="{cls}">{val_str}</span>'


def load_cpi_ledger_data(ledger_data: Optional[Dict[str, Any]] = None, ledger_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads dynamic CPI simulation ledger data from disk or provided dictionary.
    Fails closed if the ledger file is absent; never silently reruns the simulation.
    """
    if ledger_data is not None:
        return ledger_data

    path = ledger_path or CPI_LEDGER_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"CPI trade ledger not found at '{path}'. The viewer generator will not silently "
            f"rerun the simulation. Please execute 'python \"TABLE VIEWER/cpi_simulation.py\"' "
            f"explicitly to generate the audited ledger."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_cpi_presentation_data(cpi_ledger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and prepares all formatted strings and metrics for the CPI presentation.
    Fails closed on missing or malformed ledger data.
    Never uses hardcoded numeric fallbacks; directly derives from ledger data.
    """
    if not isinstance(cpi_ledger_data, dict) or not cpi_ledger_data:
        raise ValueError("CPI ledger data must be a non-empty dictionary.")

    if "trials" not in cpi_ledger_data or not isinstance(cpi_ledger_data["trials"], dict):
        raise ValueError("CPI ledger data missing required 'trials' dictionary.")

    trials = cpi_ledger_data["trials"]
    required_trials = [
        "primary_1.5x_conservative",
        "sensitivity_1.0x_conservative",
        "sensitivity_2.0x_conservative"
    ]
    for t_name in required_trials:
        if t_name not in trials:
            raise ValueError(f"Missing required trial '{t_name}' in CPI ledger.")
        t_dict = trials[t_name]
        if not isinstance(t_dict, dict):
            raise ValueError(f"Trial '{t_name}' must be a dictionary.")
        if "metrics" not in t_dict or not isinstance(t_dict["metrics"], dict):
            raise ValueError(f"Trial '{t_name}' missing 'metrics' dictionary.")
        if "trades" not in t_dict or not isinstance(t_dict["trades"], list):
            raise ValueError(f"Trial '{t_name}' missing 'trades' list.")

        met = t_dict["metrics"]
        required_metrics = ["total_trades", "wins", "losses", "total_gross_r", "mean_gross_r"]
        for m_key in required_metrics:
            if m_key not in met or met[m_key] is None:
                raise ValueError(f"Trial '{t_name}' missing required metric '{m_key}'.")
            val = met[m_key]
            if m_key in ["total_trades", "wins", "losses"]:
                if not isinstance(val, int) or val < 0:
                    raise ValueError(f"Trial '{t_name}' metric '{m_key}' must be a non-negative integer, got {val}.")
            elif m_key in ["total_gross_r", "mean_gross_r"]:
                if not isinstance(val, (int, float)):
                    raise ValueError(f"Trial '{t_name}' metric '{m_key}' must be a numeric value, got {val}.")

        # 1. Require len(trades) == total_trades
        trades = t_dict["trades"]
        total_trades = met["total_trades"]
        if len(trades) != total_trades:
            raise ValueError(
                f"Trial '{t_name}' trade count mismatch: len(trades) ({len(trades)}) != "
                f"total_trades ({total_trades})."
            )

        # 2. Require wins + losses + ties == total_trades
        ties = met.get("ties", 0)
        if not isinstance(ties, int) or ties < 0:
            raise ValueError(f"Trial '{t_name}' metric 'ties' must be a non-negative integer, got {ties}.")
        if met["wins"] + met["losses"] + ties != total_trades:
            raise ValueError(
                f"Trial '{t_name}' outcome reconciliation failure: wins ({met['wins']}) + "
                f"losses ({met['losses']}) + ties ({ties}) != total_trades ({total_trades})."
            )

        # 3. Reconcile total_gross_r against sum of trade gross_r_multiple with small float tolerance
        trade_r_sum = 0.0
        for i, tr in enumerate(trades):
            if not isinstance(tr, dict):
                raise ValueError(f"Trial '{t_name}' trade at index {i} must be a dictionary.")
            if "gross_r_multiple" not in tr or tr["gross_r_multiple"] is None or not isinstance(tr["gross_r_multiple"], (int, float)):
                raise ValueError(f"Trial '{t_name}' trade at index {i} missing numeric 'gross_r_multiple'.")
            trade_r_sum += tr["gross_r_multiple"]

        if abs(trade_r_sum - met["total_gross_r"]) > 1e-3:
            raise ValueError(
                f"Trial '{t_name}' gross R reconciliation failure: sum of trade gross_r_multiple ({trade_r_sum:.4f}) != "
                f"total_gross_r ({met['total_gross_r']:.4f})."
            )

    p_trial = trials["primary_1.5x_conservative"]
    p_met = p_trial["metrics"]
    s1_trial = trials["sensitivity_1.0x_conservative"]
    s1_met = s1_trial["metrics"]
    s2_trial = trials["sensitivity_2.0x_conservative"]
    s2_met = s2_trial["metrics"]

    # Validate primary trial metrics
    primary_required = [
        "mean_risk_pips",
        "mean_gross_pnl_pips",
        "bars_held_distribution",
        "direction_splits",
        "co_release_splits",
        "best_trade",
        "gross_r_without_best_trade"
    ]
    for p_key in primary_required:
        if p_key not in p_met or p_met[p_key] is None:
            raise ValueError(f"Primary trial missing required metric '{p_key}'.")

    if not isinstance(p_met["mean_risk_pips"], (int, float)):
        raise ValueError("Primary trial 'mean_risk_pips' must be numeric.")
    if not isinstance(p_met["mean_gross_pnl_pips"], (int, float)):
        raise ValueError("Primary trial 'mean_gross_pnl_pips' must be numeric.")
    if not isinstance(p_met["gross_r_without_best_trade"], (int, float)):
        raise ValueError("Primary trial 'gross_r_without_best_trade' must be numeric.")

    best_tr = p_met["best_trade"]
    if not isinstance(best_tr, dict) or "release_time_server" not in best_tr or not best_tr["release_time_server"]:
        raise ValueError("Primary trial 'best_trade' must be a dictionary containing non-empty 'release_time_server'.")

    # Validate bars_held_distribution
    bars_held_dist = p_met["bars_held_distribution"]
    if not isinstance(bars_held_dist, dict):
        raise ValueError("Primary trial 'bars_held_distribution' must be a dictionary.")
    total_trades_cnt = p_met["total_trades"]
    if total_trades_cnt > 0 and len(bars_held_dist) == 0:
        raise ValueError("Primary trial 'bars_held_distribution' cannot be empty when total_trades > 0.")
    dist_sum = 0
    for b_k, b_cnt in bars_held_dist.items():
        if not isinstance(b_cnt, int) or b_cnt < 0:
            raise ValueError(f"Holding-time count for bar '{b_k}' must be a non-negative integer, got {b_cnt}.")
        dist_sum += b_cnt
    if dist_sum != total_trades_cnt:
        raise ValueError(
            f"Holding-time distribution sum ({dist_sum}) != total_trades ({total_trades_cnt})."
        )

    # Validate direction_splits
    dir_splits = p_met["direction_splits"]
    if not isinstance(dir_splits, dict):
        raise ValueError("Primary trial 'direction_splits' must be a dictionary.")
    for d_key in ["long_count", "short_count", "long_gross_r", "short_gross_r"]:
        if d_key not in dir_splits or dir_splits[d_key] is None:
            raise ValueError(f"Primary trial direction_splits missing required field '{d_key}'.")
    long_count = dir_splits["long_count"]
    short_count = dir_splits["short_count"]
    long_gross_r = dir_splits["long_gross_r"]
    short_gross_r = dir_splits["short_gross_r"]
    if not isinstance(long_count, int) or long_count < 0 or not isinstance(short_count, int) or short_count < 0:
        raise ValueError("Direction split counts must be non-negative integers.")
    if not isinstance(long_gross_r, (int, float)) or not isinstance(short_gross_r, (int, float)):
        raise ValueError("Direction split R values must be numeric.")

    total_trades_cnt = p_met["total_trades"]
    if long_count + short_count != total_trades_cnt:
        raise ValueError(
            f"Direction splits count reconciliation failure: long_count ({long_count}) + "
            f"short_count ({short_count}) != total_trades ({total_trades_cnt})."
        )
    if abs((long_gross_r + short_gross_r) - p_met["total_gross_r"]) > 1e-3:
        raise ValueError(
            f"Direction splits R reconciliation failure: long_gross_r ({long_gross_r}) + "
            f"short_gross_r ({short_gross_r}) != total_gross_r ({p_met['total_gross_r']})."
        )

    # Validate co_release_splits
    co_splits = p_met["co_release_splits"]
    if not isinstance(co_splits, dict):
        raise ValueError("Primary trial 'co_release_splits' must be a dictionary.")
    for c_key in ["jobless_claims_count", "jobless_claims_gross_r", "other_co_releases_count", "other_co_releases_gross_r"]:
        if c_key not in co_splits or co_splits[c_key] is None:
            raise ValueError(f"Primary trial co_release_splits missing required field '{c_key}'.")
    jobless_count = co_splits["jobless_claims_count"]
    jobless_gross_r = co_splits["jobless_claims_gross_r"]
    other_count = co_splits["other_co_releases_count"]
    other_gross_r = co_splits["other_co_releases_gross_r"]
    if not isinstance(jobless_count, int) or jobless_count < 0 or not isinstance(other_count, int) or other_count < 0:
        raise ValueError("Co-release split counts must be non-negative integers.")
    if not isinstance(jobless_gross_r, (int, float)) or not isinstance(other_gross_r, (int, float)):
        raise ValueError("Co-release split R values must be numeric.")

    if jobless_count + other_count != total_trades_cnt:
        raise ValueError(
            f"Co-release splits count reconciliation failure: jobless_claims_count ({jobless_count}) + "
            f"other_co_releases_count ({other_count}) != total_trades ({total_trades_cnt})."
        )
    if abs((jobless_gross_r + other_gross_r) - p_met["total_gross_r"]) > 1e-3:
        raise ValueError(
            f"Co-release splits R reconciliation failure: jobless_claims_gross_r ({jobless_gross_r}) + "
            f"other_co_releases_gross_r ({other_gross_r}) != total_gross_r ({p_met['total_gross_r']})."
        )

    # Ambiguous counts derivation directly from validated trades
    s1_ambig = sum(1 for t in s1_trial["trades"] if t.get("ambiguous_flag", False))
    p_ambig = sum(1 for t in p_trial["trades"] if t.get("ambiguous_flag", False))
    s2_ambig = sum(1 for t in s2_trial["trades"] if t.get("ambiguous_flag", False))

    # Format trial R values
    s1_gross_r_html = format_trial_r_html(s1_met["total_gross_r"])
    p_gross_r_html = format_trial_r_html(p_met["total_gross_r"], is_bold=True)
    s2_gross_r_html = format_trial_r_html(s2_met["total_gross_r"])

    # Subgroup R values
    long_r_html = format_subgroup_r_html(long_gross_r)
    short_r_html = format_subgroup_r_html(short_gross_r)
    jobless_r_html = format_subgroup_r_html(jobless_gross_r)
    other_r_html = format_subgroup_r_html(other_gross_r)

    # Primary trial trade field validation & subgroup target/stop counts derived directly from trades
    p_trades = p_trial["trades"]
    for i, tr in enumerate(p_trades):
        if tr.get("direction") not in ("LONG", "SHORT"):
            raise ValueError(f"Primary trial trade at index {i} has invalid direction: {tr.get('direction')}.")
        if not tr.get("exit_reason") or not isinstance(tr["exit_reason"], str):
            raise ValueError(f"Primary trial trade at index {i} missing valid string 'exit_reason'.")
        if "co_releases" not in tr or not isinstance(tr["co_releases"], (str, list)):
            raise ValueError(f"Primary trial trade at index {i} missing valid 'co_releases' string or list.")

    p_longs = [t for t in p_trades if t.get("direction") == "LONG"]
    p_shorts = [t for t in p_trades if t.get("direction") == "SHORT"]
    if len(p_longs) != long_count or len(p_shorts) != short_count:
        raise ValueError(
            f"Primary trial trade direction counts mismatch: Longs ({len(p_longs)}) != direction_splits long_count ({long_count}) "
            f"or Shorts ({len(p_shorts)}) != direction_splits short_count ({short_count})."
        )

    p_jobless = [t for t in p_trades if "840140001" in t.get("co_releases", [])]
    p_other = [t for t in p_trades if "840140001" not in t.get("co_releases", [])]
    if len(p_jobless) != jobless_count or len(p_other) != other_count:
        raise ValueError(
            f"Primary trial co-release trade counts mismatch: Jobless ({len(p_jobless)}) != co_release_splits jobless_claims_count ({jobless_count}) "
            f"or Other ({len(p_other)}) != co_release_splits other_co_releases_count ({other_count})."
        )

    p_long_targets = sum(1 for t in p_longs if t.get("exit_reason") == "TARGET")
    p_long_stops = sum(1 for t in p_longs if t.get("exit_reason") == "STOP")
    p_short_targets = sum(1 for t in p_shorts if t.get("exit_reason") == "TARGET")
    p_short_stops = sum(1 for t in p_shorts if t.get("exit_reason") == "STOP")

    p_jobless_targets = sum(1 for t in p_jobless if t.get("exit_reason") == "TARGET")
    p_jobless_stops = sum(1 for t in p_jobless if t.get("exit_reason") == "STOP")
    p_other_targets = sum(1 for t in p_other if t.get("exit_reason") == "TARGET")
    p_other_stops = sum(1 for t in p_other if t.get("exit_reason") == "STOP")

    # Holding time distribution
    bars_held_items = sorted(bars_held_dist.items(), key=lambda x: int(x[0]))
    bars_denom = total_trades_cnt if total_trades_cnt > 0 else 1
    bars_held_strs = [
        f"Bar {b}: {cnt} ({(cnt / bars_denom) * 100:.1f}%)"
        for b, cnt in bars_held_items
    ]
    bars_str_html = ", ".join(bars_held_strs)

    # Timeouts derived directly from validated trades
    timeout_cnt = sum(1 for t in p_trades if "TIMEOUT" in t.get("exit_reason", ""))
    exit_counts = p_met.get("exit_counts")
    if isinstance(exit_counts, dict) and "TIMEOUT_H24" in exit_counts:
        if exit_counts["TIMEOUT_H24"] != timeout_cnt:
            raise ValueError(
                f"Primary trial exit_counts.TIMEOUT_H24 ({exit_counts['TIMEOUT_H24']}) != "
                f"trade timeout exits ({timeout_cnt})."
            )

    if timeout_cnt == 0:
        timeout_str_html = "Zero trades reached H24 timeout."
    elif timeout_cnt == 1:
        timeout_str_html = "1 trade reached H24 timeout."
    else:
        timeout_str_html = f"{timeout_cnt} trades reached H24 timeout."

    return {
        "p_met": p_met,
        "s1_met": s1_met,
        "s2_met": s2_met,
        "s1_ambig": s1_ambig,
        "p_ambig": p_ambig,
        "s2_ambig": s2_ambig,
        "s1_gross_r_html": s1_gross_r_html,
        "p_gross_r_html": p_gross_r_html,
        "s2_gross_r_html": s2_gross_r_html,
        "total_trades_cnt": total_trades_cnt,
        "long_count": long_count,
        "short_count": short_count,
        "long_gross_r": long_gross_r,
        "short_gross_r": short_gross_r,
        "p_long_targets": p_long_targets,
        "p_long_stops": p_long_stops,
        "p_short_targets": p_short_targets,
        "p_short_stops": p_short_stops,
        "long_r_html": long_r_html,
        "short_r_html": short_r_html,
        "jobless_count": jobless_count,
        "jobless_gross_r": jobless_gross_r,
        "other_count": other_count,
        "other_gross_r": other_gross_r,
        "p_jobless_targets": p_jobless_targets,
        "p_jobless_stops": p_jobless_stops,
        "p_other_targets": p_other_targets,
        "p_other_stops": p_other_stops,
        "jobless_r_html": jobless_r_html,
        "other_r_html": other_r_html,
        "bars_str_html": bars_str_html,
        "timeout_str_html": timeout_str_html,
    }


def render_cpi_section(cpi_pres: Dict[str, Any], codex_display_approved: bool) -> str:
    """
    Renders the Forward-Test Setup Panel and Historical CPI Results Panel HTML.
    """
    if codex_display_approved:
        gate_style = ' style="display: none;"'
        numeric_style = ' style="display: block;"'
    else:
        gate_style = ' style="display: block;"'
        numeric_style = ' style="display: none;"'

    p_met = cpi_pres["p_met"]
    s1_met = cpi_pres["s1_met"]
    s2_met = cpi_pres["s2_met"]

    return f"""<!-- Forward-Test Setup Section (Under Audit) -->
<div id="forwardTestSection" class="forward-test-panel">
  <div class="forward-test-header">
    <div class="forward-test-title">
      <span class="forward-test-tag">UNDER AUDIT — NO REGISTERED SETUP</span>
      <h3>Candidate Forward-Test Setup: US CPI on EURUSD</h3>
    </div>
    <div class="forward-test-status">
      <span>Exploratory Baseline &bull; Pre-Registration Codex Audit</span>
    </div>
  </div>

  <div class="param-card">
    <div class="param-card-header">Candidate Parameter Card</div>
    <table class="param-table">
      <tr><th>Asset</th><td>EURUSD (Spot FX)</td></tr>
      <tr><th>Signal Bundle</th><td>USD CPI m/m (840030005) + USD Core CPI m/m (840030006)</td></tr>
      <tr><th>Concordance Gate</th><td>Both A &gt; F &rarr; SHORT; Both A &lt; F &rarr; LONG; Mixed/Zero &rarr; No Trade</td></tr>
      <tr><th>Collision Filter</th><td>12 Retail Sales shared timestamps excluded; Core PCE excluded</td></tr>
      <tr><th>Entry Timing</th><td>OPEN of exact next-hour H1 candle ((ts // 3600 + 1) * 3600; e.g. 16:00:00 for 15:30 release). Search forward across gaps disabled.</td></tr>
      <tr><th>Volatility Measure</th><td>ATR14 (14 completed H1 TR strictly ending prior to release timestamp: candle_time + 3600 &lt; release_ts; spike bar strictly excluded)</td></tr>
      <tr><th>Protective Stop</th><td>1.0 &times; ATR14 nominal from entry (fills at worse open if gapping)</td></tr>
      <tr><th>Profit Target</th><td>1.5 &times; ATR14 nominal (primary trial; sensitivities 1.0x, 2.0x; capped at target price on favorable gap)</td></tr>
      <tr><th>Max Holding</th><td>24 observed H1 candles (complete 24-bar path required; exits at H24 close if neither hit)</td></tr>
      <tr><th>Touch Precedence</th><td>Conservative (Stop first on same-bar touch; flagged ambiguous; optimistic sensitivity reported)</td></tr>
      <tr><th>Registration Governance</th><td>A candidate setup is registered <em>for</em> demo forward testing upon explicit pre-execution approval by the Project Director / Codex, after which it undergoes prospective forward evaluation. Zero setups are currently registered.</td></tr>
    </table>
  </div>
</div>

<!-- Separate Historical CPI Results Section (Audit Gated) -->
<div id="historicalCpiResultsSection" class="historical-results-panel">
  <div class="results-panel-header">
    <div class="results-panel-title">
      <span class="results-panel-tag">EXPLORATORY HISTORICAL SIMULATION — NO REGISTERED SETUP</span>
      <h3>Historical CPI Results: EURUSD (2015–2026, Partial)</h3>
    </div>
    <div class="results-disclaimer">
      <strong>Exploratory historical OHLC simulation; no registered setup.</strong>
      <br>Sample Period: 2015–2026 Full History ({cpi_pres['total_trades_cnt']} Directional Episodes) &bull; Pinned history ends at September 23, 2026 snapshot (2026 is partial). These figures are ledger-reconciled exploratory historical results, not evidence that a setup is registered or independently validated. These fixed all-years results do NOT change with the pair, year, or episode selectors on the Event Table tab.
    </div>
  </div>

  <!-- Audit Gate Card (Rendered when CODEX_DISPLAY_APPROVED is False) -->
  <div id="resultsAuditGateCard" class="results-audit-gate-card"{gate_style}>
    <div class="audit-gate-badge">AUDIT GATE ACTIVE</div>
    <h4>Awaiting Codex display audit</h4>
    <p>The historical CPI simulation results table has been programmatically implemented and reconciled against <code>cpi_trade_ledger.json</code>. Numeric display remains gated in the normal viewer pending independent Codex display authorization (<code>CODEX_DISPLAY_APPROVED = False</code>).</p>
    <p class="gate-governance-note">Exploratory historical OHLC simulation; no registered setup.</p>
  </div>

  <!-- Numeric Content Container (Rendered when CODEX_DISPLAY_APPROVED is True) -->
  <div id="resultsNumericContent" class="results-numeric-content"{numeric_style}>
    <div class="compact-table-outer">
      <table class="compact-results-table">
        <thead>
          <tr>
            <th>Target : Stop</th>
            <th>Trades N</th>
            <th>Target-First</th>
            <th>Stop-First</th>
            <th>Gross R</th>
            <th>Mean R</th>
            <th>Ambiguous N</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>1.0&times; : 1.0&times;</td>
            <td>{s1_met['total_trades']}</td>
            <td>{s1_met['wins']}</td>
            <td>{s1_met['losses']}</td>
            <td>{cpi_pres['s1_gross_r_html']}</td>
            <td>{s1_met['mean_gross_r']:+.2f} R</td>
            <td>{cpi_pres['s1_ambig']}</td>
          </tr>
          <tr class="highlight-primary-row">
            <td><strong>1.5&times; : 1.0&times; (PRIMARY)</strong></td>
            <td>{p_met['total_trades']}</td>
            <td>{p_met['wins']}</td>
            <td>{p_met['losses']}</td>
            <td>{cpi_pres['p_gross_r_html']}</td>
            <td>{p_met['mean_gross_r']:+.2f} R</td>
            <td>{cpi_pres['p_ambig']}</td>
          </tr>
          <tr>
            <td>2.0&times; : 1.0&times;</td>
            <td>{s2_met['total_trades']}</td>
            <td>{s2_met['wins']}</td>
            <td>{s2_met['losses']}</td>
            <td>{cpi_pres['s2_gross_r_html']}</td>
            <td>{s2_met['mean_gross_r']:+.2f} R</td>
            <td>{cpi_pres['s2_ambig']}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="results-table-note">
      <p><strong>Primary Trial Splits (Descriptive post-hoc observations, NOT new eligibility filters):</strong></p>
      <ul>
        <li><strong>Directional Split:</strong> Longs (N={cpi_pres['long_count']}): {cpi_pres['long_r_html']} ({cpi_pres['p_long_targets']} targets / {cpi_pres['p_long_stops']} stops) &bull; Shorts (N={cpi_pres['short_count']}): {cpi_pres['short_r_html']} ({cpi_pres['p_short_targets']} targets / {cpi_pres['p_short_stops']} stops)</li>
        <li><strong>Co-Release Split:</strong> {cpi_pres['jobless_count']} timestamps coinciding with Initial Jobless Claims: {cpi_pres['jobless_r_html']} ({cpi_pres['p_jobless_targets']} targets / {cpi_pres['p_jobless_stops']} stops) &bull; Remaining {cpi_pres['other_count']} timestamps: {cpi_pres['other_r_html']} ({cpi_pres['p_other_targets']} targets / {cpi_pres['p_other_stops']} stops)</li>
        <li><strong>Robustness Check:</strong> Removing single best trade (+1.50 R on {p_met['best_trade']['release_time_server']}): gross return = {p_met['gross_r_without_best_trade']:+.2f} R</li>
        <li><strong>Trade-Level Means:</strong> Mean risk: {p_met['mean_risk_pips']:.2f} pips &bull; Mean gross P&L: {p_met['mean_gross_pnl_pips']:+.2f} pips</li>
        <li><strong>Holding Time:</strong> {cpi_pres['bars_str_html']}. {cpi_pres['timeout_str_html']}</li>
      </ul>
      <p class="results-friction-warning">Gross mid/bid H1 prices only. Zero broker spread, slippage, commission, or overnight financing modeled. Evaluated on full-history unblinded data; a setup may be explicitly registered FOR prospective demo forward testing upon Project Director / Codex authorization, with prospective evaluation occurring AFTER registration. Historical figures here remain ledger-reconciled exploratory observations and do not constitute independent validation or automatic registration.</p>
      <p class="ledger-links">
        Audit Artifacts:
        <code>cpi_setup/cpi_trade_ledger.csv</code> &bull;
        <code>cpi_setup/cpi_decision_ledger.csv</code> &bull;
        <code>cpi_setup/cpi_trade_ledger.json</code> &bull;
        <code>cpi_setup/cpi_simulation_report.md</code>
      </p>
    </div>
  </div>
</div>"""
