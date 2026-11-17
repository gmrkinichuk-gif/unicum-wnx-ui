// Execute actual AS3 geometry bodies with display-object fixtures, not WoT.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

function body(file, name) {
  const source = fs.readFileSync(new URL('../as3/src/unicum/' + file, import.meta.url), 'utf8');
  const match = source.match(new RegExp(`(?:public|private)(?: static)? function ${name}\\(([\\s\\S]*?)\\) : \\w+\\s*\\{([\\s\\S]*?)\\n      \\}`));
  assert.ok(match, `missing actual method ${file}:${name}`);
  return [match[1].replace(/:\w+/g, ''), match[2]
    .replace(/for each\(var (\w+):\w+ in ([^)]+)\)/g, 'for(var $1 of $2)')
    .replace(/\s+as\s+\w+/g, '')
    .replace(/(var\s+\w+):\w+/g, '$1')
    .replace(/catch\((\w+):\w+\)/g, 'catch($1)')];
}

class Rectangle {
  constructor(x, y, width, height) { Object.assign(this, {x,y,width,height}); }
  get left() { return this.x; }
  get top() { return this.y; }
  get right() { return this.x + this.width; }
  get bottom() { return this.y + this.height; }
  union(b) {
    const x=Math.min(this.x,b.x), y=Math.min(this.y,b.y);
    return new Rectangle(x,y,Math.max(this.right,b.right)-x,Math.max(this.bottom,b.bottom)-y);
  }
}
let now=0;
function object(name,x,width,alpha=1) {
  return {name,x,width,alpha,height:20,visible:true,getBounds:()=>new Rectangle(x,0,width,20)};
}
const panelArgs = body('RosterLayout.as','panel');
const ownedFields=new Set();
const panel = new Function('Rectangle','getTimer','PanelTextSwap', `return function(${panelArgs[0]}){${panelArgs[1]}}`)(Rectangle,()=>now,{owns:field=>ownedFields.has(field)});
const full=object('playerNameFullTF',0,380), icon=object('vehicleIcon',210,90);
const action=object('actionMarker',290,20);
const children=[object('bg',0,450),object('hit',0,500),object('normAltBg',0,550),
  object('unusedAnimation',0,600,0),object('unicumPanelText',0,700),full,icon,action];
const row={state:4,y:0,x:0,numChildren:children.length,getChildAt:i=>children[i],toString:()=> 'native-row'};
const found=[{row,icon}];
const layout={_panels:{}};
const wide=panel.call(layout,found);
assert.equal(wide.right,380,'background and hit area cannot widen content');
assert.equal(wide.height,24);
assert.equal(panel.call(layout,found),wide,'unchanged layout uses bounded cache');
row.state=3; full.visible=false;
const narrow=panel.call(layout,found);
assert.equal(narrow.right,310,'mode change invalidates cache even when icon position is unchanged');
assert.equal(children[0].width,450,'native background remains untouched');
assert.equal(children[1].width,500,'native hit target remains untouched');
assert.equal(narrow.right,action.x+action.width,'functional native indicator remains covered');
row.state=4;full.visible=true;full.alpha=0;ownedFields.add(full);
assert.equal(panel.call(layout,found).right,380,'Alt-owned hidden source still reserves its native width');
ownedFields.delete(full);now=300;
assert.equal(panel.call(layout,found).right,310,'unowned transparent content stays excluded');

const stripeArgs=body('NameMarkerStripe.as','update');
const stripeUpdate=new Function('TextFormatAlign','uint',`return function(${stripeArgs[0]}){with(this){${stripeArgs[1]}}}`)({CENTER:'center',RIGHT:'right'},n=>n>>>0);
let fills=[],rects=[],boundsReads=0;
const view={parent:{parent:{}},visible:false,_signature:'',graphics:{clear(){},lineStyle(){},beginFill(color){fills.push(color);},drawRect(...r){rects.push(r);},endFill(){}}};
const rightArgs=body('NameMarkerStripe.as','textRight');
view.textRight=new Function('TextFormatAlign',`return function(${rightArgs[0]}){with(this){${rightArgs[1]}}}`)({CENTER:'center',RIGHT:'right'});
const label=(text,visible,x,y,width,height,align='center')=>({text,htmlText:text,visible,x,y,width,height,rotation:0,parent:{},scaleX:1,scaleY:1,textWidth:text.length*6,textHeight:14,
  getBounds(){boundsReads++;return new Rectangle(this.x,this.y,this.width,this.height);},getTextFormat:()=>({align})});
