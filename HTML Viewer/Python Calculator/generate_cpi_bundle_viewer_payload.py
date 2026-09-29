import pandas as pd
import json
import time
import os

def generate_payload():
    t0 = time.time()
    sum_path = 'Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_outcomes_v3/summary_grid_results.csv'
    ann_path = 'Research Candidate/CPI/CPI_BUNDLE_V1/run_20260930_outcomes_v3/annual_breakdown.csv'

    print("Reading CSVs...")
    df_sum = pd.read_csv(sum_path)
    df_ann = pd.read_csv(ann_path)
    print(f"Read CSVs in {time.time()-t0:.2f}s")

    payload = {
        'version': 'USD_CPI_BUNDLE_V1_OUTCOMES_V3',
        'run': 'run_20260930_outcomes_v3',
        'selection_policy': 'NONE',
        'status': 'EXPLORATORY_UNREGISTERED',
        'summary_cols': [
            'stop', 'target', 'cell', 'rr', 'nb', 'nt', 'w', 'l', 't', 'dt',
            'wr', 'sf_mean', 'sf_sum', 'tf_mean', 'tf_sum', 'loyo',
            'loyo_min_mean', 'loyo_max_mean', 'loyo_min_sum', 'loyo_max_sum',
            'tp_bar_med', 'sl_bar_med', 'all_bar_med'
        ],
        'annual_cols': [
            'year', 'nb', 'nt', 'w', 'l', 't', 'sum_r'
        ],
        'summaries': {},
        'annual': {}
    }

    print("Processing summaries...")
    for (p, pair, comp, coh, h), group in df_sum.groupby(['panel', 'pair', 'comparison_id', 'cohort_filter', 'horizon_bars']):
        key = f"{p}|{pair}|{comp}|{coh}|{h}"
        cells = []
        for _, r in group.iterrows():
            cells.append([
                int(r['stop_atr']),
                int(r['target_atr']),
                str(r['cell_label']),
                str(r['reward_risk']),
                int(r['N_bundles']),
                int(r['N_trades']),
                int(r['N_wins']),
                int(r['N_losses']),
                int(r['N_timeouts']),
                int(r['N_dual_touch']),
                round(float(r['win_rate']), 4),
                round(float(r['gross_mean_r']), 4),
                round(float(r['gross_sum_r']), 2),
                round(float(r['tf_gross_mean_r']), 4),
                round(float(r['tf_gross_sum_r']), 2),
                str(r['loyo_positive_years']),
                round(float(r['loyo_min_mean_r']), 4),
                round(float(r['loyo_max_mean_r']), 4),
                round(float(r['loyo_min_sum_r']), 2),
                round(float(r['loyo_max_sum_r']), 2),
                float(r['tp_bars_median']),
                float(r['sl_bars_median']),
                float(r['overall_bars_median']),
            ])
        payload['summaries'][key] = cells

    print("Processing annual breakdown...")
    for (p, pair, comp, coh, h), group in df_ann.groupby(['panel', 'pair', 'comparison_id', 'cohort_filter', 'horizon_bars']):
        key = f"{p}|{pair}|{comp}|{coh}|{h}"
        cell_dict = {}
        for cell, cgroup in group.groupby('cell_label'):
            rows = []
            for _, r in cgroup.iterrows():
                rows.append([
                    int(r['year']),
                    int(r['N_bundles']),
                    int(r['N_trades']),
                    int(r['N_wins']),
                    int(r['N_losses']),
                    int(r['N_timeouts']),
                    round(float(r['gross_sum_r']), 2)
                ])
            cell_dict[str(cell)] = rows
        payload['annual'][key] = cell_dict

    out_file = 'HTML Viewer/cpi_bundle_viewer_payload.json'
    print(f"Writing {out_file}...")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, separators=(',', ':'))

    size = os.path.getsize(out_file)
    print(f"Done! Payload written to {out_file} ({size} bytes, {size / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    generate_payload()
