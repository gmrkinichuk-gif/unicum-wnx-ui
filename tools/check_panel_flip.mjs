// Pure AS3 animation formulas are extracted, never reimplemented here.
// Row lifecycle is a test fixture, not an execution of the Scaleform runtime.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';

const workspace = fileURLToPath(new URL('../', import.meta.url));
const output = path.join(workspace, 'build', 'checks', 'panel-flip');
fs.mkdirSync(output, { recursive: true });
const source = fs.readFileSync(new URL('../as3/src/unicum/PanelFlip.as', import.meta.url), 'utf8');
const duration = Number(source.match(/DURATION:Number\s*=\s*([\d.]+)/)?.[1]);
assert.equal(duration, 150, 'review animation duration if changed');
const formulas = {};
for (const name of ['step', 'scale', 'opacity']) {
  const match = source.match(new RegExp(`public static function ${name}\\(([\\s\\S]*?)\\) : \\w+\\s*\\{([\\s\\S]*?)\\n      \\}`));
  assert.ok(match, `missing actual pure AS3 method ${name}`);
  const parameters = match[1].replace(/:\w+/g, '');
  const body = match[2].replace(/(var\s+\w+):\w+/g, '$1');
  formulas[name] = { parameters, body };
}
const step = new Function('DURATION', `return function(${formulas.step.parameters}) {${formulas.step.body}}`)(duration);
const scale = new Function(formulas.scale.parameters, formulas.scale.body);
const opacity = new Function(formulas.opacity.parameters, formulas.opacity.body);

