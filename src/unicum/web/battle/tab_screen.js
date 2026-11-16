// Reflow the existing Gameface roster so client bindings and hit targets survive.
// Only our statistics spans are created. Names, icons and status nodes are native.
const { model, report } = api;
const VIEW = '[class*="FullStatsApp_view_"]';
const ROW = '[class*="Player_base_"]';
const NAME = '[class*="UserInfo_userName_"] > [class*="UserInfo_tooltip_trigger_"], [data-bind-value*=".hiddenUserName"]';
const HEX = /^#[0-9a-f]{6}$/i;
const owned = new Map();
const classes = new Map();
const rows = new Map();
let raw = null;
let data = {};
let alive = true;
let told = false;
let visible = false;
let modelCount = '';
let lastError = '';

function log(message) { try { report(`roster 0.9.15: ${message}`); } catch (error) {} }
function connected(node) { return document.documentElement.contains(node); }
log('script created');

function css(node, key, value) {
  if (!node) return;
  let saved = owned.get(node);
  if (!saved) { saved = new Map(); owned.set(node, saved); }
  // Coherent exposes getPropertyValue but not getPropertyPriority in 2.4.1.1.
  // Priority is optional restore metadata, never a rendering prerequisite.
  if (!saved.has(key)) saved.set(key, [node.style.getPropertyValue(key),
    typeof node.style.getPropertyPriority === 'function' ? node.style.getPropertyPriority(key) : '']);
  if (node.style.getPropertyValue(key) !== value) node.style.setProperty(key, value);
}
function mark(node, name) {
  if (!node) return;
  if (!classes.has(node)) classes.set(node, new Set());
  classes.get(node).add(name);
  node.classList.add(name);
}
function filteredMark(root, selector, name, excluded) {
  // Coherent 2.4.1.1 rejects CSS negation selectors. Preserve the original
  // case-sensitive class-substring exclusions and own the positive class.
  for (const node of Array.from(root.querySelectorAll(selector))) {
    const native = node.getAttribute('class') || '';
    if (excluded.every(part => native.indexOf(part) < 0)) mark(node, name);
    else {
      node.classList.remove(name);
      const marked = classes.get(node);
      if (marked) marked.delete(name);
    }
  }
}
function restore(node) {
  const saved = owned.get(node);
  if (saved) for (const [key, value] of saved) {
    if (value[0]) node.style.setProperty(key, value[0], value[1]);
    else node.style.removeProperty(key);
  }
  owned.delete(node);
  const marked = classes.get(node);
  if (marked) for (const name of marked) node.classList.remove(name);
  classes.delete(node);
}
function text(node, value) {
  if (node.textContent !== value) node.textContent = value;
}
function rgba(hex, opacity) {
  return `rgba(${parseInt(hex.slice(1,3),16)},${parseInt(hex.slice(3,5),16)},${parseInt(hex.slice(5,7),16)},${opacity})`;
}
function wnx(value) {
  return typeof value === 'number' && Number.isFinite(value)
    ? String(Math.round(value)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : '';
}
function rem(px) {
  return typeof viewEnv !== 'undefined' && viewEnv.pxToRem ? viewEnv.pxToRem(px) : px;
}
function statsOf(player) {
  if (!data.shown) return [];
  return [wnx(player && player.wnx), player && player.winrate, player && player.battles]
    .map(value => value === undefined || value === null || value === '' ? '\u2014' : String(value));
}
function removeRow(row) {
  const entry = rows.get(row);
  if (entry) { entry.block.remove(); entry.eye.remove(); if (entry.liveHost) restore(entry.liveHost); if (entry.live) restore(entry.live); }
  rows.delete(row);
}
function decorate(row, side) {
  const name = row.querySelector(NAME);
  const key = name ? (name.textContent || '').trim() : '';
  const player = key ? (data.players || {})[key] : null;
  const color = player && HEX.test(player.bandColor) ? player.bandColor : '#666b73';
  // Client TabView binds Player_base__killed_* directly to item.isKilled.
  const killed = (row.getAttribute('class') || '').indexOf('Player_base__killed_') >= 0;
  mark(row, 'unicum-roster-row');
  filteredMark(row, '[class*="Player_vehicleContour_"]', 'unicum-roster-contour',
    ['wrapper', 'image', 'level', 'voice']);
  if (side === 'enemies') mark(row, 'unicum-roster-enemy');
  css(row, 'background-color', 'rgba(12,16,22,0.96)');
  css(row, 'background-image', `linear-gradient(${rgba(color, 0.42)},${rgba(color, 0.42)})`);
  // The client itself uses inset shadows. A wash sits over the WNX fill
  // and below text without introducing a tooltip-clipping stacking context.
  css(row, 'box-shadow', killed ? 'inset 0 0 0 1000rem rgba(160,25,30,0.24)' : 'none');
  css(row, 'border-left-color', color);
  css(row, 'border-right-color', color);
  let entry = rows.get(row);
  if (!entry) {
    const block = document.createElement('div');
    block.className = 'unicum-roster-stats';
    for (const label of ['WNX', 'WR', 'Battles']) {
      const cell = document.createElement('span');
      cell.title = label;
      block.appendChild(cell);
    }
    const eye = document.createElement('span');
    eye.className = 'unicum-tab-eye';
    eye.title = 'Rating or displayed nickname unavailable';
    entry = { block, eye, live: null, liveHost: null };
    rows.set(row, entry);
  }
  // Own spans can live beside the nickname without moving any bound native
  // node. The native row's contour, vehicle and status columns stay intact.
  const user = row.querySelector('[class*="UserInfo_user_info_"]');
  if (user && entry.block.parentElement !== user) user.appendChild(entry.block);
  entry.block.style.display = data.shown ? '' : 'none';
  const values = statsOf(player);
  for (let i = 0; i < 3; i++) text(entry.block.children[i], values[i] || '');
  const nickWrap = row.querySelector('[class*="UserInfo_nickname_wrapper_"]');
  const live = row.querySelector('[class*="LiveTag_liveTag__wrapper_"]');
  // The bound LiveTag root is a direct row child in the client's It/Du.
  // Put that same node in flow even while data-bind-if hides its icons:
  // a later client update can reveal them without a geometry/polling race.
  let liveHost = live;
  while (liveHost && liveHost.parentElement !== row) liveHost = liveHost.parentElement;
  if (entry.live && (entry.live !== live || side !== 'allies')) restore(entry.live);
  if (entry.liveHost && (entry.liveHost !== liveHost || side !== 'allies')) restore(entry.liveHost);
  entry.live = side === 'allies' ? live : null;
  entry.liveHost = side === 'allies' ? liveHost : null;
  if (live && liveHost && side === 'allies') {
    mark(liveHost, 'unicum-roster-live-host');
    mark(live, 'unicum-roster-live-tag');
  }
  const unknown = !key || !player || !player.wnxAvailable ||
    (name && name.getAttribute('data-bind-value') || '').indexOf('.hiddenUserName') >= 0;
  if (nickWrap && unknown && data.indicatorEnabled) {
    if (entry.eye.parentElement !== nickWrap) nickWrap.appendChild(entry.eye);
  } else entry.eye.remove();
  return player && player.wnxAvailable ? 1 : 0;
}
function average(header, side) {
  if (!header) return;
  let node = header.querySelector('.unicum-roster-average');
  const rating = data.shown && data.averages && data.averages[side];
  if (!rating) { if (node) node.remove(); return; }
  if (!node) { node = document.createElement('span'); node.className = 'unicum-roster-average'; header.appendChild(node); }
  const image = rating.image;
  node.style.backgroundImage = image ? `url(${image})` : '';
  node.style.width = image ? `${rating.width}rem` : '';
  node.style.height = image ? `${rating.height}rem` : '';
  text(node, image ? '' : wnx(rating.value));
}
function render() {
  if (!alive) return;
  const view = document.querySelector(VIEW);
  if (!view || !view.getBoundingClientRect().height) { visible = false; return; }
  if (!visible) { visible = true; log('Tab visible; native view found'); }
  const current = model.model && model.model.data;
  if (current && current !== raw) {
    try { data = JSON.parse(current); raw = current; }
    catch (error) { log(`bad model data: ${error}`); }
    const count = `${Object.keys(data.players || {}).length} aliases, shown=${!!data.shown}`;
    if (count !== modelCount) { modelCount = count; log(`model received: ${count}`); }
  }
  if (data.redesignEnabled === false) {
    for (const node of Array.from(document.querySelectorAll('.unicum-roster-average'))) node.remove();
    for (const row of rows.keys()) removeRow(row);
    for (const node of Array.from(classes.keys())) restore(node);
    return;
  }
  mark(view, 'unicum-roster-view');
  filteredMark(view, '[class*="FullStatsApp_fullStats_"]', 'unicum-roster-content', ['header', 'list']);
  const width = Math.min(700, Math.floor((rem(document.documentElement.clientWidth) - 48) / 2));
  if (width < 680) mark(view, 'unicum-roster-compact');
  else view.classList.remove('unicum-roster-compact');
  const header = view.querySelector('[class*="FullStatsApp_fullStats_header_"]');
  let matched = 0;
  let liveCount = 0;
  let liveVisible = 0;
  const active = new Set();
  for (const [index, side] of ['allies', 'enemies'].entries()) {
    const team = view.querySelector(`[class*="FullStatsApp_${side}_"]`);
    if (!team) continue;
    mark(team, 'unicum-roster-team');
    css(team, 'width', `${Math.max(1, width)}rem`);
    const heading = header && header.children[index];
    if (heading) { mark(heading, 'unicum-roster-heading'); css(heading, 'width', `${Math.max(1, width)}rem`); }
    for (const row of Array.from(team.querySelectorAll(ROW))) {
      active.add(row);
      matched += decorate(row, side);
      const entry = rows.get(row);
      if (entry && entry.live) { liveCount++; if (entry.live.getBoundingClientRect().height > 0) liveVisible++; }
    }
    average(heading, side);
  }
  for (const row of rows.keys()) if (!active.has(row) || !connected(row)) { removeRow(row); restore(row); }
  for (const node of classes.keys()) if (!connected(node)) { owned.delete(node); classes.delete(node); }
  const counts = `${active.size} rows, ${matched} WNX matches, native Live Tags ${liveVisible}/${liveCount} visible`;
  if (counts !== told) { told = counts; log(`rendered: ${counts}`); }
}
function poll() {
  try { render(); }
  catch (error) {
    const message = String(error);
    if (message !== lastError) { lastError = message; log(`render failed: ${message}`); }
  }
}
const timer = setInterval(poll, 200);
poll();
return { stop() {
  alive = false;
  clearInterval(timer);
  for (const row of rows.keys()) removeRow(row);
  for (const node of Array.from(classes.keys())) restore(node);
  for (const node of Array.from(owned.keys())) restore(node);
  for (const node of Array.from(document.querySelectorAll('.unicum-roster-average'))) node.remove();
  log('script stopped');
} };
