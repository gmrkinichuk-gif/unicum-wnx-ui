// Execute the actual AS3 control consumers with small display/event fixtures.
import fs from 'node:fs';
import assert from 'node:assert/strict';

function method(file, name) {
  const source = fs.readFileSync(new URL('../as3/src/unicum/' + file, import.meta.url), 'utf8');
  const match = source.match(new RegExp(`(?:public|private)(?: static)? function ${name}\\(([\\s\\S]*?)\\) : \\w+\\s*\\{([\\s\\S]*?)\\n      \\}`));
  assert.ok(match, `${file}.${name} exists`);
  return [match[1].replace(/:\w+/g, ''), match[2]
    .replace(/for each\(var (\w+):\w+ in ([^)]+)\)/g, 'for(var $1 of $2)')
    .replace(/\s+as\s+\w+/g, '').replace(/(var\s+\w+):\w+/g, '$1')
    .replace(/catch\((\w+):\w+\)/g, 'catch($1)')];
}

const options = {signature: ''};
const [readArgs, readBody] = method('RosterOptions.as', 'read');
const read = new Function('int', `return function(${readArgs}){with(this){${readBody}}}`)(Number);
// AS3 bare static property accesses become fixture members under with(this).
for (const name of ['loadingBackground','loadingStripe','loadingOpacity','loadingStats',
  'panelBackground','panelStripe','panelOpacity','altStats','animation','duration']) options[name] = null;
assert.equal(read.call(options, '1,1,50,1,1,1,1,1,40,0,1,150'), true);
assert.equal(options.loadingOpacity, 0.5);
assert.equal(options.panelOpacity, 0.4);
assert.equal(read.call(options, options.signature), false, 'unchanged options do not invalidate rendering');
read.call(options, '0,0,0,0,1,0,0,1,100,2,0,999');
assert.equal(options.duration, 300, 'AS3 duration is bounded independently');
assert.deepEqual(options.loadingStats, [false,true,false]);
assert.equal(options.animation, false);

const [drawArgs, drawBody] = method('RosterRows.as', 'draw');
const draw = new Function('RosterOptions','RosterGrid','uint',
  `return function(${drawArgs}){with(this){${drawBody}}}`)(options,{stripe:(a,b,r)=>r?b-3:a},n=>n>>>0);
function render(compact, bg, stripe, opacity) {
  options[compact?'panelBackground':'loadingBackground'] = bg;
  options[compact?'panelStripe':'loadingStripe'] = stripe;
  options[compact?'panelOpacity':'loadingOpacity'] = opacity;
  const operations=[];
  const parent={};
  const graphics={clear(){operations.length=0;},beginFill(...args){operations.push(['fill',...args]);},
    drawRect(...args){operations.push(['rect',...args]);},endFill(){}};
  const state={bg:{parent,graphics},stats:[{parent},{parent},{parent}],signature:''};
  const rows={_rows:{icon:state}};
  const icon={parent,visible:true,toString:()=> 'icon'};
  const marker=[];marker[10]='#4a92b7';
  const bounds={x:0,y:0,width:300,height:24,left:0,right:300};
  draw.call(rows,icon,bounds,marker,compact,true);
  const old=operations.length;
  draw.call(rows,icon,bounds,marker,compact,true);
  assert.equal(operations.length,old,'settled row does not redraw');
  return operations;
}
for (const compact of [true,false]) {
  assert.equal(render(compact,false,false,0.4).length,0,'independent switches hide all graphics');
  assert.equal(render(compact,false,true,0.4).filter(op=>op[0]==='rect').length,1,'stripe works without background');
  const operations=render(compact,true,false,0.2);
  assert.equal(operations.filter(op=>op[0]==='rect').length,2,'background works without stripe');
  assert.ok(operations.some(op=>op[0]==='fill' && op[1]===0x4a92b7 && op[2]===0.2),'opacity reaches actual WNX graphics');
}
const [stepArgs,stepBody]=method('PanelFlip.as','step');
const step=new Function(stepArgs,stepBody);
assert.equal(step(0,1,50,50),1);
assert.equal(step(0,1,150,300),0.5);
const [advanceArgs,advanceBody]=method('PanelTextSwap.as','advance');
const advance=new Function('RosterOptions','PanelFlip',`return function(${advanceArgs}){${advanceBody}}`)(options,{step});
const transition={position:0,target:1,last:0};
advance(transition,1);
assert.equal(transition.position,1,'disabled animation snaps to the selected statistics');

const [statsArgs,statsBody]=method('PanelModes.as','statistics');
const stats=new Function('RosterOptions','PLAYERS_PANEL_STATE','int',`return function(${statsArgs}){${statsBody}}`)(options,{FULL:4,FULL_NO_BADGES:5},Number);
const marker=[];marker[11]='2180';marker[12]='56%';marker[13]='18.4k';marker.hasStats=true;marker.statsLine='2180 | 56% | 18.4k';
for(const [choice,expected] of [[1,'2180'],[2,'56%'],[3,'18.4k'],[4,marker.statsLine]]) {
  options.altStats=choice;
  assert.equal(stats({state:4},marker),expected,'selected Alt statistic reaches the native text slot');
}


for (const file of ['LobbyView.as', 'TeamNamesHtml.as']) {
  const host = fs.readFileSync(new URL('../as3/src/unicum/' + file, import.meta.url), 'utf8');
  assert.doesNotMatch(host, /SettingsTabs?|settingsTab/, 'native settings registration is absent');
}
const lobby = fs.readFileSync(new URL('../as3/src/unicum/LobbyView.as', import.meta.url), 'utf8');
assert.match(lobby, /new TrackerRoot\(this\)/, 'hangar Tracker remains available');
console.log('PASS WNX controls, removed native settings registration and retained Tracker host');
