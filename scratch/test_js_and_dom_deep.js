const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

console.log('=== RUNNING JS SYNTAX & DOM DEEP VERIFICATION ===');

const html = fs.readFileSync('HTML Viewer/table_viewer.html', 'utf8');

// 1. Check embedded JSON blocks
const viewerDataMatch = html.match(/<script type="application\/json" id="viewer-data">([\s\S]*?)<\/script>/);
assert.ok(viewerDataMatch, 'viewer-data script block must exist');
const viewerData = JSON.parse(viewerDataMatch[1]);
assert.equal(viewerData.schema, 1, 'viewer-data schema must be 1');
assert.ok(viewerData.families.CPI, 'CPI family in viewer-data must exist');
assert.ok(viewerData.families.NFP, 'NFP family in viewer-data must exist');
console.log('PASSED: viewer-data JSON successfully parsed (CPI & NFP families present).');

const cpiBundleMatch = html.match(/<script type="application\/json" id="cpi-bundle-data">([\s\S]*?)<\/script>/);
assert.ok(cpiBundleMatch, 'cpi-bundle-data script block must exist');
const cpiBundle = JSON.parse(cpiBundleMatch[1]);
assert.equal(cpiBundle.version, 'USD_CPI_BUNDLE_V1_OUTCOMES_V3', 'version mismatch');
assert.equal(cpiBundle.run, 'run_20260930_outcomes_v3', 'run mismatch');
assert.equal(cpiBundle.selection_policy, 'NONE', 'selection_policy must be NONE');
console.log('PASSED: cpi-bundle-data JSON successfully parsed.');

// 2. Extract and check JS syntax of the main script tag
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 3, `Expected exactly 3 script tags in HTML, found ${scripts.length}`);
const mainJsCode = scripts[2][1];

// Compile to test syntax
const scriptObj = new vm.Script(mainJsCode, { filename: 'table_viewer_inline.js' });
console.log('PASSED: Inline JavaScript parsed and compiled cleanly with zero syntax errors.');

// 3. Mock DOM environment for complete execution
class Element {
  constructor(tag = 'div', value = '') {
    this.tag = tag;
    this.value = value;
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this._textContent = '';
    this._innerHTML = '';
    this.style = {};
    this.classList = {
      _classes: new Set(),
      add(...cls) { cls.forEach(c => this._classes.add(c)); },
      remove(...cls) { cls.forEach(c => this._classes.delete(c)); },
      contains(c) { return this._classes.has(c); },
      toggle(c, force) {
        if (force !== undefined) {
          if (force) this.add(c); else this.remove(c);
        } else {
          if (this.contains(c)) this.remove(c); else this.add(c);
        }
      }
    };
  }
  get textContent() { return this._textContent; }
  set textContent(val) {
    this._textContent = val === null || val === undefined ? '' : String(val);
    this._innerHTML = this._textContent;
  }
  get innerHTML() { return this._innerHTML || this._textContent; }
  set innerHTML(val) {
    this._innerHTML = val === null || val === undefined ? '' : String(val);
    this._textContent = this._innerHTML.replace(/<[^>]*>/g, '');
  }
  appendChild(child) { this.children.push(child); return child; }
  append(...children) { children.forEach(child => this.appendChild(child)); }
  replaceChildren(...children) {
    this.children = children.flatMap(child => child.tag === 'fragment' ? child.children : [child]);
    if (this.tag === 'select' && this.children.length > 0 && !this.value) {
      this.value = this.children[0].value || '';
    }
  }
  setAttribute(k, v) { this[k] = v; }
  getAttribute(k) { return this[k]; }
  removeAttribute(k) { delete this[k]; }
  addEventListener(event, callback) { this.listeners[event] = callback; }
  dispatch(event) {
    const evt = { type: event, stopPropagation() {}, preventDefault() {} };
    this.listeners[event]?.(evt);
  }
  focus() {}
  scrollIntoView() {}
}

