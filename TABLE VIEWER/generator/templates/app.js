  // Embedded dataset
  const DB = __DATA_JSON__;

  let viewingMode = 'BASE'; // 'BASE' or 'QUOTE'
  let medianPopulation = 'COMPLETE_AFP'; // 'COMPLETE_AFP' or 'ALL_PRICED'

  // DOM Elements
  const selPair = document.getElementById('selPair');
  const selYear = document.getElementById('selYear');
  const selFamily = document.getElementById('selFamily');
  const selCpiResponse = document.getElementById('selCpiResponse');
  const cpiSelectorInfo = document.getElementById('cpiSelectorInfo');
  const selEpisode = document.getElementById('selEpisode');
  const selMedianPop = document.getElementById('selMedianPop');
  const btnReset = document.getElementById('btnReset');
  const btnModeBase = document.getElementById('btnModeBase');
  const btnModeQuote = document.getElementById('btnModeQuote');
  const subTitleText = document.getElementById('subTitleText');

  const statusBanner = document.getElementById('statusBanner');
  const badgePair = document.getElementById('badgePair');
  const badgeFamily = document.getElementById('badgeFamily');
  const badgeYear = document.getElementById('badgeYear');
  const badgeCalendarN = document.getElementById('badgeCalendarN');
  const badgeCompleteAfpN = document.getElementById('badgeCompleteAfpN');
  const badgePricedN = document.getElementById('badgePricedN');
  const badgeCpiCondition = document.getElementById('badgeCpiCondition');
  const badgeCpiSharedExcl = document.getElementById('badgeCpiSharedExcl');
  const badgeSmallNSample = document.getElementById('badgeSmallNSample');
  const legendGreenText = document.getElementById('legendGreenText');
  const legendRedText = document.getElementById('legendRedText');

  const emptyState = document.getElementById('emptyState');
  const tableContainer = document.getElementById('tableContainer');
  const dataTable = document.getElementById('dataTable');
  const tableBody = document.getElementById('tableBody');
  const tableFoot = document.getElementById('tableFoot');
  const cpiMethodologyNote = document.getElementById('cpiMethodologyNote');
  const cpiMethodologyText = document.getElementById('cpiMethodologyText');
  const forwardTestSection = document.getElementById('forwardTestSection');
  const historicalCpiResultsSection = document.getElementById('historicalCpiResultsSection');

  // Tab & Candidate Research Elements
  const tabBtnEventTable = document.getElementById('tabBtnEventTable');
  const tabBtnCandidateResearch = document.getElementById('tabBtnCandidateResearch');
  const tabPanelEventTable = document.getElementById('tabPanelEventTable');
  const tabPanelCandidateResearch = document.getElementById('tabPanelCandidateResearch');
  const tabButtons = [tabBtnEventTable, tabBtnCandidateResearch];

  const selResearchStudy = document.getElementById('selResearchStudy');
  const studyContentCpiBaseline = document.getElementById('studyContentCpiBaseline');
  const studyContentCpiMomentum = document.getElementById('studyContentCpiMomentum');
  const studyContentPending = document.getElementById('studyContentPending');
  const pendingStudyTitle = document.getElementById('pendingStudyTitle');
  const pendingStudyDesc = document.getElementById('pendingStudyDesc');

  // Type-7 Linear Interpolation Percentile: pos = (n - 1) * p
  function computeType7Percentile(sortedVals, p) {
    const n = sortedVals.length;
    if (n === 0) return null;
    if (n === 1) return sortedVals[0];
    const pos = (n - 1) * p;
    const k = Math.floor(pos);
    const d = pos - k;
    if (k >= n - 1) return sortedVals[n - 1];
    return sortedVals[k] + d * (sortedVals[k + 1] - sortedVals[k]);
  }

  // Initialize Selectors
  function initSelectors() {
    // 1. Populate Pairs
    DB.pairs.forEach(p => {
      const meta = DB.pair_meta[p];
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = meta.desc;
      selPair.appendChild(opt);
    });

    // 2. Populate Event Families with Affected Pairs Note
    Object.keys(DB.families).forEach(k => {
      const fam = DB.families[k];
      const opt = document.createElement('option');
      opt.value = k;
      opt.textContent = fam.label + ' (' + fam.affected + ')';
      selFamily.appendChild(opt);
    });

    // 3. Build H1..H60 header th elements once
    const headerRow = dataTable.querySelector('thead tr');
    for (let h = 1; h <= 60; h++) {
      const th = document.createElement('th');
      th.className = 'pip-cell';
      th.textContent = 'H' + h;
      headerRow.appendChild(th);
    }
  }

  // Filter episodes based on selections
  function getFilteredEpisodes() {
    const pair = selPair.value;
    const year = selYear.value;
    const family = selFamily.value;
    const cpiResp = selCpiResponse ? selCpiResponse.value : 'ALL';

    if (!pair || !year || !family) return [];

    const isConditionedCpi = (pair === 'EURUSD' && family === 'US_INFLATION' && cpiResp && cpiResp !== 'ALL');

    return DB.episodes.filter(ep => {
      if (ep.family !== family) return false;
      if (year !== 'ALL' && ep.year !== parseInt(year, 10)) return false;
      if (isConditionedCpi) {
        if (ep.is_shared_timestamp) return false; // Exclude cross-family collisions
        if (ep.cpi_group !== cpiResp) return false; // Match conditioned group
      }
      return true;
    });
  }

  // Update Episode Selector options based on available filtered episodes
  function updateEpisodeSelector(filtered, pair) {
    selEpisode.innerHTML = '';
    if (!filtered || filtered.length === 0) {
      selEpisode.disabled = true;
      const opt = document.createElement('option');
      opt.value = 'ALL';
      opt.textContent = '0 Episodes Found';
      selEpisode.appendChild(opt);
      return;
    }

    selEpisode.disabled = false;
    const pricedCount = filtered.filter(ep => ep.pips && ep.pips[pair] !== null).length;

    const allOpt = document.createElement('option');
    allOpt.value = 'ALL';
    allOpt.textContent = 'All Episodes (Calendar N=' + filtered.length + ', Priced N=' + pricedCount + ')';
    selEpisode.appendChild(allOpt);

    filtered.forEach((ep, idx) => {
      const opt = document.createElement('option');
      opt.value = ep.ts;
      let label = (idx + 1) + '. ' + ep.dt_str;
      if (ep.indicators.length > 0) {
        const indNames = ep.indicators.map(i => i.name).join(', ');
        label += ' — ' + indNames;
      }
      if (!ep.pips || ep.pips[pair] === null) {
        label += ' [No Price Data]';
      }
      opt.textContent = label;
      selEpisode.appendChild(opt);
    });
  }

  // Compute signed pips based on BASE vs QUOTE mode
  // BASE mode: signed pips = (Hn close - entry open) / pip size = rawPip
  // QUOTE mode: signed pips = -(Hn close - entry open) / pip size = -rawPip
  function getSignedPips(rawPip, mode) {
    if (rawPip === null || rawPip === undefined) return null;
    return mode === 'BASE' ? rawPip : -rawPip;
  }

  // Render Table
  function render() {
    const pair = selPair.value;
    const year = selYear.value;
    const family = selFamily.value;

    // Check if all primary filters are selected
    if (!pair || !year || !family) {
      emptyState.style.display = 'block';
      statusBanner.style.display = 'none';
      tableContainer.style.display = 'none';
      selEpisode.disabled = true;
      selEpisode.innerHTML = '<option value="ALL">Select filters above first</option>';
      selCpiResponse.disabled = true;
      cpiSelectorInfo.style.display = 'none';
      cpiMethodologyNote.style.display = 'none';
      return;
    }

    // Enable CPI Response selector strictly for EURUSD & US_INFLATION
    const isCpiApplicable = (pair === 'EURUSD' && family === 'US_INFLATION');
    if (isCpiApplicable) {
      selCpiResponse.disabled = false;
    } else {
      selCpiResponse.disabled = true;
      selCpiResponse.value = 'ALL';
    }

    const cpiResp = selCpiResponse.value;
    const isConditionedCpi = (isCpiApplicable && cpiResp !== 'ALL');

    const filtered = getFilteredEpisodes();
    if (filtered.length === 0) {
      emptyState.style.display = 'block';
      emptyState.querySelector('h3').textContent = 'No Episodes Found';
      emptyState.querySelector('p').textContent = 'No macroeconomic releases were recorded for this combination in the pinned dataset.';
      statusBanner.style.display = 'none';
      tableContainer.style.display = 'none';
      selEpisode.disabled = true;
      selEpisode.innerHTML = '<option value="ALL">0 Episodes Found</option>';
      cpiMethodologyNote.style.display = 'none';
      return;
    }

    emptyState.style.display = 'none';
    statusBanner.style.display = 'flex';
    tableContainer.style.display = 'block';

    const meta = DB.pair_meta[pair];
    const calendarN = filtered.length;
    const completeAfpN = filtered.filter(ep => ep.is_complete_afp).length;
    const pricedN = filtered.filter(ep => ep.pips && ep.pips[pair] !== null).length;

    // Update Status Banner
    badgePair.textContent = 'Pair: ' + pair + ' (' + meta.base + '/' + meta.quote + ')';
    badgeFamily.textContent = 'Family: ' + DB.families[family].label;
    badgeYear.textContent = 'Year: ' + (year === 'ALL' ? '2015–2026' : year);
    badgeCalendarN.textContent = 'Calendar Episodes: ' + calendarN;
    badgeCompleteAfpN.textContent = 'Complete A/F/P: ' + completeAfpN;
    badgePricedN.textContent = 'Priced (' + pair + '): ' + pricedN;

    if (viewingMode === 'BASE') {
      subTitleText.textContent = 'H1–H60 Signed Pip Displacements (60 observed H1 candles) &bull; BASE Mode (' + meta.base + ' Strength / Price Up = Green)';
      legendGreenText.textContent = meta.base + ' Good / Up (+Pips)';
      legendRedText.textContent = meta.base + ' Bad / Down (-Pips)';
    } else {
      subTitleText.textContent = 'H1–H60 Signed Pip Displacements (60 observed H1 candles) &bull; QUOTE Mode (' + meta.quote + ' Strength / Price Down = Green)';
      legendGreenText.textContent = meta.quote + ' Good / Down (+Pips)';
      legendRedText.textContent = meta.quote + ' Bad / Up (-Pips)';
    }

    // Filter to selected single episode if specified
    const selectedEpTs = selEpisode.value;
    let episodesToRender = filtered;
    if (selectedEpTs && selectedEpTs !== 'ALL') {
      const single = filtered.filter(ep => ep.ts === parseInt(selectedEpTs, 10));
      if (single.length > 0) episodesToRender = single;
    }
    const isSingleEpisode = (episodesToRender.length === 1 && selectedEpTs && selectedEpTs !== 'ALL');

    // Conditioned CPI UI Information
    if (isConditionedCpi) {
      let ruleText = '';
      let condLabel = '';
      if (cpiResp === 'BOTH_ABOVE') {
        ruleText = 'Headline & Core CPI present; unshared timestamp; both A−F > 0. (Excludes Core PCE)';
        condLabel = 'Both Above (A−F > 0)';
      } else if (cpiResp === 'BOTH_BELOW') {
        ruleText = 'Headline & Core CPI present; unshared timestamp; both A−F < 0. (Excludes Core PCE)';
        condLabel = 'Both Below (A−F < 0)';
      } else if (cpiResp === 'MIXED_ZERO') {
        ruleText = 'Headline & Core CPI present; unshared timestamp; neither above nor below holds. (Excludes Core PCE)';
        condLabel = 'Mixed / Zero';
      }

      const excludedSharedCount = DB.episodes.filter(ep => {
        if (ep.family !== 'US_INFLATION') return false;
        if (year !== 'ALL' && ep.year !== parseInt(year, 10)) return false;
        return ep.is_shared_timestamp;
      }).length;

      cpiSelectorInfo.style.display = 'block';
      cpiSelectorInfo.textContent = 'Rule: ' + ruleText + ' | Eligible N = ' + filtered.length + ' (Excluded ' + excludedSharedCount + ' shared)';

      badgeCpiCondition.style.display = 'inline-flex';
      badgeCpiCondition.textContent = 'Condition: ' + condLabel;

      badgeCpiSharedExcl.style.display = 'inline-flex';
      badgeCpiSharedExcl.textContent = 'Shared Collisions Excluded: ' + excludedSharedCount;

      if (isSingleEpisode) {
        badgeSmallNSample.style.display = 'inline-flex';
        badgeSmallNSample.textContent = 'Single Episode (N = 1)';
        cpiMethodologyNote.className = 'methodology-note small-n';
        cpiMethodologyText.innerHTML = '<strong>Single Episode Selected (N = 1):</strong> A single historical episode is currently displayed. Percentiles (P10, P50 median, P90) collapse to this single observed price path. When evaluating conditioned CPI subsets (N &lt; 10), descriptive sample percentiles have high sampling variability and do not represent confidence intervals or guaranteed trading bounds. The full 2015–2026 series is exploratory; later years are not an untouched holdout.';
      } else if (filtered.length < 10) {
        badgeSmallNSample.style.display = 'inline-flex';
        badgeSmallNSample.textContent = 'Caution: Small N = ' + filtered.length + ' (<10)';
        cpiMethodologyNote.className = 'methodology-note small-n';
        cpiMethodologyText.innerHTML = '<strong>Small Sample Caution:</strong> This conditioned CPI subset contains N = ' + filtered.length + ' (&lt;10) priced episodes. (When a single episode is selected, N is 1 and percentiles collapse to that episode). Descriptive sample percentiles (P10, P50 median, P90) have high sampling variability in small samples and do not represent confidence intervals or guaranteed trading bounds. The full 2015–2026 series is exploratory; later years are not an untouched holdout.';
      } else {
        badgeSmallNSample.style.display = 'none';
        cpiMethodologyNote.className = 'methodology-note';
        cpiMethodologyText.innerHTML = '<strong>Descriptive Methodology Note:</strong> P10, P50 (median), and P90 are empirical sample percentiles computed using Type-7 linear interpolation at position (N−1)×p. (When a single episode is selected, N is 1). They describe historical sample dispersion and do not represent confidence intervals or predictive trading bounds. The full 2015–2026 series is exploratory; later years are not an untouched holdout.';
      }
      cpiMethodologyNote.style.display = 'block';
    } else {
      cpiSelectorInfo.style.display = 'none';
      badgeCpiCondition.style.display = 'none';
      badgeCpiSharedExcl.style.display = 'none';
      badgeSmallNSample.style.display = 'none';
      cpiMethodologyNote.style.display = 'none';
    }

    // Clear Body
    tableBody.innerHTML = '';

    // Collect horizon values for summary calculation across qualifying episodes
    const horizonValues = Array.from({ length: 60 }, () => []);

    episodesToRender.forEach((ep, idx) => {
      const tr = document.createElement('tr');
      const hasPriceData = (ep.pips && ep.pips[pair] !== null);
      const rawPips = hasPriceData ? ep.pips[pair] : null;

      // Col 1: #
      const tdIdx = document.createElement('td');
      tdIdx.className = 'sticky-col-1';
      tdIdx.textContent = (idx + 1);
      tr.appendChild(tdIdx);

      // Col 2: Date / Time
      const tdDate = document.createElement('td');
      tdDate.className = 'sticky-col-2';
      tdDate.textContent = ep.dt_str;
      tr.appendChild(tdDate);

      // Col 3: Indicators (Stacked)
      const tdInd = document.createElement('td');
      tdInd.className = 'sticky-col-3';
      const indDiv = document.createElement('div');
      indDiv.className = 'stacked-row';
      ep.indicators.forEach(ind => {
        const line = document.createElement('div');
        line.className = 'stacked-line';
        line.textContent = ind.name;
        indDiv.appendChild(line);
      });
      tdInd.appendChild(indDiv);
      tr.appendChild(tdInd);

      // Columns 4-8: A, F, P, S, M (Stacked)
      ['actual', 'forecast', 'previous', 'surprise', 'momentum'].forEach((field, fIdx) => {
        const td = document.createElement('td');
        td.className = 'sticky-col-afpsm sticky-col-' + (fIdx + 4);
        const fDiv = document.createElement('div');
        fDiv.className = 'stacked-row';
        ep.indicators.forEach(ind => {
          const line = document.createElement('div');
          line.className = 'stacked-line';
          line.textContent = ind[field];
          if (field === 'surprise' && ind.raw_s !== null && ind.raw_s !== undefined) {
            if (ind.raw_s > 0) line.style.color = '#15803d';
            else if (ind.raw_s < 0) line.style.color = '#b91c1c';
          }
          fDiv.appendChild(line);
        });
        td.appendChild(fDiv);
        tr.appendChild(td);
      });

      // Horizons H1..H60
      for (let h = 0; h < 60; h++) {
        const tdH = document.createElement('td');
        tdH.className = 'pip-cell';

        if (rawPips && rawPips[h] !== null && rawPips[h] !== undefined) {
          const signedVal = getSignedPips(rawPips[h], viewingMode);

          // Check if this episode qualifies for median population (or conditioned view)
          if (isConditionedCpi || medianPopulation === 'ALL_PRICED' || (medianPopulation === 'COMPLETE_AFP' && ep.is_complete_afp)) {
            horizonValues[h].push(signedVal);
          }

          const signStr = signedVal > 0 ? '+' : '';
          tdH.textContent = signStr + signedVal.toFixed(1);

          if (signedVal > 0) tdH.className += ' cell-pos';
          else if (signedVal < 0) tdH.className += ' cell-neg';
          else tdH.className += ' cell-zero';

          tdH.title = 'H' + (h + 1) + ': ' + signStr + signedVal.toFixed(1) + ' pips (' + viewingMode + ' mode)';
        } else {
          tdH.className += ' cell-na';
          tdH.textContent = '--';
          tdH.title = 'H' + (h + 1) + ': No price data / post-cutoff';
        }
        tr.appendChild(tdH);
      }

      tableBody.appendChild(tr);
    });

    // Footer Rendering
    tableFoot.innerHTML = '';
    if (!isConditionedCpi) {
      // Single Median Row (Standard descriptive view)
      const trFoot = document.createElement('tr');
      trFoot.className = 'foot-single-median';

      const tdF1 = document.createElement('td');
      tdF1.className = 'sticky-col-1';
      tdF1.textContent = 'M';
      trFoot.appendChild(tdF1);

      const tdF2 = document.createElement('td');
      tdF2.className = 'sticky-col-2';
      tdF2.textContent = 'MEDIAN';
      trFoot.appendChild(tdF2);

      const tdF3 = document.createElement('td');
      tdF3.className = 'sticky-col-3';
      const qualifyingEpisodes = episodesToRender.filter(e => {
        const hasPrice = e.pips && e.pips[pair] !== null;
        if (!hasPrice) return false;
        if (medianPopulation === 'COMPLETE_AFP') return e.is_complete_afp;
        return true;
      });
      const footerPricedN = qualifyingEpisodes.length;

      if (medianPopulation === 'COMPLETE_AFP') {
        tdF3.textContent = 'Complete A/F/P only (Priced N=' + footerPricedN + ')';
      } else {
        tdF3.textContent = 'All priced releases (Priced N=' + footerPricedN + ')';
      }
      trFoot.appendChild(tdF3);

      for (let i = 4; i <= 8; i++) {
        const td = document.createElement('td');
        td.className = 'sticky-col-afpsm sticky-col-' + i;
        td.textContent = '--';
        trFoot.appendChild(td);
      }

      for (let h = 0; h < 60; h++) {
        const tdH = document.createElement('td');
        tdH.className = 'pip-cell';
        const vals = horizonValues[h];

        if (vals && vals.length > 0) {
          vals.sort((a, b) => a - b);
          const mid = Math.floor(vals.length / 2);
          const med = vals.length % 2 !== 0 ? vals[mid] : (vals[mid - 1] + vals[mid]) / 2;
          const signStr = med > 0 ? '+' : '';
          tdH.textContent = signStr + med.toFixed(1);

          if (med > 0) tdH.className += ' cell-pos';
          else if (med < 0) tdH.className += ' cell-neg';
          else tdH.className += ' cell-zero';

          tdH.title = 'Median H' + (h + 1) + ': ' + signStr + med.toFixed(1) + ' pips (N=' + vals.length + ')';
        } else {
          tdH.className += ' cell-na';
          tdH.textContent = '--';
          tdH.title = 'Median H' + (h + 1) + ': -- (N=0)';
        }
        trFoot.appendChild(tdH);
      }

      tableFoot.appendChild(trFoot);
    } else {
      // FIVE Conditioned CPI Summary Rows
      const rowConfigs = [
        { key: 'p10', label1: 'P10', label2: 'P10 PIPS', label3: 'P10 signed pips (Type-7)', cls: 'foot-cpi-p10' },
        { key: 'p50', label1: 'P50', label2: 'P50 (MEDIAN)', label3: 'P50 signed pips (median)', cls: 'foot-cpi-p50' },
        { key: 'p90', label1: 'P90', label2: 'P90 PIPS', label3: 'P90 signed pips (Type-7)', cls: 'foot-cpi-p90' },
        { key: 'pos', label1: 'POS%', label2: 'POSITIVE %', label3: 'Positive in selected BASE/QUOTE mode', cls: 'foot-cpi-pos' },
        { key: 'n', label1: 'N', label2: 'COUNT', label3: 'Available N', cls: 'foot-cpi-n' }
      ];

      const hMetrics = [];
      for (let h = 0; h < 60; h++) {
        const vals = horizonValues[h];
        const n = vals ? vals.length : 0;
        if (n === 0) {
          hMetrics.push({ n: 0, p10: null, p50: null, p90: null, posFreq: null });
        } else {
          const sorted = vals.slice().sort((a, b) => a - b);
          const p10 = computeType7Percentile(sorted, 0.10);
          const p50 = computeType7Percentile(sorted, 0.50);
          const p90 = computeType7Percentile(sorted, 0.90);
          const posCount = sorted.filter(v => v > 0).length;
          const posFreq = (posCount / n) * 100;
          hMetrics.push({ n: n, p10: p10, p50: p50, p90: p90, posFreq: posFreq, posCount: posCount });
        }
      }

      rowConfigs.forEach(rc => {
        const tr = document.createElement('tr');
        tr.className = rc.cls;

        const td1 = document.createElement('td');
        td1.className = 'sticky-col-1';
        td1.textContent = rc.label1;
        tr.appendChild(td1);

        const td2 = document.createElement('td');
        td2.className = 'sticky-col-2';
        td2.textContent = rc.label2;
        tr.appendChild(td2);

        const td3 = document.createElement('td');
        td3.className = 'sticky-col-3';
        td3.textContent = rc.label3;
        tr.appendChild(td3);

        for (let i = 4; i <= 8; i++) {
          const td = document.createElement('td');
          td.className = 'sticky-col-afpsm sticky-col-' + i;
          td.textContent = '--';
          tr.appendChild(td);
        }

        for (let h = 0; h < 60; h++) {
          const tdH = document.createElement('td');
          tdH.className = 'pip-cell';
          const m = hMetrics[h];

          if (rc.key === 'p10' || rc.key === 'p50' || rc.key === 'p90') {
            const val = m[rc.key];
            if (val !== null && val !== undefined) {
              const signStr = val > 0 ? '+' : '';
              tdH.textContent = signStr + val.toFixed(1);
              if (val > 0) tdH.className += ' cell-pos';
              else if (val < 0) tdH.className += ' cell-neg';
              else tdH.className += ' cell-zero';
              tdH.title = rc.label1 + ' H' + (h + 1) + ': ' + signStr + val.toFixed(1) + ' pips (N=' + m.n + ')';
            } else {
              tdH.className += ' cell-na';
              tdH.textContent = '--';
              tdH.title = rc.label1 + ' H' + (h + 1) + ': -- (N=0)';
            }
          } else if (rc.key === 'pos') {
            if (m.posFreq !== null && m.posFreq !== undefined) {
              tdH.textContent = m.posFreq.toFixed(1) + '%';
              if (m.posFreq > 50.0) tdH.className += ' cell-pos';
              else if (m.posFreq < 50.0) tdH.className += ' cell-neg';
              else tdH.className += ' cell-zero';
              tdH.title = 'Positive % H' + (h + 1) + ': ' + m.posFreq.toFixed(1) + '% (' + m.posCount + '/' + m.n + ' > 0 pips in ' + viewingMode + ' mode)';
            } else {
              tdH.className += ' cell-na';
              tdH.textContent = '--';
              tdH.title = 'Positive % H' + (h + 1) + ': -- (N=0)';
            }
          } else if (rc.key === 'n') {
            tdH.textContent = m.n.toString();
            tdH.title = 'Available N H' + (h + 1) + ': ' + m.n;
          }

          tr.appendChild(tdH);
        }

        tableFoot.appendChild(tr);
      });
    }
  }

  // Event Listeners
  selPair.addEventListener('change', () => {
    updateEpisodeSelector(getFilteredEpisodes(), selPair.value);
    render();
  });

  selYear.addEventListener('change', () => {
    updateEpisodeSelector(getFilteredEpisodes(), selPair.value);
    render();
  });

  selFamily.addEventListener('change', () => {
    updateEpisodeSelector(getFilteredEpisodes(), selPair.value);
    render();
  });

  selCpiResponse.addEventListener('change', () => {
    updateEpisodeSelector(getFilteredEpisodes(), selPair.value);
    render();
  });

  selEpisode.addEventListener('change', () => {
    render();
  });

  selMedianPop.addEventListener('change', () => {
    medianPopulation = selMedianPop.value;
    render();
  });

  btnModeBase.addEventListener('click', () => {
    viewingMode = 'BASE';
    btnModeBase.classList.add('active');
    btnModeQuote.classList.remove('active');
    render();
  });

  btnModeQuote.addEventListener('click', () => {
    viewingMode = 'QUOTE';
    btnModeQuote.classList.add('active');
    btnModeBase.classList.remove('active');
    render();
  });

  btnReset.addEventListener('click', () => {
    selPair.value = '';
    selYear.value = '';
    selFamily.value = '';
    selCpiResponse.value = 'ALL';
    selCpiResponse.disabled = true;
    selEpisode.value = 'ALL';
    selEpisode.disabled = true;
    selMedianPop.value = 'COMPLETE_AFP';
    medianPopulation = 'COMPLETE_AFP';
    viewingMode = 'BASE';
    btnModeBase.classList.add('active');
    btnModeQuote.classList.remove('active');
    render();
  });

  // Tab Switching Logic
  function switchTab(targetTab) {
    if (targetTab === 'eventTable') {
      tabBtnEventTable.classList.add('active');
      tabBtnEventTable.setAttribute('aria-selected', 'true');
      tabBtnEventTable.setAttribute('tabindex', '0');

      tabBtnCandidateResearch.classList.remove('active');
      tabBtnCandidateResearch.setAttribute('aria-selected', 'false');
      tabBtnCandidateResearch.setAttribute('tabindex', '-1');

      tabPanelEventTable.style.display = 'block';
      tabPanelCandidateResearch.style.display = 'none';
    } else if (targetTab === 'candidateResearch') {
      tabBtnCandidateResearch.classList.add('active');
      tabBtnCandidateResearch.setAttribute('aria-selected', 'true');
      tabBtnCandidateResearch.setAttribute('tabindex', '0');

      tabBtnEventTable.classList.remove('active');
      tabBtnEventTable.setAttribute('aria-selected', 'false');
      tabBtnEventTable.setAttribute('tabindex', '-1');

      tabPanelCandidateResearch.style.display = 'block';
      tabPanelEventTable.style.display = 'none';
    }
  }

  if (tabBtnEventTable && tabBtnCandidateResearch) {
    tabBtnEventTable.addEventListener('click', () => switchTab('eventTable'));
    tabBtnCandidateResearch.addEventListener('click', () => switchTab('candidateResearch'));

    tabButtons.forEach((btn, idx) => {
      btn.addEventListener('keydown', (e) => {
        let targetIdx = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          targetIdx = (idx + 1) % tabButtons.length;
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          targetIdx = (idx - 1 + tabButtons.length) % tabButtons.length;
        } else if (e.key === 'Home') {
          targetIdx = 0;
        } else if (e.key === 'End') {
          targetIdx = tabButtons.length - 1;
        }

        if (targetIdx !== null) {
          e.preventDefault();
          tabButtons[targetIdx].focus();
          switchTab(targetIdx === 0 ? 'eventTable' : 'candidateResearch');
        }
      });
    });
  }

  // Candidate Research Study Selector Logic
  function updateResearchStudy() {
    if (!selResearchStudy) return;
    const study = selResearchStudy.value;
    if (study === 'US_CPI_EURUSD_AF_H24' || study === 'US_CPI_EURUSD') {
      if (studyContentCpiBaseline) studyContentCpiBaseline.style.display = 'block';
      if (studyContentCpiMomentum) studyContentCpiMomentum.style.display = 'none';
      if (studyContentPending) studyContentPending.style.display = 'none';
    } else if (study === 'US_CPI_EURUSD_AP_H60') {
      if (studyContentCpiBaseline) studyContentCpiBaseline.style.display = 'none';
      if (studyContentCpiMomentum) studyContentCpiMomentum.style.display = 'block';
      if (studyContentPending) studyContentPending.style.display = 'none';
    } else {
      if (studyContentCpiBaseline) studyContentCpiBaseline.style.display = 'none';
      if (studyContentCpiMomentum) studyContentCpiMomentum.style.display = 'none';
      if (studyContentPending) {
        studyContentPending.style.display = 'block';
        const optText = selResearchStudy.options[selResearchStudy.selectedIndex].text;
        if (pendingStudyTitle) pendingStudyTitle.textContent = optText + ' — Pending Pre-Registration Audit';
        if (pendingStudyDesc) {
          pendingStudyDesc.textContent = 'No candidate parameter card or simulation ledger is available in this viewer for ' + optText + '. Zero setups are registered for demo forward testing. To inspect raw price paths, use the Event Table tab.';
        }
      }
    }
  }

  if (selResearchStudy) {
    selResearchStudy.addEventListener('change', updateResearchStudy);
  }

  // Initial Run
  initSelectors();
  render();
  updateResearchStudy();

