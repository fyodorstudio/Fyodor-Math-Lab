// Minimal no-browser DOM smoke test. This never controls a user's desktop.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.resolve(__dirname, '../../table_viewer.html'), 'utf8');
const data = html.match(/<script type="application\/json" id="viewer-data">([\s\S]*?)<\/script>/);
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
assert.ok(data && scripts.length === 2, 'Embedded evidence and viewer code must exist');

class Element {
  constructor(tag = 'div', value = '') {
    this.tag = tag;
    this.value = value;
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.textContent = '';
  }
  appendChild(child) { this.children.push(child); return child; }
  append(...children) { children.forEach(child => this.appendChild(child)); }
  replaceChildren(...children) {
    this.children = children.flatMap(child => child.tag === 'fragment' ? child.children : [child]);
    if (this.tag === 'select') this.value = this.children[0]?.value || '';
  }
  setAttribute() {}
  addEventListener(event, callback) { this.listeners[event] = callback; }
  dispatch(event) { this.listeners[event]?.({ type: event }); }
  focus() {}
}

const ids = new Map();
function get(id, tag = 'div', value = '') {
  if (!ids.has(id)) ids.set(id, new Element(tag, value));
  return ids.get(id);
}
get('viewer-data').textContent = data[1];
get('event-family', 'select', 'CPI');
get('candidate-event', 'select', 'CPI');
get('candidate-signal', 'select', 'af');
get('candidate-horizon', 'select', '60');
get('candidate-cohort', 'select', 'ALL_ELIGIBLE');
const document = {
  getElementById: id => get(id),
  createElement: tag => new Element(tag),
  createDocumentFragment: () => new Element('fragment'),
  querySelectorAll: () => [],
};
vm.runInNewContext(scripts.at(-1)[1], { document, console }, { timeout: 10000 });

function gridTable() {
  const card = get('result-tables').children[0];
  return card.children.find(child => child.tag === 'div' && child.className === 'grid-scroll').children[0];
}
function selectedCell() {
  const table = gridTable();
  const body = table.children.find(child => child.tag === 'tbody');
  assert.equal(body.children.length, 52);
  return body.children.find(row => row.children[0].textContent === '2.00' && row.children[1].textContent === '2.00');
}

assert.equal(get('event-head').children.length, 240);
assert.ok(get('event-rows').children.length > 0);
assert.equal(get('event-count').textContent.includes('EURUSD'), true);
let row = selectedCell();
assert.equal(row.children[4].textContent, '73');
assert.equal(row.children[5].textContent, '36');
assert.equal(row.children[9].textContent, '-0.013699');
assert.equal(row.children[15].textContent, '4/9');

get('candidate-event').value = 'NFP';
get('candidate-event').dispatch('change');
row = selectedCell();
assert.equal(row.children[4].textContent, '111');
assert.equal(row.children[5].textContent, '62');
assert.equal(row.children[9].textContent, '+0.117117');
assert.equal(row.children[15].textContent, '9/9');
get('candidate-signal').value = 'both';
get('candidate-signal').dispatch('change');
assert.equal(get('result-tables').children.length, 2);
get('candidate-cohort').value = 'COMMON_H240';
get('candidate-cohort').dispatch('change');
get('candidate-horizon').value = '240';
get('candidate-horizon').dispatch('change');
assert.equal(get('result-tables').children.length, 2);
get('event-family').value = 'NFP';
get('event-family').dispatch('change');
get('event-year').value = '2026';
get('event-year').dispatch('change');
assert.ok(get('event-count').textContent.includes('partial'));
assert.ok(get('event-rows').children.length > 0);
gridTable().children[0].children[0].children[9].children[0].dispatch('click');
let sortedRows = gridTable().children[1].children;
assert.ok(Number(sortedRows[0].children[9].textContent) >= Number(sortedRows.at(-1).children[9].textContent));
gridTable().children[0].children[0].children[9].children[0].dispatch('click');
sortedRows = gridTable().children[1].children;
assert.ok(Number(sortedRows[0].children[9].textContent) <= Number(sortedRows.at(-1).children[9].textContent));
get('result-tables').children[0].children[0].children.find(child => child.className === 'sort-reset').dispatch('click');
assert.equal(gridTable().children[1].children[0].children[0].textContent, '1.00');
assert.equal(gridTable().children[1].children[0].children[1].textContent, '1.00');
console.log('Viewer DOM smoke test passed: CPI/NFP selectors, 52-cell grids, H1 event rows');