const idMap = new Map();
function getOrCreate(id, tag = 'div', value = '') {
  if (!idMap.has(id)) idMap.set(id, new Element(tag, value));
  return idMap.get(id);
}

// Prepopulate required IDs
getOrCreate('viewer-data').textContent = viewerDataMatch[1];
getOrCreate('cpi-bundle-data').textContent = cpiBundleMatch[1];

// Tab buttons
getOrCreate('tab-cpi-bundle', 'button');
getOrCreate('tab-candidates', 'button');
getOrCreate('tab-events', 'button');
getOrCreate('tab-guide', 'button');

// Panels
getOrCreate('panel-cpi-bundle');
getOrCreate('panel-candidates');
getOrCreate('panel-events');
getOrCreate('panel-guide');

// Selectors for Candidates
getOrCreate('event-family', 'select', 'CPI');
getOrCreate('candidate-event', 'select', 'CPI');
getOrCreate('candidate-pair', 'select', 'EURUSD');
getOrCreate('candidate-signal', 'select', 'af');
getOrCreate('candidate-panel', 'select', 'PRIMARY_PANEL');
getOrCreate('candidate-cohort', 'select', 'ALL_ELIGIBLE');
getOrCreate('candidate-horizon', 'select', '60');
getOrCreate('result-tables');
getOrCreate('inspector-body');
getOrCreate('inspector-title');
getOrCreate('inspector-context');
getOrCreate('event-head');
getOrCreate('event-rows');
getOrCreate('event-count');
getOrCreate('event-year', 'select', 'all');

// Selectors for Bundle
getOrCreate('bundle-comparison', 'select', 'CANDIDATE_1_HEADLINE_MM');
getOrCreate('bundle-pair', 'select', 'ALL_PAIRS_COMBINED');
getOrCreate('bundle-panel', 'select', 'FULL_PANEL');
getOrCreate('bundle-horizon', 'select', '60');
getOrCreate('bundle-cohort', 'select', 'ALL_ELIGIBLE');
getOrCreate('bundle-count');
getOrCreate('bundle-grid-table', 'table');
getOrCreate('bundle-grid-thead-row');
getOrCreate('bundle-grid-tbody');
getOrCreate('bundle-inspector-panel');
getOrCreate('bundle-inspector-title');
getOrCreate('bundle-inspector-context');
getOrCreate('bundle-inspector-metrics');
getOrCreate('bundle-annual-table', 'table');
getOrCreate('bundle-annual-tbody');

const mockDoc = {
  getElementById: id => getOrCreate(id),
  createElement: tag => new Element(tag),
  createDocumentFragment: () => new Element('fragment'),
  querySelectorAll: sel => [],
};

// Run runtime script in context
const ctx = {
  document: mockDoc,
  console: console,
  setTimeout: () => {},
  clearTimeout: () => {},
};

vm.createContext(ctx);
scriptObj.runInContext(ctx);
console.log('PASSED: Viewer initialized in virtual DOM context.');

// 4. Verify Bundle Grid Rendering & Sorting
const tbody = getOrCreate('bundle-grid-tbody');
assert.equal(tbody.children.length, 52, `Expected 52 rows in bundle grid, got ${tbody.children.length}`);

// Test finding fractional rows
const row125 = tbody.children.find(r => r.children[0].textContent === '1' && r.children[1].textContent === '1.25');
assert.ok(row125, 'Row 1:1.25 must be present in bundle grid');
assert.equal(row125.children[0].textContent, '1', 'SL ATR must be 1');
assert.equal(row125.children[1].textContent, '1.25', 'TP ATR must be 1.25');
assert.equal(row125.children[2].textContent, '1.25', 'R:R must be 1.25');

