// Execute actual AS3 bodies with display/event fixtures. This is not a live GFx test.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {checkTrackerSettings} from './check_tracker_settings_fixture.mjs';
let assertions=0;
function ok(value,message){assert.ok(value,message);assertions++;}
function method(file,name){
 const source=fs.readFileSync(new URL('../as3/src/unicum/tracker/'+file+'.as',import.meta.url),'utf8');
 const found=source.match(new RegExp(`(?:public|private)(?: static)? function ${name}\\(([\\s\\S]*?)\\)(?: : [\\w*]+)?\\s*\\{([\\s\\S]*?)\\n      \\}`));
 assert.ok(found,`${file}.${name}`);
 const strip=s=>s.replace(/:\s*(?:Wire|Number|String|Boolean|Object|Array|Function|Sprite|MouseEvent|FocusEvent|TextField|TextFormat|Graph|Point|Rectangle|Matrix|TrackerRoot|SettingsControls|OpacitySlider|Event|KeyboardEvent|InteractiveObject|DisplayObjectContainer|DisplayObject|int|uint|void|\*)(?=\s*[,)=;{]|\s+in\b|\s*$)/g,'')
   .replace(/:\*/g,'').replace(/(\w+) is (String|Number|Boolean)/g,(_,v,t)=>`(typeof ${v} === '${t.toLowerCase()}')`)
   .replace(/\bis\b/g,'instanceof').replace(/for each\(var (\w+) in ([^)]+)\)/g,'for(var $1 of $2)');
 return [strip(found[1]),strip(found[2])];
}
function compile(file,name,deps={}){
 const [args,body]=method(file,name);
 return new Function(...Object.keys(deps),`return function(${args}){with(this){${body}}}`)(...Object.values(deps));
}
const Geometry={};
for(const name of ['step','barWidth','clamp','fit']) Geometry[name]=compile('Geometry',name).bind(Geometry);
class Sprite{
 constructor(){this.children=[];this.handlers={};this.x=0;this.y=0;this.scaleX=this.scaleY=1;
  const ops=this.ops=[];this.graphics={clear(){ops.length=0;},lineStyle(...a){ops.push(['lineStyle',...a]);},
   beginFill(...a){ops.push(['fill',...a]);},beginGradientFill(...a){ops.push(['gradient',...a]);},
   endFill(){ops.push(['end']);},drawRect(...a){ops.push(['rect',...a]);},
   drawRoundRect(...a){ops.push(['round',...a]);},
   moveTo(...a){ops.push(['move',...a]);},lineTo(...a){ops.push(['line',...a]);},drawCircle(...a){ops.push(['circle',...a]);}};}
 addChild(child){this.children.push(child);child.parent=this;return child;}
 addChildAt(child,index){this.children.splice(index,0,child);child.parent=this;return child;}
 get numChildren(){return this.children.length;}
 removeChildAt(index){this.children.splice(index,1)[0].parent=null;}
 removeChild(child){this.removeChildAt(this.children.indexOf(child));}
 get height(){return this.ops.find(op=>op[0]==='round')?.[4]??0;}
 localToGlobal({x,y}){const point={x:x*this.scaleX+this.x,y:y*this.scaleY+this.y};return this.parent?.localToGlobal(point)??point;}
 globalToLocal(point){const {x,y}=this.parent?.globalToLocal(point)??point;return {x:(x-this.x)/this.scaleX,y:(y-this.y)/this.scaleY};}
 addEventListener(type,fn){this.handlers[type]=fn;}
}
class Rectangle{constructor(x,y,width,height){Object.assign(this,{x,y,width,height});}}
class Matrix{createGradientBox(width,height,angle){Object.assign(this,{width,height,angle});}}
class DropShadowFilter{
 constructor(distance,angle,color,alpha,blurX,blurY){Object.assign(this,{distance,angle,color,alpha,blurX,blurY});}
}
const Glass={text(parent,value,x,y,width,height=22,size=13,color=0xd9dde4){
 const field={value,x,y,width,height,size,color,defaultTextFormat:{size,color,align:'left'},
  setTextFormat(format){this.size=format.size;this.align=format.align;},
  get textWidth(){return this.value.length*this.size*0.64;},get textHeight(){return this.size*1.15;}};
 field.addEventListener=(type,fn)=>{field[type]=fn;};
 return parent.addChild(field);
}};
const MouseEvent={MOUSE_OVER:'over',MOUSE_OUT:'out',ROLL_OVER:'rollover',ROLL_OUT:'rollout',MOUSE_DOWN:'down',
 MOUSE_MOVE:'move',MOUSE_UP:'up',CLICK:'click',MOUSE_WHEEL:'wheel'};