const modeSource = fs.readFileSync(new URL('../as3/src/unicum/PanelModes.as', import.meta.url), 'utf8');
const dumpOption = process.argv.indexOf('--client-dump');
if (dumpOption < 0 || !process.argv[dumpOption + 1]) {
  throw new Error('Pass --client-dump PATH to the matching client library dump; see docs/DEVELOPMENT.md');
}
const clientDump = fs.readFileSync(process.argv[dumpOption + 1], 'utf8');
const classStart = clientDump.indexOf('public class net.wg.data.constants.generated::PLAYERS_PANEL_STATE extends Object');
assert.ok(classStart >= 0, 'client panel constants class must exist');
const classEnd = clientDump.indexOf('\n}', classStart);
const constantClass = clientDump.slice(classStart, classEnd);
const modeConstants = {};
for (const [, name, value] of constantClass.matchAll(/public static const (\w+):int = (-?\d+)/g)) {
  if (/^(MEDIUM|LONG|FULL|SHORT)(_NO_BADGES)?$|^(HIDDEN|NONE)$/.test(name)) modeConstants[name] = Number(value);
}
const modeBody = modeSource.match(/public static function target\(row:Object\) : TextField\s*\{([\s\S]*?)\n      \}/)?.[1];
assert.ok(modeBody, 'actual PanelModes.target body must be present');
const nativeTarget = new Function('PLAYERS_PANEL_STATE', 'row',
  modeBody.replace(/int\(/g, 'Number(').replace(/ as TextField/g, '').replace(/catch\((\w+):\w+\)/g, 'catch($1)'));
const statisticsBody = modeSource.match(/public static function statistics\(row:Object, marker:Array\) : String\s*\{([\s\S]*?)\n      \}/)?.[1];
assert.ok(statisticsBody, 'actual PanelModes.statistics body must be present');
const statisticsJS = statisticsBody.replace(/int\(/g, 'Number(').replace(/(var\s+\w+):\w+/g, '$1').replace(/catch\((\w+):\w+\)/g, 'catch($1)');
const rosterOptions = {altStats: 0};
const nativeStatistics = new Function('RosterOptions', `return function(PLAYERS_PANEL_STATE,row,marker){${statisticsJS}}`)(rosterOptions);
function fixtureMarker(line) {
  const parts = line ? line.split(' | ') : [];
  const marker = [];
  marker[11] = parts[0] && parts[0] !== '\u2014' ? parts[0] : '';
  marker.statsLine = line;
  marker.hasStats = parts.some(value => value && value !== '\u2014');
  return marker;
}
function statisticsFor(row) { return nativeStatistics(modeConstants, { state: modeConstants[row.mode] }, fixtureMarker(row.stats)); }
const nativeKeys = { playerNameCutTF: 'nameCut', playerNameFullTF: 'nameFull', vehicleTF: 'vehicle' };
const modeRows = Object.fromEntries(Object.keys(nativeKeys).map(name => [name, name]));
const modes = {};
for (const name of ['MEDIUM', 'MEDIUM_NO_BADGES', 'LONG', 'LONG_NO_BADGES', 'FULL', 'FULL_NO_BADGES', 'SHORT', 'SHORT_NO_BADGES']) {
  assert.ok(Number.isFinite(modeConstants[name]), `client constant missing: ${name}`);
  modes[name] = nativeKeys[nativeTarget(modeConstants, { ...modeRows, state: modeConstants[name] })] || null;
}
assert.deepEqual(modes, {
  MEDIUM: 'nameCut', MEDIUM_NO_BADGES: 'nameCut', LONG: 'vehicle', LONG_NO_BADGES: 'vehicle',
  FULL: 'nameFull', FULL_NO_BADGES: 'nameFull', SHORT: null, SHORT_NO_BADGES: null,
});
for (const name of ['HIDDEN', 'NONE']) assert.equal(nativeTarget(modeConstants, { ...modeRows, state: modeConstants[name] }), null);
assert.equal(nativeTarget(modeConstants, { ...modeRows, state: 999 }), null, 'unsupported modes remain untouched');
assert.equal(nativeTarget(modeConstants, { get state() { throw new Error('unavailable native mode'); } }), null, 'unavailable native API must be handled');
let assertions = 0;
function check(value, message) { assert.ok(value, message); assertions++; }
function same(actual, expected, message) { assert.deepEqual(actual, expected, message); assertions++; }
for (const mode of ['MEDIUM', 'MEDIUM_NO_BADGES', 'LONG', 'LONG_NO_BADGES']) {
  same(nativeStatistics(modeConstants, { state: modeConstants[mode] }, fixtureMarker('2180 | 56% | 18.4k')), '2180', `${mode}: actual method shows WNX only`);
  same(nativeStatistics(modeConstants, { state: modeConstants[mode] }, fixtureMarker('\u2014 | 56% | 18.4k')), '\u2014', `${mode}: absent WNX is an em dash`);
  same(nativeStatistics(modeConstants, { state: modeConstants[mode] }, null), '\u2014', `${mode}: null marker uses an em dash`);
  same(nativeStatistics(modeConstants, { state: modeConstants[mode] }, fixtureMarker('0 | \u2014 | \u2014')), '0', `${mode}: a real zero rating is not confused with missing data`);
}
for (const mode of ['FULL', 'FULL_NO_BADGES']) {
  same(nativeStatistics(modeConstants, { state: modeConstants[mode] }, fixtureMarker('2180 | 56% | 18.4k')), '2180 | 56% | 18.4k', `${mode}: all three remain`);
  same(nativeStatistics(modeConstants, { state: modeConstants[mode] }, fixtureMarker('\u2014 | 56% | 18.4k')), '\u2014 | 56% | 18.4k', `${mode}: partial data retained`);
  same(nativeStatistics(modeConstants, { state: modeConstants[mode] }, fixtureMarker('')), '\u2014', `${mode}: no data uses an em dash`);
}
function rect(x, y, width, height = 22) { return { x, y, width, height }; }
function makeRows(mode) {
  return Array.from({ length: 30 }, (_, i) => {
    const ally = i < 15;
    const y = (i % 15) * 24;
    const base = ally ? 0 : 900;
    const suffix = i % 4 === 0 ? '_very_long_player_name_0123456789 [CLAN]' : `_${i} [TAG]`;
    const fields = {
      nameCut: { ...rect(base + (ally ? 0 : 124), y, 150), text: `Player${suffix}`, alpha: 1 },
      nameFull: { ...rect(base + (ally ? 0 : 124), y, 150), text: `Player${suffix}`, alpha: 1 },
      vehicle: { ...rect(base + (ally ? 152 : 0), y, 120), text: `Tank_${i}`, alpha: 1 },
    };
    return { id: i + 1, ally, mode, fields, icon: rect(base + (ally ? 274 : 278), y, 60),
      tier: rect(base + (ally ? 285 : 286), y, 12), stats: `${1800 + i} | 56% | 18.4k` };
  });
}

class Fixture {
  constructor(mode) {
    this.rows = makeRows(mode);
    this.states = new Map();
    this.allocations = 0;
    this.frees = 0;
    this.active = 0;
    this.focus = true;
    this.blocked = false;
  }
  request(alt) {
    if (!alt) this.blocked = false;
    alt = alt && this.focus && !this.blocked;
    for (const row of this.rows) {
      const field = row.fields[modes[row.mode]];
      let state = this.states.get(row.id);
      if (!field || !statisticsFor(row)) {
        if (state) this.release(state);
        continue;
      }
      if (!state) {
        if (!alt) continue;
        state = { field, savedAlpha: field.alpha, rect: rect(field.x, field.y, field.width, field.height),
          position: 0, target: 0, visible: false, text: field.text, scale: 1, alpha: 1 };
        this.states.set(row.id, state);
        this.allocations++;
      }
      if (state.field !== field) {
        this.release(state);
        state.field = field;
        state.savedAlpha = field.alpha;
        state.rect = rect(field.x, field.y, field.width, field.height);
      }
      state.target = alt ? 1 : 0;
    }
    this.count();
  }
  count() { this.active = [...this.states.values()].filter(s => s.position !== s.target).length; }
  tick(elapsed) {
    for (const row of this.rows) {
      const state = this.states.get(row.id);
      if (!state) continue;
      state.position = step(state.position, state.target, elapsed);
      state.scale = scale(state.position);
      state.alpha = opacity(state.position);
      state.text = state.position >= 0.5 ? statisticsFor(row) : state.field.text;
      state.visible = state.position > 0;
      state.field.alpha = state.visible ? 0 : state.savedAlpha;
    }
    this.count();
  }
  cancel() {
    for (const state of this.states.values()) this.release(state);
    this.count();
  }
  release(state) { state.field.alpha = state.savedAlpha; state.position = state.target = 0; state.visible = false; }
  deactivate() { this.focus = false; this.blocked = true; this.cancel(); }
  activate() { this.focus = true; this.blocked = true; }
  dispose() { this.cancel(); this.frees += this.states.size; this.states.clear(); }
}

same(step(0, 1, -10), 0, 'negative elapsed must not advance');
same(step(0, 1, duration), 1, 'forward settles at duration');
same(step(1, 0, duration), 0, 'reverse settles at duration');
same(scale(0), 1, 'normal endpoint full width');
same(scale(1), 1, 'statistics endpoint full width');
same(opacity(0.5), 0, 'midpoint is transparent');
same(scale(0.5), 0.04, 'midpoint keeps a nonzero transform');
for (let i = 0; i <= 100; i++) {
  const p = i / 100;
  check(scale(p) >= 0.04 && scale(p) <= 1, 'scale must stay bounded');
  check(opacity(p) >= 0 && opacity(p) <= 1, 'opacity must stay bounded');
  check(Math.abs(scale(p) - scale(1 - p)) < 1e-12, 'forward/reverse scale symmetry');
}

const cases = [];
for (const mode of Object.keys(modes)) {
  const fixture = new Fixture(mode);
  const before = structuredClone(fixture.rows);
  fixture.request(false);
  same(fixture.allocations, 0, `${mode}: untouched normal state allocates no overlay`);
  fixture.request(true);
  fixture.tick(duration);
  const selected = modes[mode] !== null;
  same(fixture.allocations, selected ? 30 : 0, `${mode}: one overlay per selected row`);
  same(fixture.active, 0, `${mode}: no active animation after settle`);
  for (const row of fixture.rows) {
    const state = fixture.states.get(row.id);
    same(row.icon, before[row.id - 1].icon, `${mode}: native icon rect stable`);
    same(row.tier, before[row.id - 1].tier, `${mode}: native tier rect stable`);
    for (const key of Object.keys(row.fields)) {
      const { alpha: alphaBefore, ...fieldBefore } = before[row.id - 1].fields[key];
      const { alpha: alphaAfter, ...fieldAfter } = row.fields[key];
      same(fieldAfter, fieldBefore, `${mode}: source text and rectangle preserved`);
      if (key !== modes[mode]) same(alphaAfter, alphaBefore, `${mode}: unrelated source remains visible`);
    }
    if (selected) {
      same(state.text, statisticsFor(row), `${mode}: exact actual mode-specific statistics`);
      same(state.rect, rect(state.field.x, state.field.y, state.field.width, state.field.height), `${mode}: clip inside source rectangle`);
      same(state.field.alpha, 0, `${mode}: source hidden only while overlay visible`);
    }
    if (mode.startsWith('FULL')) same(row.fields.vehicle, before[row.id - 1].fields.vehicle, `${mode}: vehicle remains intact`);
  }
  fixture.request(false);
  fixture.tick(duration);
  same(fixture.rows, before, `${mode}: normal state exactly restored`);
  for (let i = 0; i < 120; i++) {
    fixture.request(i % 2 === 0);
    const positions = [...fixture.states.values()].map(s => s.position);
    fixture.tick(7);
    [...fixture.states.values()].forEach((s, j) => {
      check(Math.abs(s.position - positions[j]) <= 7 / duration + 1e-12, `${mode}: fast reversal continuous`);
    });
  }
  same(fixture.allocations, selected ? 30 : 0, `${mode}: rapid Alt never allocates another overlay`);
  fixture.request(true);
  fixture.tick(40);
  fixture.deactivate();
  same(fixture.rows, before, `${mode}: focus loss restores source`);
  same(fixture.active, 0, `${mode}: focus loss cancels animation`);
  fixture.activate();
  fixture.request(true);
  fixture.tick(duration);
  same(fixture.rows, before, `${mode}: stale held Alt stays blocked after focus restoration`);
  fixture.request(false);
  fixture.request(true);
  fixture.tick(50);
  fixture.dispose();
  same(fixture.states.size, 0, `${mode}: mode switch/dispose removes states`);
  same(fixture.active, 0, `${mode}: no active transitions after dispose`);
  same(fixture.frees, fixture.allocations, `${mode}: owned overlay count returns to zero`);
  same(fixture.rows, before, `${mode}: disposal restores sources`);
  cases.push({ mode, rows: 30, overlaysCreated: fixture.allocations, overlaysRetained: fixture.states.size,
    rapidReversals: 120, activeAfterDispose: fixture.active });
}
const missing = new Fixture('FULL');
missing.rows.forEach(row => { row.stats = ''; });
missing.request(true);
missing.tick(duration);
same(missing.allocations, 30, 'all missing statistics use one reusable Alt placeholder per row');
for (const state of missing.states.values()) same(state.text, '\u2014', 'all missing statistics display one em dash');
missing.request(false);
missing.tick(duration);
same(missing.active, 0, 'unknown-statistics reverse settles');
for (const row of missing.rows) same(row.fields.nameFull.alpha, 1, 'release restores the original missing-statistics name');
missing.dispose();
same(missing.states.size, 0, 'unknown-statistics disposal removes overlays');
const partial = new Fixture('FULL');
partial.rows.forEach(row => { row.stats = '2180 | \u2014 | \u2014'; });
partial.request(true);
partial.tick(duration);
same(partial.allocations, 30, 'partial statistics allocate one reused overlay per row');
for (const state of partial.states.values()) same(state.text, '2180 | \u2014 | \u2014', 'missing members of partial statistics use dashes, never zero');
partial.dispose();
same(partial.active, 0, 'partial-statistics disposal cancels all transitions');
for (const mode of ['MEDIUM', 'LONG']) {
  const narrowUnknown = new Fixture(mode);
  narrowUnknown.rows.forEach(row => { row.stats = '\u2014 | 56% | 18.4k'; });
  const nativeBefore = structuredClone(narrowUnknown.rows);
  narrowUnknown.request(true);
  narrowUnknown.tick(duration);
  same(narrowUnknown.allocations, 30, `${mode}: absent WNX uses a reusable placeholder`);
  for (const state of narrowUnknown.states.values()) same(state.text, '\u2014', `${mode}: missing rating is an em dash`);
  narrowUnknown.dispose();
  same(narrowUnknown.rows, nativeBefore, `${mode}: release/disposal restores native name/vehicle text`);
}
const switched = new Fixture('FULL');
const switchBefore = structuredClone(switched.rows);
switched.request(true);
switched.tick(40);
switched.rows.forEach(row => { row.mode = 'LONG'; });
switched.request(true);
switched.tick(duration);
same(switched.allocations, 30, 'held FULL-to-LONG mode change reuses one overlay per row');
for (const row of switched.rows) {
  same(row.fields.nameFull, switchBefore[row.id - 1].fields.nameFull, 'mode switch restores old name source');
  same(row.fields.vehicle.alpha, 0, 'LONG statistics replace only vehicle source');
}
switched.rows.forEach(row => { row.mode = 'SHORT'; });
switched.request(true);
switched.tick(duration);
same(switched.active, 0, 'held SHORT mode has no active transition');
same(switched.allocations, 30, 'switch to SHORT creates no overlay');
for (const row of switched.rows) same(row.fields, switchBefore[row.id - 1].fields, 'SHORT leaves all native fields restored');
switched.dispose();
same(switched.states.size, 0, 'mode-switch disposal clears reused overlays');

// A representative fixture traversal, not the production Scaleform pipeline.
// Both workloads read the same 30 rows; elapsed times use actual Node CPU wall
// time. Simulated frame timestamps only determine discovery cadence.
const timingRows = makeRows('FULL');
let checksum = 0;
function discover() {
  const list = timingRows.map(row => ({ id: row.id, y: row.icon.y, x: row.icon.x,
    text: row.fields.nameFull.text, width: row.fields.nameFull.width }));
  list.sort((a, b) => a.y - b.y || a.id - b.id);
  for (const row of list) checksum += row.id + row.width + row.text.length;
}
const frames = 6000;
function timeWork(throttled, animation = false) {
  let visits = 0, last = -Infinity, p = 0;
  const start = performance.now();
  for (let frame = 0; frame < frames; frame++) {
    const now = frame * (1000 / 60);
    if (!throttled || now - last >= 50) {
      discover(); last = now; visits += timingRows.length;
    }
    if (animation) {
      const target = Math.floor(frame / 20) % 2;
      p = step(p, target, 1000 / 60);
      for (let i = 0; i < 30; i++) checksum += scale(p) + opacity(p);
    }
  }
  return { elapsedMs: performance.now() - start, rowVisits: visits };
}
timeWork(false); timeWork(true); timeWork(true, true);
const median = values => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
const oldSamples = [], newSamples = [], animationSamples = [];
for (let i = 0; i < 9; i++) {
  oldSamples.push(timeWork(false));
  newSamples.push(timeWork(true));
  animationSamples.push(timeWork(true, true));
}
const oldMs = median(oldSamples.map(s => s.elapsedMs));
const newMs = median(newSamples.map(s => s.elapsedMs));
const animationMs = median(animationSamples.map(s => s.elapsedMs));
check(Number.isFinite(checksum) && checksum > 0, 'timing work must remain observable');
const timings = { environment: `Node ${process.version} ${process.platform} ${process.arch}`,
  clock: 'node:perf_hooks performance.now, actual elapsed milliseconds', frames, rows: 30, samples: 9,
  baselineDiscoveryMs: oldMs, throttledDiscoveryMs: newMs, throttledWithFormulaAnimationMs: animationMs,
  ratioThrottledToBaseline: newMs / oldMs,
  baselineRowVisits: oldSamples[0].rowVisits, throttledRowVisits: newSamples[0].rowVisits,
  limitation: 'Representative plain-object fixture only; not DOM, Scaleform, client CPU or FPS measurements. Browser preview is a separate visual check.' };

const swapFile = new URL('../as3/src/unicum/PanelTextSwap.as', import.meta.url);
const swapSource = fs.existsSync(swapFile) ? fs.readFileSync(swapFile, 'utf8') : '';
check(Boolean(swapSource), 'actual lifecycle class must exist');
const sourceContracts = {
  oneTextFieldCreationSite: (swapSource.match(/new TextField\(/g) || []).length === 1,
  oneSpriteCreationSite: (swapSource.match(/new Sprite\(/g) || []).length === 1,
  lazyOnAlt: /if\(!this\._held\) return;/.test(swapSource),
  lazyExistingRow: /if\(state == null\)[\s\S]*?new Sprite\(/.test(swapSource),
  passiveOverlay: /clip\.mouseEnabled = false;[\s\S]*?clip\.mouseChildren = false;[\s\S]*?text\.mouseEnabled = false;/.test(swapSource),
  boundedClip: /state\.clip\.scrollRect = new Rectangle\(0,0,tf\.width,tf\.height\)/.test(swapSource),
  tickOnlyActive: /public function tick\(now:int\)[\s\S]*?for\(var key:Object in this\._active\)/.test(swapSource),
  restoreAlphaAndOwner: /state\.source\.alpha = state\.alpha;[\s\S]*?delete _owners\[state\.source\];/.test(swapSource),
  detachPruned: /row\.stage == null\)[\s\S]*?release\(state\);[\s\S]*?delete this\._rows\[key\];/.test(swapSource),
  focusCancel: /this\._focus = false;[\s\S]*?this\._blocked = true;[\s\S]*?this\.cancel\(\);/.test(swapSource),
  staleAltBlocked: /if\(!held\) this\._blocked = false;[\s\S]*?held && this\._focus && !this\._blocked/.test(swapSource),
  disposeRestores: /public function dispose\(\)[\s\S]*?this\.cancel\(\);/.test(swapSource),
  removesFocusListeners: /removeEventListener\(Event\.DEACTIVATE[\s\S]*?removeEventListener\(Event\.ACTIVATE/.test(swapSource),
};
for (const [name, passed] of Object.entries(sourceContracts)) check(passed, `actual PanelTextSwap source contract: ${name}`);
const binding = { formulaSource: 'as3/src/unicum/PanelFlip.as', duration,
  lifecycle: 'Fixture simulation; does not execute Flash display objects or prove native Scaleform behavior.',
  panelTextSwapPresent: Boolean(swapSource),
  modeSelectorSource: 'as3/src/unicum/PanelModes.as actual target method body',
  statisticsSource: 'as3/src/unicum/PanelModes.as actual statistics method body',
  modeConstantsSource: 'externally supplied client-library dump', mapping: modes, modeConstants,
  sourceContracts,
};
const report = { result: 'PASS', assertions, cases, sourceBinding: binding, timings };
fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(report, null, 2) + '\n');

const jsFunctions = Object.entries(formulas).map(([name, { parameters, body }]) => `function ${name}(${parameters}) {${body}}`).join('\n');
const html = `<!doctype html><meta charset="utf-8"><title>Unicum 0.9.9 PanelFlip preview</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:24px;font:15px system-ui;color:#e6e8ed;background:#10151f}h1{font-size:23px;margin:0 0 12px}p{max-width:1100px;color:#b6bfcb}button,select{font:inherit;padding:8px 12px;background:#263145;color:white;border:1px solid #48566c;border-radius:4px}.controls{display:flex;gap:12px;align-items:center;margin:18px 0}#teams{display:flex;justify-content:space-between;gap:30px}.team{width:650px}.row{height:34px;position:relative;background:#1e2835;border-left:3px solid var(--wnx);margin-bottom:3px}.enemy{border-left:0;border-right:3px solid var(--wnx)}.cell{position:absolute;height:28px;top:3px;line-height:28px;white-space:nowrap;overflow:hidden;color:#f2f3f5}.name{left:8px;width:280px}.vehicle{left:292px;width:190px}.icon{position:absolute;right:8px;top:6px;width:70px;height:22px;background:linear-gradient(12deg,#617084,#b4becb);clip-path:polygon(0 30%,40% 30%,45% 5%,90% 10%,95% 50%,100% 65%,90% 90%,10% 90%)}.tier{position:absolute;right:85px;top:9px;font-size:12px;color:#e9edf2}.enemy .name{left:auto;right:8px;text-align:right}.enemy .vehicle{left:auto;right:292px;text-align:right}.enemy .icon{left:8px;right:auto;transform:scaleX(-1)}.enemy .tier{left:85px;right:auto}.clip{position:absolute;inset:0;overflow:hidden;pointer-events:none}.overlay{position:absolute;inset:0;transform-origin:center;white-space:nowrap;overflow:hidden}.native{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.medium .vehicle,.long .name,.short .name,.short .vehicle{display:none}.medium .name,.long .vehicle{width:420px}.long .vehicle{left:8px}.long .enemy .vehicle{left:auto;right:8px}.short .row{background:#1e2835}.status{font-family:monospace;margin-top:12px;color:#9fd4ab}#notice{color:#f2c97d}kbd{border:1px solid #617084;padding:2px 5px}
</style>
<h1>Unicum.gg 0.9.11 — local animation fixture</h1>
<p id="notice">Browser preview only. Native WoT/Scaleform and icons are not executed here. Actual easing bodies come from PanelFlip.as. The gray tank silhouette and sample colors are fixture markers, not game resources or a replacement WNX scale.</p>
<div class="controls"><select id="mode"><option>FULL</option><option>MEDIUM</option><option>LONG</option><option>SHORT</option></select><button id="toggle">Hold Alt / toggle statistics</button><button id="cancel">Cancel / focus loss</button><label><input id="freeze" type="checkbox"> Freeze at midpoint</label></div>
<div id="teams"></div><div class="status" id="status"></div>
<script>
const DURATION=${duration};
${jsFunctions}
const PLAYERS_PANEL_STATE=${JSON.stringify(modeConstants)};
function statistics(row,marker){${statisticsJS}}
${fixtureMarker.toString()}
const teams=document.querySelector('#teams'), status=document.querySelector('#status');
const modes=${JSON.stringify(modes)};
const sourceRows=${JSON.stringify(makeRows('FULL'))};
const colors=['#cc4a52','#c5793f','#d4b941','#70ac52','#4698b7','#8268b8'];
const query=new URLSearchParams(location.search);
let mode=['FULL','MEDIUM','LONG','SHORT'].includes(query.get('mode'))?query.get('mode'):'FULL',target=0,last=0;
document.querySelector('#mode').value=mode;
document.querySelector('#freeze').checked=query.get('half')==='1';
const states=[];let nativeRects=[],geometryPassed=true;
for(let side=0;side<2;side++){
 const team=document.createElement('div');team.className='team';teams.append(team);
 for(let i=0;i<15;i++){
  const data=sourceRows[side*15+i], row=document.createElement('div');row.className='row'+(side?' enemy':'');row.style.setProperty('--wnx',colors[i%6]);
  row.innerHTML='<div class="cell name"><span class="native"></span><div class="clip"><div class="overlay"></div></div></div><div class="cell vehicle"><span class="native"></span><div class="clip"><div class="overlay"></div></div></div><span class="tier">X</span><div class="icon"></div>';
  row.querySelector('.name .native').textContent=data.fields.nameFull.text;row.querySelector('.vehicle .native').textContent=data.fields.vehicle.text;
  team.append(row); states.push({row,data,p:0,target:0,selected:null});
 }
}
function select(){
 teams.className=mode.toLowerCase();
 for(const state of states){
  for(const cell of state.row.querySelectorAll('.cell')) {cell.querySelector('.native').style.opacity=1;cell.querySelector('.clip').hidden=true;}
  state.p=0;state.target=0;
  state.selected=mode==='SHORT'?null:state.row.querySelector(mode==='LONG'?'.vehicle':'.name');
 }
 target=0;
 nativeRects=states.map(s=>({icon:s.row.querySelector('.icon').getBoundingClientRect().toJSON(),tier:s.row.querySelector('.tier').getBoundingClientRect().toJSON(),
 name:s.row.querySelector('.name').getBoundingClientRect().toJSON(),vehicle:s.row.querySelector('.vehicle').getBoundingClientRect().toJSON()}));
 geometryPassed=true;
}
function request(value){target=value;for(const s of states)s.target=s.selected?value:0;}
document.querySelector('#mode').onchange=e=>{mode=e.target.value;select();};
document.querySelector('#toggle').onclick=()=>request(target?0:1);
document.querySelector('#cancel').onclick=()=>{request(0);for(const s of states)s.p=0;};
addEventListener('keydown',e=>{if(e.key==='Alt'){e.preventDefault();request(1);}});
addEventListener('keyup',e=>{if(e.key==='Alt'){e.preventDefault();request(0);}});
addEventListener('blur',()=>{request(0);for(const s of states)s.p=0;});
select();
request(query.get('alt')==='1'?1:0);
function frame(now){
 const dt=last?Math.min(50,now-last):0;last=now;let active=0;
 for(const s of states){
  if(!s.selected)continue;
  s.p=document.querySelector('#freeze').checked?0.5:step(s.p,s.target,query.has('capture')?DURATION:dt);
  if(s.p!==s.target)active++;
  const native=s.selected.querySelector('.native'), clip=s.selected.querySelector('.clip'), overlay=s.selected.querySelector('.overlay');
  clip.hidden=s.p===0;native.style.opacity=s.p===0?1:0;
  overlay.textContent=s.p>=0.5?statistics({state:PLAYERS_PANEL_STATE[mode]},fixtureMarker(s.data.stats)):native.textContent;overlay.style.transform='scaleX('+scale(s.p)+')';overlay.style.opacity=opacity(s.p);
 }
 if(mode===document.querySelector('#mode').value){
  for(let i=0;i<states.length;i++)for(const key of ['icon','tier','name','vehicle']){
   const before=nativeRects[i][key],after=states[i].row.querySelector('.'+key).getBoundingClientRect();
   if(before.x!==after.x||before.y!==after.y||before.width!==after.width||before.height!==after.height)geometryPassed=false;
  }
 }
 status.textContent='30 rows | mode '+mode+' | active transitions '+active+' | duration '+DURATION+' ms | '+(target?'statistics':'normal')+' | DOM geometry '+(geometryPassed?'PASS':'FAIL');
 document.documentElement.dataset.geometry=geometryPassed?'PASS':'CHANGED';
 document.documentElement.dataset.active=String(active);
 document.documentElement.dataset.mode=mode;
 window.panelPreview={rows:states.length,active,mode,geometryPassed};
 document.documentElement.dataset.ready='true';if(!query.has('capture'))requestAnimationFrame(frame);
}
frame(performance.now());
if(query.has('capture'))setTimeout(()=>frame(performance.now()),100);
</script>`;
fs.writeFileSync(path.join(output, 'preview.html'), html);
fs.writeFileSync(path.join(output, 'README.md'), `# PanelFlip 0.9.11 harness\n\nResult: PASS, ${assertions} assertions. Actual AS3 formulas: step, scale, opacity; duration ${duration} ms. Actual PanelModes.target and PanelModes.statistics methods executed with constants extracted from the client library dump. MEDIUM/LONG show WNX only; unavailable WNX shows one em dash while Alt is held. FULL retains all three values and partial-data dashes. SHORT remains untouched.\n\n30-row fixture tests MEDIUM, LONG, FULL, SHORT and their NO_BADGES variants; fast reversal, normal/stat endpoints, focus blocking until Alt release, disposal, preserved icon/tier/source rectangles and FULL vehicle. Overlay allocation and cleanup counters are fixture assertions, not measured Flash allocation counts. When all three statistics are absent, Alt shows one em dash and release restores the native name. Partial statistics retain available members and show dashes for missing members, never invented zero.\n\n${Object.keys(sourceContracts).length} additional source contracts inspect actual PanelTextSwap: lazy/reused passive overlay creation sites, source rectangle clipping, active-only tick, alpha restoration, detach pruning, focus blocking, disposal and listener removal. These are static contracts, not execution of the AS3 lifecycle.\n\nThe browser preview is local, uses the same extracted easing, and makes no game or network calls. It is not a screenshot from WoT. Query options: mode=FULL|MEDIUM|LONG|SHORT, alt=1, half=1; capture=1 renders a deterministic endpoint for headless screenshots. Sample colors are fixture markers, not WNX calibration.\n\nNode timing (${timings.environment}), median of 9 measured runs with performance.now over ${frames} frames and 30 rows:\n\n- baseline unthrottled fixture discovery: ${oldMs.toFixed(3)} ms (${timings.baselineRowVisits} row visits);\n- 50 ms throttled fixture discovery: ${newMs.toFixed(3)} ms (${timings.throttledRowVisits} row visits);\n- throttled discovery plus 30 repeated formula updates: ${animationMs.toFixed(3)} ms;\n- elapsed ratio throttled/baseline: ${(newMs / oldMs).toFixed(3)}.\n\nThese are synthetic plain-object traversal and actual formula timings in Node. They do not measure browser layout, Scaleform, game CPU, game memory or FPS. They cannot support a claim about client speedup or absence of FPS spikes. Native AS3 field lifecycle, mode switching, Alt+Tab, destruction and disposal still need client checks.\n`);
console.log(`PASS ${assertions} assertions; 8 mode fixtures, 30 rows each, reusable overlays, fast reversals, cancellation/disposal.`);
console.log(`Node fixture median: baseline ${oldMs.toFixed(3)} ms; throttled ${newMs.toFixed(3)} ms; with easing ${animationMs.toFixed(3)} ms. No client performance claim.`);
console.log(`Artifacts: ${output}`);