const player=label('Nickname [CLAN]',false,-50,-40,100,20);
const vehicle=label('CS-52 LIS',true,-50,-20,100,20);
const health={visible:true,parent:{},x:-35,y:0,width:70,height:8,getBounds(){return new Rectangle(this.x,this.y,this.width,this.height);}};
for(const color of [0xc55b3d,0xc6a72c,0x5c9f48,0x4a92b7,0x7a4fb2]) {
  stripeUpdate.call(view,player,vehicle,health,color);
  assert.equal(view.visible,true);
  assert.equal(fills.at(-1),color,'original supplied WNX colour stays exact');
  const line=rects.at(-1);
  assert.ok(line[0]-1>view.textRight(vehicle),'vertical stripe stays right of the visible vehicle text');
  assert.ok(line[1]-1>=vehicle.y && line[1]+line[3]+1<=vehicle.y+vehicle.height,'vertical stripe stays inside the text line height');
  assert.ok(line[1]+line[3]+1<=0 || line[1]-1>=8,'underline does not overlap the native HP bar');
  const count=rects.length,reads=boundsReads;
  stripeUpdate.call(view,player,vehicle,health,color);
  assert.equal(rects.length,count,'settled marker does not redraw vector graphics');
  assert.equal(boundsReads,reads,'settled marker does not recalculate bounds');
  assert.equal(rects.at(-1)[2],3,'WNX stripe matches the three-pixel team-panel accent');
}
const normal=rects.at(-1).slice();
player.visible=true;vehicle.visible=false;
stripeUpdate.call(view,player,vehicle,health,0x7a4fb2);
assert.notDeepEqual(rects.at(-1),normal,'Alt follows native nickname anchor');
assert.ok(rects.at(-1)[0]-1>view.textRight(player),'Alt stripe stays right of the nickname');
vehicle.visible=true;
vehicle.y=player.y;vehicle.textWidth=140;
stripeUpdate.call(view,player,vehicle,health,0x7a4fb2);
assert.ok(rects.at(-1)[0]-1>Math.max(view.textRight(player),view.textRight(vehicle)),'both simultaneous text labels remain clear of the vertical stripe');
vehicle.y=-20;
stripeUpdate.call(view,player,vehicle,health,-1);
assert.equal(view.visible,true,'unknown WNX keeps the neutral stripe');
assert.equal(fills.at(-1),0x666b73,'unknown WNX uses the existing roster grey');
const neutralRects=rects.length,neutralReads=boundsReads;
stripeUpdate.call(view,player,vehicle,health,-1);
assert.equal(rects.length,neutralRects,'settled unknown WNX does not redraw');
assert.equal(boundsReads,neutralReads,'settled unknown WNX does not recalculate bounds');
vehicle.htmlText='<font color="#ff0000">CS-52 LIS</font>';
stripeUpdate.call(view,player,vehicle,health,-1);
assert.equal(boundsReads,neutralReads,'style-only native markup does not invalidate unchanged stripe geometry');
stripeUpdate.call(view,player,vehicle,health,-2);
assert.equal(view.visible,false,'disabled marker adds no stripe');
stripeUpdate.call(view,player,vehicle,health,-1);
assert.equal(view.visible,true,'unknown stripe returns after enabling');
stripeUpdate.call(view,player,vehicle,health,0x4a92b7);
assert.equal(fills.at(-1),0x4a92b7,'late WNX replaces neutral grey with its original band');
player.visible=false;vehicle.visible=false;
stripeUpdate.call(view,player,vehicle,health,0x7a4fb2);
assert.equal(view.visible,false,'hidden native marker text stays hidden');
assert.equal(player.text,'Nickname [CLAN]');
assert.equal(health.visible,true);
vehicle.visible=true;
const iconObstacle={visible:true,parent:{},x:60,y:-20,width:16,height:20,getBounds(){return new Rectangle(this.x,this.y,this.width,this.height);}};
const firstSegment=rects.length;
stripeUpdate.call(view,player,vehicle,health,0x7a4fb2,iconObstacle);
for(const r of rects.slice(firstSegment)) assert.ok(r[0]>=76,'native vehicle-type icon remains unobscured');
health.y=-20;health.width=160;
stripeUpdate.call(view,player,vehicle,health,0x7a4fb2);
assert.ok(rects.at(-1)[0]-1>health.x+health.width,'a native HP element in the same band is avoided horizontally');
const disposeArgs=body('NameMarkerStripe.as','dispose');
const stripeDispose=new Function(`return function(){with(this){${disposeArgs[1]}}}`)();
stripeDispose.call(view);
assert.equal(view._field,null);
assert.equal(view._host,null);
assert.equal(view._health,null);
assert.equal(view._obstacle,null);
assert.equal(view.visible,false,'disposed underline releases its native anchors');
const displayedArgs=body('VehicleMarkers.as','displayed');
const displayed=new Function(`return function(${displayedArgs[0]}){${displayedArgs[1]}}`)();
const stage={visible:true,alpha:1,parent:null,stage:{}};
const branch={visible:true,alpha:1,parent:stage,stage:{}};
assert.equal(displayed(branch),true,'visible on-stage roster branch is updated');
branch.visible=false;
assert.equal(displayed(branch),false,'hidden roster branch is skipped');
branch.visible=true;stage.alpha=0;
assert.equal(displayed(branch),false,'transparent ancestor skips retained loading rows');
stage.alpha=1;branch.stage=null;
assert.equal(displayed(branch),false,'detached roster branch is skipped');
// The AS3 `as DisplayObject` cast yields null for an older proxy; the JS
// body runner has no runtime type system, so model that cast result here.
assert.equal(displayed(null),true,'legacy non-display proxy stays compatible');
const viewDisposeArgs=body('NameMarkerView.as','dispose');
const geometryArgs=body('RosterRows.as','setGeometry');
const setGeometry=new Function(`return function(${geometryArgs[0]}){${geometryArgs[1]}}`)();
let geometryWrites=0,nativeX=10,nativeWidth=120;
const geometryField={toString:()=> 'fixture',get x(){return nativeX;},set x(v){geometryWrites++;nativeX=v;},
  get width(){return nativeWidth;},set width(v){geometryWrites++;nativeWidth=v;}};
