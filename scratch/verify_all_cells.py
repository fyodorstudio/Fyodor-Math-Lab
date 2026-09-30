import json
import math
import os
import sys
import pandas as pd

def run_verification():
    print("=== STARTING DETERMINISTIC FORENSIC VERIFICATION ===")
    
    # 1. File existence
    sum_csv_path = 'Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_outcomes_v3/summary_grid_results.csv'
    ann_csv_path = 'Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_outcomes_v3/annual_breakdown.csv'
    json_path = 'HTML Viewer/cpi_bundle_viewer_payload.json'
    html_path = 'HTML Viewer/table_viewer.html'
    
    for p in [sum_csv_path, ann_csv_path, json_path, html_path]:
        assert os.path.exists(p), f"Missing file: {p}"
        print(f"Verified existence: {p} ({os.path.getsize(p):,} bytes)")

    # 2. Compare standalone JSON with embedded JSON in HTML
    print("\n--- Comparing Standalone JSON with Embedded HTML JSON ---")
    with open(json_path, 'r', encoding='utf-8') as f:
        json_file_content = f.read()
    json_obj = json.loads(json_file_content)
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    marker_start = '<script type="application/json" id="cpi-bundle-data">'
    marker_end = '</script>'
    idx1 = html_content.find(marker_start)
    assert idx1 != -1, "Marker for cpi-bundle-data not found in HTML"
    idx2 = html_content.find(marker_end, idx1)
    embedded_raw = html_content[idx1 + len(marker_start):idx2]
    # In embed_in_html, '<' was escaped to '\u003c'
    embedded_obj = json.loads(embedded_raw)
    
    # Check JSON equivalence
    assert json_obj == embedded_obj, "Embedded JSON in table_viewer.html does NOT match cpi_bundle_viewer_payload.json!"
    print("MATCH: Embedded JSON matches cpi_bundle_viewer_payload.json bit-for-bit in object semantics.")

    # 3. Deterministic verification of all 29,952 summary cells
    print("\n--- Verifying All 29,952 Summary Cells Against Source CSV ---")
    df_sum = pd.read_csv(sum_csv_path)
    print(f"Loaded summary CSV: {len(df_sum):,} rows")
    assert len(df_sum) == 29952, f"Expected 29,952 rows, got {len(df_sum)}"

    # Map payload summaries into a lookup
    payload_summaries = embedded_obj['summaries']
    
    # Expected keys
    expected_groups = df_sum.groupby(['panel', 'pair', 'comparison_id', 'cohort_filter', 'horizon_bars'])
    assert len(expected_groups) == len(payload_summaries), f"Group count mismatch: {len(expected_groups)} vs {len(payload_summaries)}"

    total_cells_checked = 0
    fractional_targets_count = 0
    
    # Check every row
    for (p, pair, comp, coh, h), group in expected_groups:
        key = f"{p}|{pair}|{comp}|{coh}|{h}"
        assert key in payload_summaries, f"Missing key in payload: {key}"
        cells = payload_summaries[key]
        assert len(cells) == len(group), f"Cell count mismatch for key {key}: {len(cells)} vs {len(group)}"
        
        for idx, (_, r) in enumerate(group.iterrows()):
            c = cells[idx]
            stop = c[0]
            target = c[1]
            cell_label = c[2]
            rr = c[3]
            nb = c[4]
            nt = c[5]
            w = c[6]
            l = c[7]
            t = c[8]
            dt = c[9]
            wr = c[10]
            sf_mean = c[11]
            sf_sum = c[12]
            tf_mean = c[13]
            tf_sum = c[14]
            loyo = c[15]
            loyo_min_mean = c[16]
            loyo_max_mean = c[17]
            loyo_min_sum = c[18]
            loyo_max_sum = c[19]
            tp_bar_med = c[20]
            sl_bar_med = c[21]
            all_bar_med = c[22]
            
            # Assert exact types and values
            assert stop == int(r['stop_atr']), f"Stop mismatch at {key} row {idx}: {stop} vs {r['stop_atr']}"
            assert math.isclose(target, float(r['target_atr']), abs_tol=1e-7), f"Target mismatch at {key} row {idx}: {target} vs {r['target_atr']}"
            if target != int(target):
                fractional_targets_count += 1
                
            assert cell_label == str(r['cell_label']), f"Cell label mismatch: {cell_label} vs {r['cell_label']}"
            assert rr == str(r['reward_risk']), f"RR mismatch: {rr} vs {r['reward_risk']}"
            assert nb == int(r['N_bundles']), f"N_bundles mismatch: {nb} vs {r['N_bundles']}"
            assert nt == int(r['N_trades']), f"N_trades mismatch: {nt} vs {r['N_trades']}"
            assert w == int(r['N_wins']), f"N_wins mismatch: {w} vs {r['N_wins']}"
            assert l == int(r['N_losses']), f"N_losses mismatch: {l} vs {r['N_losses']}"
            assert t == int(r['N_timeouts']), f"N_timeouts mismatch: {t} vs {r['N_timeouts']}"
            assert dt == int(r['N_dual_touch']), f"N_dual_touch mismatch: {dt} vs {r['N_dual_touch']}"
            assert math.isclose(wr, round(float(r['win_rate']), 4), abs_tol=1e-5), f"WR mismatch"
            assert math.isclose(sf_mean, round(float(r['gross_mean_r']), 4), abs_tol=1e-5), f"sf_mean mismatch"
            assert math.isclose(sf_sum, round(float(r['gross_sum_r']), 4), abs_tol=1e-5), f"sf_sum mismatch"
            assert math.isclose(tf_mean, round(float(r['tf_gross_mean_r']), 4), abs_tol=1e-5), f"tf_mean mismatch"
            assert math.isclose(tf_sum, round(float(r['tf_gross_sum_r']), 4), abs_tol=1e-5), f"tf_sum mismatch"
            assert loyo == str(r['loyo_positive_years']), f"loyo mismatch"
            assert math.isclose(loyo_min_mean, round(float(r['loyo_min_mean_r']), 4), abs_tol=1e-5), f"loyo_min_mean mismatch"
            assert math.isclose(loyo_max_mean, round(float(r['loyo_max_mean_r']), 4), abs_tol=1e-5), f"loyo_max_mean mismatch"
            assert math.isclose(loyo_min_sum, round(float(r['loyo_min_sum_r']), 4), abs_tol=1e-5), f"loyo_min_sum mismatch"
            assert math.isclose(loyo_max_sum, round(float(r['loyo_max_sum_r']), 4), abs_tol=1e-5), f"loyo_max_sum mismatch"
            assert math.isclose(tp_bar_med, float(r['tp_bars_median']), abs_tol=1e-5), f"tp_bar_med mismatch"
            assert math.isclose(sl_bar_med, float(r['sl_bars_median']), abs_tol=1e-5), f"sl_bar_med mismatch"
            assert math.isclose(all_bar_med, float(r['overall_bars_median']), abs_tol=1e-5), f"all_bar_med mismatch"
            
            total_cells_checked += 1

    print(f"PASSED: Reconciled {total_cells_checked:,} of 29,952 cells with 100% exactness!")
    print(f"Verified fractional target count: {fractional_targets_count:,} fractional target cells preserved (non-integer).")
    assert fractional_targets_count == 20736, f"Expected exactly 20,736 fractional cells, got {fractional_targets_count}"

    # 4. Verify Annual Breakdown
    print("\n--- Verifying Annual Breakdown ---")
    df_ann = pd.read_csv(ann_csv_path)
    print(f"Loaded annual CSV: {len(df_ann):,} rows")
    payload_annual = embedded_obj['annual']
    annual_cells_checked = 0
    for (p, pair, comp, coh, h), group in df_ann.groupby(['panel', 'pair', 'comparison_id', 'cohort_filter', 'horizon_bars']):
        key = f"{p}|{pair}|{comp}|{coh}|{h}"
        assert key in payload_annual, f"Missing annual key: {key}"
        cell_dict = payload_annual[key]
        for cell, cgroup in group.groupby('cell_label'):
            assert str(cell) in cell_dict, f"Missing cell in annual {key}: {cell}"
            rows = cell_dict[str(cell)]
            assert len(rows) == len(cgroup), f"Annual rows count mismatch: {len(rows)} vs {len(cgroup)}"
            for idx, (_, r) in enumerate(cgroup.iterrows()):
                ar = rows[idx]
                assert ar[0] == int(r['year'])
                assert ar[1] == int(r['N_bundles'])
                assert ar[2] == int(r['N_trades'])
                assert ar[3] == int(r['N_wins'])
                assert ar[4] == int(r['N_losses'])
                assert ar[5] == int(r['N_timeouts'])
                assert math.isclose(ar[6], round(float(r['gross_sum_r']), 4), abs_tol=1e-5)
                annual_cells_checked += 1
    print(f"PASSED: Reconciled {annual_cells_checked:,} annual breakdown rows with 100% exactness!")

    # 5. Explicitly sample fractional cells: 1:1.25, 2:2.75, 4:3.5
    print("\n--- Explicit Sampling of Fractional Cells ---")
    sample_key = "FULL_PANEL|ALL_PAIRS_COMBINED|CANDIDATE_1_HEADLINE_MM|ALL_ELIGIBLE|60"
    assert sample_key in payload_summaries, f"Key {sample_key} not in summaries"
    sample_cells = payload_summaries[sample_key]
    
    samples_to_find = {
        '1:1.25': (1, 1.25),
        '2:2.75': (2, 2.75),
        '4:3.5': (4, 3.5),
    }
    
    for label, (exp_stop, exp_target) in samples_to_find.items():
        found = [c for c in sample_cells if c[2] == label]
        assert len(found) == 1, f"Expected 1 cell for {label}, got {len(found)}"
        c = found[0]
        print(f"Sample [{label}]:")
        print(f"  stop_atr: {c[0]} (expected {exp_stop})")
        print(f"  target_atr: {c[1]} (expected {exp_target})")
        print(f"  reward_risk: {c[3]}")
        print(f"  N_bundles: {c[4]}, N_trades: {c[5]}, Wins: {c[6]}, Losses: {c[7]}, Timeouts: {c[8]}")
        print(f"  Win Rate: {c[10]:.4f}, Gross Mean R: {c[11]:.4f}, Gross Sum R: {c[12]:.4f}")
        print(f"  LOYO positive: {c[15]}, LOYO sum range: [{c[18]:.4f} .. {c[19]:.4f}]")
        assert c[0] == exp_stop
        assert c[1] == exp_target

    print("\n=== ALL FORENSIC VERIFICATIONS PASSED SUCCESSFULLY ===")

if __name__ == '__main__':
    run_verification()