const deps={Sprite,Rectangle,Matrix,DropShadowFilter,GradientType:{LINEAR:'linear'},Geometry,Glass,uint:x=>Number(x)>>>0,MouseEvent};
for(const name of ['number','mix','tint','verticalFill','raisedPanel','clear']) Glass[name]=compile('Glass',name,deps).bind(Glass);
const TrackerIcons={DAMAGE:'avgDamage24.png', ASSIST:'assist24.png', SETTINGS:'settings.png',
 draw(parent,path,x,y,size){parent.addChild({icon:path,x,y,size});}};
const iconsSource=fs.readFileSync(new URL('../as3/src/unicum/tracker/TrackerIcons.as',import.meta.url),'utf8');
for(const [name,path] of Object.entries({DAMAGE:'statistic/avgDamage24.png',ASSIST:'statistic/assist24.png',SETTINGS:'buttons/settings.png'}))
 ok(iconsSource.includes(`const ${name}:String = "../maps/icons/${path}"`),'uses the documented client resource path');
const Card={};
Object.assign(deps,{Card,TrackerIcons});
for(const name of ['line','rule','control','button','metric']) Card[name]=compile('Card',name,deps).bind(Card);
const bind=compile('Graph','bind',deps);
const construct=compile('Graph','Graph',deps);
for(const count of [10,20,30])for(const bars of [true,false]){
 const values=Array.from({length:count},(_,i)=>({tankName:`Tank ${i}`,wnx:i===3?null:i===4?0:i===5?300000:i*330,color:'#83579d'}));
 const graph=new Sprite();graph.WIDTH=252;graph.HEIGHT=60;graph.bind=bind;
 const hovers=[];construct.call(graph,values,bars,0x83579d,(row,isBar)=>hovers.push([row,isBar]));
 const plot=graph.children[0];
 const ticks=graph.children.slice(2);
 ok(ticks.every(field=>field.x>=0 && field.x+field.width<=252),'all chart labels fit horizontally');
 ok(plot.scrollRect.width===252 && plot.scrollRect.height===60,'plot clipped');
 ok(plot.children.length===count,'each position has a distinct hit area');
 for(let i=0;i<count;i++){
  const hit=plot.children[i],rect=hit.ops.find(op=>op[0]==='rect');
  ok(Math.abs(hit.x-i*252/count)<1e-9 && rect[1]===0 && Math.abs(rect[3]-252/count)<1e-9,'nonoverlapping step-bounded hit zones');
  hit.handlers.over({});
  ok(hovers.at(-1)[0]===values[i],'hover identifies the exact tank/point');
  hit.handlers.out({});ok(hovers.at(-1)[0]===null,'hover exit clears tooltip');
 }
 if(bars){
  const rects=plot.ops.filter(op=>op[0]==='rect');
  ok(rects.length===count,'all bars, including explicit unavailable marker, retained');
  for(let i=0;i<count;i++){
   const [,x,y,w,h]=rects[i];
   ok(x>=i*252/count && x+w<=(i+1)*252/count+1e-9 && w<252/count,'positive bar gap');
   ok(y>=0 && y+h<=60 && Number.isFinite(h),'zero/extreme/missing heights fit plot');
  }
 }
}
class Point{constructor(x=0,y=0){Object.assign(this,{x,y});}}
const tooltip=compile('TrackerRoot','tooltip',{...deps,Point});
const tooltipRoot={_state:{color:'#65717e'},_settings:null,_tooltip:new Sprite(),_widget:{y:8,scaleY:1,panelHeight:200},
 _viewportWidth:1280,_viewportHeight:720,numChildren:2,word:key=>key,globalToLocal:point=>point,setChildIndex(){}};
const tooltipTarget={width:10,height:76,localToGlobal:point=>point};
const battle={tankName:'Test tank',time:'11:11',damageDealt:0,damageAssistedRadio:0,
 damageAssistedTrack:null,wnx:null,message:'Incomplete battle results'};
tooltip.call(tooltipRoot,battle,true,tooltipTarget);
ok(tooltipRoot._tooltip.children[0].filters.length===1 && !tooltipRoot._tooltip.children[0].mouseEnabled,
 'battle tooltip uses the same glass surface and passive shadow');