const geometryOwner={_geometry:{fixture:{}}};
for(let i=0;i<100;i++)setGeometry.call(geometryOwner,geometryField,10,120,true);
assert.equal(geometryWrites,0,'stable roster geometry causes no redundant native writes');
nativeX=15;nativeWidth=80;
setGeometry.call(geometryOwner,geometryField,10,120,true);
assert.equal(geometryWrites,2,'a real client geometry overwrite is still corrected');
const viewSource=viewDisposeArgs[1].replace('var waiting = _images[key];','var waiting = Array.isArray(_images[key]) ? _images[key] : null;');
const markerView={_anchor:{},_vehicleAnchor:{},_healthAnchor:{},_wanted:['asset'],_stripe:{dispose(){}},visible:true};
const anotherView={};
const images={pending:[markerView,anotherView],cached:{bitmap:true}};
const disposeView=new Function('_images',`return function(){with(this){${viewSource}}}`)(images);
disposeView.call(markerView);
assert.equal(markerView._anchor,null);
assert.equal(markerView._vehicleAnchor,null);
assert.equal(markerView._healthAnchor,null);
assert.deepEqual(images.pending,[anotherView],'disposal removes only this marker from shared image waiters');
assert.equal(images.cached.bitmap,true,'shared bitmap cache is preserved');
const colorArgs=body('RosterTextColors.as','apply');
const colorApply=new Function('field',`return function(${colorArgs[0]}){${colorArgs[1]}}`)((row,key)=>row[key]);
const calls=[];
const vehicleColors=[];
const colors={setNameColor(...args){calls.push(args);},setColor(...args){vehicleColors.push(args);}};
const nativeRow={playerNameFullTF:{},playerNameCutTF:{},vehicleTF:{}};
colorApply.call(colors,nativeRow,'#f2f3f5',true,true,true,'CLAN','Self',null,true);
assert.ok(calls.every(call=>call[2]===false && call[3]===false),'current native name formats remain owned by the client');
assert.equal(vehicleColors.at(-1)[1],null,'current vehicle keeps its native colour');
calls.length=0;
colorApply.call(colors,nativeRow,'#f2f3f5',true,true,true,'CLAN','Other',null,false);
assert.ok(calls.every(call=>call[2]===true && call[3]===true),'other-player name colouring remains enabled');
assert.equal(vehicleColors.at(-1)[1],'#f2f3f5','other-player vehicle styling stays enabled');
const currentArgs=body('RosterTextColors.as','currentColor');
const currentColor=new Function('uint',`return function(${currentArgs[0]}){${currentArgs[1]}}`)(n=>n>>>0);
assert.equal(currentColor({length:5,getTextFormat:()=>({color:0xffdd66})}),0xffdd66,'statistics reuse the actual native name colour');
assert.equal(currentColor({length:0,textColor:0xccaa66}),0xccaa66,'empty fields use the native default colour');
const previewRoot=fileURLToPath(new URL('../build/checks/marker-stripe/',import.meta.url));
fs.mkdirSync(previewRoot,{recursive:true});
const pictures=[];
for(const scenario of [{alt:false,color:0x5c9f48},{alt:true,color:0x5c9f48},{alt:false,color:-1},{alt:true,color:-1}]) {
  const {alt,color}=scenario;
  player.visible=alt;vehicle.visible=!alt;vehicle.y=-20;vehicle.textWidth=54;health.y=0;health.width=70;
  view._token='';view._signature='';rects=[];fills=[];
  stripeUpdate.call(view,player,vehicle,health,color);
  const active=alt?player:vehicle;
  const shapes=rects.map((r,i)=>`<rect x="${r[0]}" y="${r[1]}" width="${r[2]}" height="${r[3]}" fill="#${fills[i].toString(16).padStart(6,'0')}"/>`).join('');
  const badgeX=view.textRight(player)+12;
  const badge=alt&&color>=0?`<rect x="${badgeX}" y="-37" width="23" height="14" fill="#5c9f48"/><text x="${badgeX+11.5}" y="-27" text-anchor="middle" fill="white" font-size="10">2180</text>`:'';
  pictures.push(`<section><h2>${alt?'Alt nickname':'Normal vehicle'} — ${color<0?'WNX unavailable':'WNX available'}</h2><svg viewBox="-85 -55 230 100" width="690" height="300"><rect x="-85" y="-55" width="230" height="100" fill="#26323d"/><text x="0" y="${active.y+14}" text-anchor="middle" textLength="${active.textWidth}" lengthAdjust="spacingAndGlyphs" fill="#c6e5b3" font-size="12">${active.text}</text><rect x="-35" y="0" width="70" height="8" fill="#648e20"/><text x="0" y="7" text-anchor="middle" fill="white" font-size="8">1350 / 1350</text><path d="M0 11L6 17L0 23L-6 17Z" fill="#7cd626"/>${shapes}${badge}</svg></section>`);
}
fs.writeFileSync(path.join(previewRoot,'preview.html'),`<!doctype html><meta charset="utf-8"><style>body{background:#10151d;color:#eef;font:16px Arial;padding:24px}section{display:inline-block;margin-right:20px}h2{font-size:18px}</style><h1>Vertical WNX marker accent — local fixture</h1><p>Actual AS3 geometry with display-object fixtures. Not a WoT screenshot.</p>${pictures.join('')}`);
console.log('PASS actual AS3 panel bounds/cache and vertical marker stripe: 3px, normal/Alt right text edge, simultaneous labels, type/HP obstacles, neutral unknown WNX, disabled marker, late WNX, colour, cache and disposal');
