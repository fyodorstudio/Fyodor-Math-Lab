"""Build the standalone viewer from the pinned, verified CPI/NFP V2 packages.

The HTML is a display artifact, not a calculator. Source strings for reported
statistics are copied unchanged from summary_grid_results.csv.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "HTML Viewer" / "table_viewer.html"
RUN_ID = "run_20260929_v2_final"
BEGIN = "<!-- VIEWER_DATA_BEGIN -->"
END = "<!-- VIEWER_DATA_END -->"
PAIRS = {"AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"}
PINNED_HASHES = {
    "CPI": {
        "manifest.json": "b8973be543a60d21ee08cf9456cd5211afcc6679eddffe5ae6ca579531036d03",
        "release_paths.csv": "e5f9177c5f80c6bd0432b3b18b3337665be56ff08ce247637c5706b787516d1f",
        "summary_grid_results.csv": "4da55653bf5b0918c2d9183caa22339e819193d935bff2c62a6b2a37b8ab2089",
        "trial_ledger.csv": "80eba119282f357159799504f58455f93498b4084265b945b0e5f8878f9c9de0",
        "annual_breakdown.csv": "33bf683c47c3999e74dfa94913b119d4116c5b61c940ae5ae8a5e71984ec307e",
        "loyo_folds.csv": "6b6e80778637589ed3ee216653fc2ef2f09a97e0b7cb2535b07b923a9c336712",
    },
    "NFP": {
        "manifest.json": "b7578e77979db8bfdf03ceff15549706ee9dac48727500e17e5d24110f99fe70",
        "release_paths.csv": "46d50ed51d73f5d9a5556cd8f46c6fae7537816eaa6058621b401c7f64ac5dde",
        "summary_grid_results.csv": "85160babd800843e941dde832eba8a1a1a106bc790957f7652f299275d4d5feb",
        "trial_ledger.csv": "ec7ab279d17b8cd3574c76bebf199b8352b97a80d502bcda659e172996464cee",
        "annual_breakdown.csv": "4a5dac25eb06b5400b472f7d17dd4328b11e53f4cd7579203c178d9f8755f539",
        "loyo_folds.csv": "36b61ae2c7d0c6a3666f73faa8c1b78e829b4d39b58226b6a193a8c53c9322f4",
    },
}
FIELDS = (
    "panel", "pair", "signal_type", "cohort_filter", "horizon_bars", "stop_atr",
    "target_atr", "N_bundles", "N_trades", "N_wins", "N_losses",
    "N_timeouts", "N_dual_touch", "gross_mean_r", "gross_sum_r",
    "tp_bars_median", "sl_bars_median", "overall_bars_median",
    "overall_bars_p90", "loyo_positive_years", "loyo_total_folds",
    "adj_mean_gross_r",
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def load_family(family):
    base = ROOT / "Research Candidate" / family
    package = base / f"{family}_EXPLORATION_V2" / RUN_ID
    with (package / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    if (manifest["family"], manifest["protocol_id"], manifest["run_id"],
            manifest["selection_policy"], manifest["provenance_verified"]) != (
            family, f"{family}_EXPLORATION_V2", RUN_ID, "NONE", True):
        raise ValueError(f"Invalid {family} package provenance")
    if set(manifest["parameters"]["active_pairs"]) != PAIRS:
        raise ValueError(f"Unexpected {family} pair universe")
    for filename, expected in PINNED_HASHES[family].items():
        if sha256(package / filename) != expected:
            raise ValueError(f"{family} {filename} differs from the verified final package")

    pre_path = base / f"pre_outcome_ledger_{family.lower()}_v2.csv"
    expected_pre_hash = {
        "CPI": "29ac66f511736121a0a588221df2a5d8c816722d9c79f9e72ff99c9fe28f0b66",
        "NFP": "157970c1788ce7cdd47291bcc9e94898e33559fd73fc7503bd7ed821483007cb",
    }[family]
    if sha256(pre_path) != expected_pre_hash:
        raise ValueError(f"{family} pre-outcome ledger hash changed")

    pre = {}
    for row in rows(pre_path):
        key = (row["bundle_id"], row["pair"])
        if key in pre or row["family"] != family or row["pair"] not in PAIRS:
            raise ValueError(f"Duplicate or unexpected {family} pre-outcome row: {key}")
        pre[key] = row

    paths = {}
    for row in rows(package / "release_paths.csv"):
        key = (row["bundle_id"], row["pair"])
        if key not in pre or row["timestamp"] != pre[key]["timestamp"]:
            raise ValueError(f"Unmatched {family} path: {key}")
        path = paths.setdefault(key, [])
        if int(row["bar_h"]) != len(path) + 1:
            raise ValueError(f"Non-contiguous {family} H1 path: {key}")
        path.append(float(row["pips_from_entry"]))
    if set(paths) != set(pre) or any(len(path) != 240 for path in paths.values()):
        raise ValueError(f"Incomplete {family} 240-bar release paths")

    episodes = []
    for key, row in pre.items():
        episodes.append([
            row["timestamp_server_text"], row["pair"], row["actual"],
            row["forecast"], row["previous"],
            row["has_us_jobless_claims_collision"] == "True",
            row["has_cad_employment_collision"] == "True",
            row["has_h240_path_gap_free"] == "True",
            row["is_candidate_eligible_h60_af"] == "True",
            row["is_candidate_eligible_h60_ap"] == "True",
            paths[key],
        ])
    episodes.sort(key=lambda r: (r[0], r[1]))

    summaries = []
    seen = set()
    groups = {}
    for row in rows(package / "summary_grid_results.csv"):
        key = tuple(row[field] for field in FIELDS[:7])
        if key in seen or row["pair"] not in PAIRS | {"ALL_PAIRS_COMBINED"}:
            raise ValueError(f"Duplicate or unexpected {family} summary cell: {key}")
        seen.add(key)
        group = tuple(row[field] for field in FIELDS[:5])
        groups[group] = groups.get(group, 0) + 1
        n = int(row["N_trades"])
        if int(row["N_wins"]) + int(row["N_losses"]) + int(row["N_timeouts"]) != n:
            raise ValueError(f"Bad {family} exit counts: {key}")
        summaries.append([row[field] for field in FIELDS])
    if any(count != 52 for count in groups.values()):
        raise ValueError(f"Incomplete {family} summary grid")

    return {
        "run": RUN_ID,
        "codeCommit": manifest["code_commit"],
        "sourceHashes": {
            "preOutcome": expected_pre_hash,
            "releasePaths": sha256(package / "release_paths.csv"),
            "summaryGrid": sha256(package / "summary_grid_results.csv"),
        },
        "episodes": episodes,
        "summaries": summaries,
    }


def build_html():
    source = HTML.read_text(encoding="utf-8")
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise ValueError("Viewer data markers must occur exactly once")
    payload = {"schema": 1, "families": {name: load_family(name) for name in ("CPI", "NFP")}}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    snippet = f'{BEGIN}\n<script type="application/json" id="viewer-data">{encoded}</script>\n{END}'
    before, rest = source.split(BEGIN, 1)
    _, after = rest.split(END, 1)
    return before + snippet + after, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check that the HTML matches source packages without writing")
    args = parser.parse_args()
    rendered, payload = build_html()
    if args.check:
        if rendered != HTML.read_text(encoding="utf-8"):
            raise SystemExit("Viewer is stale; rebuild from the verified local packages")
        print("Viewer matches source packages")
    else:
        HTML.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"Built {HTML}")
    for name, family in payload["families"].items():
        print(f"{name}: {len(family['episodes'])} event/pair rows, {len(family['summaries'])} summary cells")


if __name__ == "__main__":
    main()