const tooltipValues=()=>tooltipRoot._tooltip.children.filter(item=>'value' in item).map(item=>item.value);
ok(tooltipValues().includes('0') && tooltipValues().includes('—') &&
 tooltipValues().includes('Incomplete battle results'),'partial tooltip shows zero damage and an unavailable assist');
ok(tooltipRoot._tooltip.y===216,'point tooltip opens outside the chart card without covering its footer');
tooltip.call(tooltipRoot,{...battle,damageAssistedTrack:0,wnx:0,message:''},true,tooltipTarget);
ok(tooltipValues().includes('WNX  0') && tooltipValues().filter(value=>value==='0').length===2,
 'complete tooltip preserves both genuine zeroes with no third metric');
tooltip.call(tooltipRoot,{time:'11:11',arenaUniqueId:'123',wnx:null,message:'Expected WNX values are unavailable'},
 false,tooltipTarget);
ok(tooltipValues().includes('Expected WNX values are unavailable'),'trend gap tooltip shows its reason');
ok(tooltipRoot._tooltip.children[0].ops.some(op=>op[0]==='gradient'),'trend tooltip uses the same glass gradient');
tooltip.call(tooltipRoot,null,false,tooltipTarget);
ok(!tooltipRoot._tooltip.numChildren,'leaving the graph removes the complete tooltip');

class Graph extends Sprite{
 constructor(...args){super();this.WIDTH=252;this.HEIGHT=60;this.bind=bind;construct.apply(this,args);}
}
const widgetMethods={};
for(const name of ['update','draw','drawModeTabs','selectMode','drawScore','addGraph'])
 widgetMethods[name]=compile('Widget',name,{...deps,Graph});