const row275 = tbody.children.find(r => r.children[0].textContent === '2' && r.children[1].textContent === '2.75');
assert.ok(row275, 'Row 2:2.75 must be present in bundle grid');
assert.equal(row275.children[0].textContent, '2', 'SL ATR must be 2');
assert.equal(row275.children[1].textContent, '2.75', 'TP ATR must be 2.75');
assert.equal(row275.children[2].textContent, '1.375', 'R:R must be 1.375');

const row350 = tbody.children.find(r => r.children[0].textContent === '4' && r.children[1].textContent === '3.5');
assert.ok(row350, 'Row 4:3.5 must be present in bundle grid');
assert.equal(row350.children[0].textContent, '4', 'SL ATR must be 4');
assert.equal(row350.children[1].textContent, '3.5', 'TP ATR must be 3.5');
assert.equal(row350.children[2].textContent, '0.875', 'R:R must be 0.875');
console.log('PASSED: Verified fractional cell rows 1:1.25, 2:2.75, and 4:3.5 render exact multipliers and R:R.');

// Test clicking inspector on 1:1.25
row125.children.at(-1).children[0].dispatch('click');
const panel = getOrCreate('bundle-inspector-panel');
assert.equal(panel.style.display, 'block', 'Inspector panel must become visible');
assert.ok(getOrCreate('bundle-inspector-title').textContent.includes('TP 1.25 ATR'), 'Inspector title must include TP 1.25 ATR');
assert.ok(getOrCreate('bundle-inspector-title').textContent.includes('1:1.25'), 'Inspector title must include 1:1.25');

// Test annual breakdown rows in inspector
const annualTbody = getOrCreate('bundle-annual-tbody');
assert.ok(annualTbody.children.length >= 12, 'Annual table must contain at least 12 rows (2015-2026 + Total)');
const totalRow = annualTbody.children.find(r => r.children[0].textContent.includes('TOTAL'));
assert.ok(totalRow, 'TOTAL row must be present in annual table');
console.log(`PASSED: Detail inspector displays TP 1.25 ATR and ${annualTbody.children.length} annual rows with TOTAL summary.`);

// Test Sorting: sort by TP ATR (col index 1)
const theadRow = getOrCreate('bundle-grid-thead-row');
const tpColHeaderBtn = theadRow.children[1].children[0]; // TP ATR sort button
tpColHeaderBtn.dispatch('click'); // Sort asc
let sortedRows = tbody.children;
let firstTp = parseFloat(sortedRows[0].children[1].textContent);
let lastTp = parseFloat(sortedRows.at(-1).children[1].textContent);
assert.ok(firstTp <= lastTp, `Ascending TP sort failed: ${firstTp} vs ${lastTp}`);

tpColHeaderBtn.dispatch('click'); // Sort desc
sortedRows = tbody.children;
firstTp = parseFloat(sortedRows[0].children[1].textContent);
lastTp = parseFloat(sortedRows.at(-1).children[1].textContent);
assert.ok(firstTp >= lastTp, `Descending TP sort failed: ${firstTp} vs ${lastTp}`);
console.log(`PASSED: Numeric sorting by TP ATR works ascending (${firstTp}) and descending (${lastTp}).`);

// Test LOYO sorting (col index 14)
const loyoColHeaderBtn = theadRow.children[14].children[0];
loyoColHeaderBtn.dispatch('click');
sortedRows = tbody.children;
console.log('PASSED: LOYO column sorting executed without error.');

// 5. Verify Original Candidate & Event Views Are Preserved
getOrCreate('tab-candidates').dispatch('click');
assert.equal(getOrCreate('panel-candidates').hidden, false);
getOrCreate('tab-events').dispatch('click');
assert.equal(getOrCreate('panel-events').hidden, false);
assert.ok(getOrCreate('event-rows').children.length > 0, 'Event table rows must be populated');
console.log(`PASSED: Original Candidate and Event views preserved and operational with ${getOrCreate('event-rows').children.length} event rows.`);

console.log('=== ALL JS SYNTAX & DOM DEEP VERIFICATIONS PASSED ===');