const labels=Object.fromEntries([...fs.readFileSync(new URL('../src/unicum/tracker/localize.py',import.meta.url),'utf8')
 .matchAll(/'(Mini|Compact|Trend|Battles)': u'([^']+)'/g)].map(([,key,value])=>[key,value]));
const modes=['Mini','Compact','Trend','Battles'];
const fixtureRows=Array.from({length:20},(_,i)=>({
 wnx:[832, 2100, 1263, 1052, 998, 1300, 1940, 1780, 1020, 1600, 2600, 2450, 900, 102, 400, 1800, 2110, 950, 1420, 3200][i],
 color:['#d6a858','#a481bd','#aeb959','#99ad83','#bc7a67'][i%5],
}));
function cardFixture(mode,locale,color='#8f68b2',extra={}){
 const actions=[];
 const widget={...widgetMethods,_body:new Sprite(),panelWidth:272,panelHeight:76,beginDrag(){},
  _state:{mode,color,opacity:88,count:20,progress:20,total:1518,wnx:1694,delta:-129,damage:2338,assist:331,
   points:fixtureRows.map((row,i)=>({...row,wnx:1610+Math.sin(i/4)*220-i*5})),bars:fixtureRows,...extra},
  _owner:{word:key=>locale==='uk'?labels[key]:key,send:action=>actions.push(action),
   openSettings(){actions.push('gear');},tooltip(){},layout(){}}};
 widget.draw();
 return {widget,actions};
}
for(const locale of ['en','uk'])for(const mode of modes){
 const {widget,actions}=cardFixture(mode,locale);
 const children=widget._body.children;
 const controls=children.filter(child=>child.buttonMode);
 ok(controls.length===5,'four modes and one settings control');
 ok(controls.slice(0,4).map(tab=>tab.children[0].value).join()===
  modes.map(key=>locale==='uk'?labels[key]:key).join(),'all four complete labels are present');
 for(const [i,tab] of controls.entries()){
  const frame=tab.ops.find(op=>op[0]==='round');
  const field=tab.children[0];
  ok(tab.x+frame[3]<=(controls[i+1]?.x??widget.panelWidth),'header controls stay within the card');
  if(i<4){
   ok(field.align==='center' && field.textWidth+4<=field.width && !field.multiline && !field.wordWrap,
    'labels fit on one line with Scaleform gutters');
   ok(tab.ops.some(op=>op[0]==='line')===(mode===modes[i]),'selected mode alone is underlined');
  }else ok(field.icon===TrackerIcons.SETTINGS,'settings uses the native icon');
  tab.handlers.click({stopPropagation(){}});
 }
 ok(actions.slice(0,4).every((action,i)=>action.kind==='mode'&&action.value===modes[i])&&actions[4]==='gear',
  'mode and gear clicks dispatch original actions');
 const score=children.find(field=>field.value===(mode==='Mini'?'1518':'1694'));
 ok(score.align==='center' && score.x+score.width/2===(mode==='Mini'?136:73),'WNX centered in its own field');
 const delta=children.find(field=>field.value==='-129');
 if(mode!=='Mini')ok(delta.align==='center'&&delta.x+delta.width/2===199,'delta centered in the right field');
 const graph=children.find(child=>child instanceof Graph);
 const icons=children.filter(child=>child.icon);
 if(mode==='Trend'||mode==='Battles'){
  ok(widget.panelHeight===200 && graph.y+91<icons[0].y,'both metrics stay below the graph');
  ok(icons.map(child=>child.icon).join()==='avgDamage24.png,assist24.png','footer has exactly the two native icons');
  ok(icons.every(icon=>icon.size===24 && icon.y+icon.size<widget.panelHeight),'native-sized icons fit the footer');
  ok(children.filter(field=>field.y>=171 && 'value' in field).map(field=>field.value).join()==='2338,331',
   'footer only shows the two average values');
 }else ok(widget.panelWidth===272&&widget.panelHeight===76&&!graph&&!icons.length,'Mini and Compact share the same size');
 ok(children.filter(field=>'value' in field).every(field=>field.y+field.height<=widget.panelHeight+1),
  'card content fits vertically');
 ok(!children.some(child=>child.handlers?.rollover&&!child.buttonMode),'card has no summary-on-hover listener');
}
const purple=cardFixture('Battles','uk').widget._body;
const green=cardFixture('Battles','uk','#769f50').widget._body;
function gradient(sprite){return sprite.ops.find(op=>op[0]==='gradient');}
ok(gradient(purple.children[0])[2][1]!==gradient(green.children[0])[2][1],'glass tint follows the WNX color');
for(const opacity of [40,90]){
 const {widget}=cardFixture('Compact','uk','#769f50',{opacity});
 const body=widget._body,surface=body.children[0];
 const [,type,colors,alphas,stops,matrix]=gradient(surface);
 ok(type==='linear' && matrix.angle===Math.PI/2 && matrix.height===widget.panelHeight &&
  alphas.every(alpha=>alpha===opacity/100) && stops.join()==='0,106,255',
  'panel uses the selected opacity through a vertical gradient');
 ok((colors[0]&255)>(colors[1]&255) && (colors[1]&255)>(colors[2]&255),'upper glass is lighter than the base and bottom');
 ok(surface.mouseEnabled===false && surface.mouseChildren===false && surface.filters[0].distance===4 &&
  surface.filters[0].blurY===8 && body.ops.find(op=>op[0]==='round')[4]===widget.panelHeight,
  'soft shadow is isolated from input and only the card dimensions are interactive');
 const active=body.children.filter(child=>child.buttonMode)[1];
 ok(gradient(active)&&active.ops.some(op=>op[0]==='move'&&op[2]===1),'selected tab has a lit upper edge');
}
ok(new Set(purple.children.find(child=>child instanceof Graph).children[0].ops.filter(op=>op[0]==='fill').map(op=>op[1])).size>2,
 'bar color follows the individual battle rating');
const waiting=cardFixture('Trend','uk','#779153',{progress:6,wnx:null,message:'Зіграйте ще 14 випадкових боїв'}).widget;
ok(waiting.panelHeight===106 && waiting._body.children.some(field=>field.value==='6/20') &&
 waiting._body.children.some(field=>field.value===waiting._state.message) &&
 !waiting._body.children.some(field=>field instanceof Graph || field.icon),'incomplete chart keeps progress and its message inline');
const updated=cardFixture('Battles','uk').widget;
const oldGraph=updated._body.children.find(child=>child instanceof Graph);
let tooltipClear=false;
updated._owner.tooltip=(row,bars,sender)=>{tooltipClear=row===null&&!bars&&sender===updated;};
updated.update({...updated._state,mode:'Mini'});
ok(tooltipClear && oldGraph.parent===null && updated.panelHeight===76 &&
 updated._body.children.every(child=>!(child instanceof Graph)),'mode refresh clears the old graph and point tooltip');
const clampWidget=compile('TrackerRoot','clampWidget',{Geometry});
for(const [width,height] of [[1280,720],[1366,768],[1920,1080],[2560,1440]])for(const uiScale of [1,1.25,1.5,2]){
 for(const panelHeight of [76,106,200])for(const [x,y] of [[-100,-100],[99999,99999],[0,300],[700,0]]){
  const widget=new Sprite();Object.assign(widget,{x,y,panelWidth:272,panelHeight});
  const root={_widget:widget,_viewportWidth:width/uiScale,_viewportHeight:height/uiScale};
  clampWidget.call(root);
  const bottom=widget.y+panelHeight*widget.scaleY;
  ok(widget.x>=8 && widget.x+widget.panelWidth*widget.scaleX<=root._viewportWidth-8+1e-6,'horizontal clamp at UI scale');
  ok(widget.y>=8-1e-6 && bottom<=root._viewportHeight-8+1e-6,'inline panel fits inside viewport');
 }
}
const save=compile('TrackerSettings','save');
const finishSave=compile('TrackerSettings','finishSave');
const dismiss=compile('TrackerSettings','dismiss');
const updateSettings=compile('TrackerSettings','update');
const dirty=compile('TrackerSettings','dirty');
const applySettings=compile('TrackerRoot','applySettings');
function settingsFixture(draft){
 const sent=[],events=[];
 const owner={_saveSerial:0,applySettings,send:action=>sent.push(action),closeSettings(){events.push('closed');}};
 const state={_owner:owner,_state:null,_saveRequest:0,_draft:draft,_saveError:'',_closeAfterSave:false,dirty,dismiss,finishSave,
  draw(){events.push(['draw',this._state]);}};
 return {sent,events,state};
}
for(const close of [true,false]){
 const draft={tracker_count:2};
 const {sent,events,state}=settingsFixture(draft);
 save.call(state,close);
 ok(sent.length===1 && sent[0].request===1 && sent[0].kind==='apply' && sent[0].values===draft,
  'Apply and OK send a correlated snapshot and keep the draft');
 dismiss.call(state);
 save.call(state,close);
 updateSettings.call(state,{saveResult:{request:99,error:''}});
 ok(sent.length===1 && events.length===1 && state._draft===draft,'duplicate clicks and stale acknowledgments leave the save in flight');
 const canonical={saveResult:{request:1,error:''},categories:[{value:2}]};
 updateSettings.call(state,canonical);
 ok(!state.dirty() && state._saveRequest===0,'matching acknowledgement clears the draft');
 ok(close ? events.at(-1)==='closed' : events.at(-1)[1]===canonical,
  'OK closes after confirmation; Apply redraws authoritative state');
}
const failed=settingsFixture({tracker_count:2,hideBattles:true,hideLoadouts:true});
save.call(failed.state,true);
updateSettings.call(failed.state,{saveResult:{request:1,error:'local',retry:[]}});
ok(failed.state._draft.tracker_count===2 && failed.state._saveError==='local' && !failed.events.includes('closed'),
 'failed disk save leaves the entire draft and window open');
save.call(failed.state,true);
updateSettings.call(failed.state,{saveResult:{request:2,error:'account',retry:['hideBattles']}});
ok(Object.keys(failed.state._draft).join()==='hideBattles' && failed.state._saveError==='account' &&
 !failed.events.includes('closed'),'site failure leaves only unapplied preferences in the draft');
save.call(failed.state,true);
updateSettings.call(failed.state,{saveResult:{request:3,error:''}});
ok(!failed.state.dirty() && failed.events.at(-1)==='closed','retry acknowledges the remaining preferences');
const clean=settingsFixture({});
save.call(clean.state,false);
save.call(clean.state,true);
ok(clean.sent.length===0 && clean.events.join()==='closed','no-op OK closes and Apply sends nothing');
const {windowFixture,windowKey,press,buttons}=checkTrackerSettings({
 compile,deps,Sprite,Point,ok,modes,TrackerIcons,gradient,dirty,MouseEvent});
const suspend=compile('Widget','suspend',{MouseEvent:{MOUSE_MOVE:'move',MOUSE_UP:'up'}});
const removed=[];
const widget={stage:{removeEventListener:(...args)=>removed.push(args)},moveDrag(){},endDrag(){},_drag:{},_moved:true};
suspend.call(widget);
ok(removed.length===2 && !widget._moved && widget._drag===null,'battle/teardown clears drag listeners and state');
const key=windowKey;
const escape=compile('TrackerSettings','escape',{getTimer:()=>1000});
for(const modal of [null,'tracker_reset']){
 const calls=[],window={_modal:modal,_popup:null,_lastEscape:0,_saveRequest:0,stage:null,escape,dismiss,
  _owner:{closeSettings(){calls.push('close');}},cancelModal(){calls.push('cancel');}};
 key.call(window,{keyCode:27,stopImmediatePropagation(){calls.push('stop');}});
 ok(calls[1]===(modal?'cancel':'close'),'Escape cancels modal/draft, never confirms');
 escape.call(window);
 ok(calls.length===2,'native/AS3 duplicate Escape cannot close settings after cancelling the modal');
}
const updateVisibility=compile('TrackerRoot','updateVisibility');
const visibility={_nativeWindows:{},_inGarage:true,visible:false};
updateVisibility.call(visibility);
ok(visibility.visible,'tracker visible while in garage');
visibility._nativeWindows={lobbyMenu:true,settingsWindow:true};
updateVisibility.call(visibility);
ok(!visibility.visible,'native windows suppress tracker even during fresh state publication');
delete visibility._nativeWindows.lobbyMenu;
updateVisibility.call(visibility);
ok(!visibility.visible,'closing one native window does not show the tracker over another');
delete visibility._nativeWindows.settingsWindow;
updateVisibility.call(visibility);
ok(visibility.visible,'closing native windows restores tracker');
class Wire{constructor(text){this._text=text;this._at=0;}}
for(const name of ['read','space','stringValue']) Wire.prototype[name]=compile('Wire',name);
Wire.parse=compile('Wire','parse',{Wire});
Wire.stringify=compile('Wire','stringify').bind(Wire);
for(const value of [{uk:'Українська',tank:'Tank \\ " long\nname',arena:'19011738950705142',
 score:null,flag:true,values:[0,1e30,-1.2e-9,false,'\t\r\b😀']},[null,false,true,123.456],{empty:{},list:[]}]){
 assert.deepEqual(Wire.parse(JSON.stringify(value)),value);
 assert.deepEqual(JSON.parse(Wire.stringify(value)),value);
 assertions+=2;
}
for(const text of ['{"bad":','[1,]','{"x":NaN}','{"x":1e999}','"bad\\uXX00"','{} trailing']){
 assert.throws(()=>Wire.parse(text));assertions++;
}
if(process.argv[2]==='--preview-data'){
 const frames=modes.map((mode,i)=>{
  const {widget}=cardFixture(mode,'uk',i%2===0?'#769f50':'#8f68b2',{opacity:60});
  return {mode:labels[mode],width:widget.panelWidth,height:widget.panelHeight,body:widget._body};
 });
 fs.writeFileSync(process.argv[3],JSON.stringify(frames,(key,value)=>key==='parent'?undefined:value));
}
if(process.argv[2]==='--settings-preview-data'){
 const {window}=windowFixture('uk');
 fs.writeFileSync(process.argv[3],JSON.stringify({width:window.WIDTH,height:window.HEIGHT,body:window},
  (key,value)=>key==='parent'||key.startsWith('_')?undefined:value));
}
if(process.argv[2]==='--popups-preview-data'){
 const {window}=windowFixture('uk');
 const {window:menuWindow}=windowFixture('uk');
 Object.assign(menuWindow._state.categories[0].rows[0],{label:'Мова налаштувань',value:1});
 menuWindow.chooseCategory(0);
 press(buttons(menuWindow._content)[0]);
 const chartCards=['Trend','Battles'].map((mode,index)=>{
  const color=index?'#a481bd':'#769f50';
  const {widget}=cardFixture(mode,'uk',color,{opacity:60});
  const body=new Sprite();
  body.addChild(widget._body);
  const root={...tooltipRoot,_widget:{y:0,panelHeight:200,scaleY:1},_state:{color},_tooltip:new Sprite(),
   word:key=>key==='win'?'Перемога':key};
  const hit={...tooltipTarget,localToGlobal:point=>new Point(point.x+131,point.y+75)};
  tooltip.call(root,{time:'22.11 16:28',wnx:index?3200:1694,tankName:'Black Rock',tier:11,winnerResult:'win',
   damageDealt:3085,damageAssistedRadio:420,damageAssistedTrack:120},mode==='Battles',hit);
  body.addChild(root._tooltip);
  return body;
 });
 fs.writeFileSync(process.argv[3],JSON.stringify({settings:window,menu:menuWindow,chartCards},
  (key,value)=>key==='parent'||key.startsWith('_')?undefined:value));
}
console.log(`PASS tracker AS3 fixtures: ${assertions} assertions; 10/20/30 bars, exact hover targets, extreme/zero/gaps, Ukrainian/English controls, dynamic colors, chart footer, 4 resolutions × 4 UI scales, Apply/OK/Escape and teardown`);
