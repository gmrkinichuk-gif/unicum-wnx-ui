// Execute actual AS3 bodies with display/event fixtures. This is not a live GFx test.
import fs from 'node:fs';
import assert from 'node:assert/strict';
let assertions=0;
function ok(value,message){assert.ok(value,message);assertions++;}
function method(file,name){
 const source=fs.readFileSync(new URL('../as3/src/unicum/tracker/'+file+'.as',import.meta.url),'utf8');
 const found=source.match(new RegExp(`(?:public|private)(?: static)? function ${name}\\(([\\s\\S]*?)\\)(?: : [\\w*]+)?\\s*\\{([\\s\\S]*?)\\n      \\}`));
 assert.ok(found,`${file}.${name}`);
 const strip=s=>s.replace(/:\s*(?:Wire|Number|String|Boolean|Object|Array|Function|Sprite|MouseEvent|TextField|Point|Rectangle|TrackerRoot|Event|KeyboardEvent|InteractiveObject|DisplayObjectContainer|DisplayObject|int|uint|void|\*)(?=\s*[,)=;{]|\s+in\b|\s*$)/g,'')
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
   beginFill(...a){ops.push(['fill',...a]);},endFill(){},drawRect(...a){ops.push(['rect',...a]);},
   moveTo(...a){ops.push(['move',...a]);},lineTo(...a){ops.push(['line',...a]);},drawCircle(...a){ops.push(['circle',...a]);}};}
 addChild(child){this.children.push(child);child.parent=this;return child;}
 addEventListener(type,fn){this.handlers[type]=fn;}
}
class Rectangle{constructor(x,y,width,height){Object.assign(this,{x,y,width,height});}}
const Glass={text(){},number:compile('Glass','number'),mix:(a,b,k)=>b};
const MouseEvent={MOUSE_OVER:'over',MOUSE_OUT:'out'};
const deps={Sprite,Rectangle,Geometry,Glass,uint:x=>Number(x)>>>0,MouseEvent};
const bind=compile('Graph','bind',deps);
const construct=compile('Graph','Graph',deps);
for(const count of [10,20,30])for(const bars of [true,false]){
 const values=Array.from({length:count},(_,i)=>({tankName:`Tank ${i}`,wnx:i===3?null:i===4?0:i===5?300000:i*330,color:'#83579d'}));
 const graph=new Sprite();graph.WIDTH=300;graph.HEIGHT=76;graph.bind=bind;
 const hovers=[];construct.call(graph,values,bars,0x83579d,(row,isBar)=>hovers.push([row,isBar]));
 const plot=graph.children[0];
 ok(plot.scrollRect.width===300 && plot.scrollRect.height===76,'plot clipped');
 ok(plot.children.length===count,'each position has a distinct hit area');
 for(let i=0;i<count;i++){
  const hit=plot.children[i],rect=hit.ops.find(op=>op[0]==='rect');
  ok(Math.abs(hit.x-i*300/count)<1e-9 && rect[1]===0 && Math.abs(rect[3]-300/count)<1e-9,'nonoverlapping step-bounded hit zones');
  hit.handlers.over({});
  ok(hovers.at(-1)[0]===values[i],'hover identifies the exact tank/point');
  hit.handlers.out({});ok(hovers.at(-1)[0]===null,'hover exit clears tooltip');
 }
 if(bars){
  const rects=plot.ops.filter(op=>op[0]==='rect');
  ok(rects.length===count,'all bars, including explicit unavailable marker, retained');
  for(let i=0;i<count;i++){
   const [,x,y,w,h]=rects[i];
   ok(x>=i*300/count && x+w<=(i+1)*300/count+1e-9 && w<300/count,'positive bar gap');
   ok(y>=0 && y+h<=76 && Number.isFinite(h),'zero/extreme/missing heights fit plot');
  }
 }
}
const placeDetails=compile('Widget','placeDetails');
const clampWidget=compile('TrackerRoot','clampWidget',{Geometry});
for(const [width,height] of [[1280,720],[1366,768],[1920,1080],[2560,1440]])for(const uiScale of [1,1.25,1.5,2]){
 for(const expanded of [false,true])for(const panelHeight of [66,100,202])for(const [x,y] of [[-100,-100],[99999,99999],[0,300],[700,0]]){
  const widget=new Sprite();Object.assign(widget,{x,y,panelWidth:320,panelHeight,_expanded:expanded,_details:{},totalHeight:panelHeight+(expanded?160:0)});
  widget.placeDetails=placeDetails;
  const root={_widget:widget,_viewportWidth:width/uiScale,_viewportHeight:height/uiScale};
  clampWidget.call(root);
  const top=widget.y+(expanded?Math.min(0,widget._details.y)*widget.scaleY:0);
  const bottom=widget.y+(expanded?Math.max(panelHeight,widget._details.y+156):panelHeight)*widget.scaleY;
  ok(widget.x>=8 && widget.x+widget.panelWidth*widget.scaleX<=root._viewportWidth-8+1e-6,'horizontal clamp at UI scale');
  ok(top>=8-1e-6 && bottom<=root._viewportHeight-8+1e-6,'expanded panel fits above/below viewport');
 }
}
const save=compile('TrackerSettings','save');
for(const close of [true,false]){
 const sent=[],state={_owner:{send:x=>sent.push(x),closeSettings(){sent.push('closed');}},_draft:{tracker_count:2},draw(){sent.push('draw');}};
 save.call(state,close);
 assert.deepEqual(sent[0],{kind:'apply',values:{tracker_count:2}});
 assert.deepEqual(state._draft,{});
 ok(sent[1]===(close?'closed':'draw'),'OK closes; Apply stays open');
}
const suspend=compile('Widget','suspend',{MouseEvent:{MOUSE_MOVE:'move',MOUSE_UP:'up'}});
const removed=[];
const widget={stage:{removeEventListener:(...args)=>removed.push(args)},moveDrag(){},endDrag(){},_drag:{},_pinned:true,_expanded:true};
suspend.call(widget);
ok(removed.length===2 && !widget._pinned && !widget._expanded && widget._drag===null,'battle/teardown clears drag and pinned details');
const key=compile('TrackerSettings','key',{Sprite,InteractiveObject:class{},MouseEvent});
const escape=compile('TrackerSettings','escape',{getTimer:()=>1000});
for(const modal of [null,'tracker_reset']){
 const calls=[],window={_modal:modal,_popup:null,_lastEscape:0,escape,_owner:{closeSettings(){calls.push('close');}},cancelModal(){calls.push('cancel');}};
 key.call(window,{keyCode:27,stopImmediatePropagation(){calls.push('stop');}});
 ok(calls[1]===(modal?'cancel':'close'),'Escape cancels modal/draft, never confirms');
 escape.call(window);
 ok(calls.length===2,'native/AS3 duplicate Escape cannot close settings after cancelling the modal');
}
const buttonSource=fs.readFileSync(new URL('../as3/src/unicum/tracker/Glass.as',import.meta.url),'utf8');
ok(buttonSource.includes('danger ? 0x642c32'),'reset fill stays red independent of theme');
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
console.log(`PASS tracker AS3 fixtures: ${assertions} assertions; 10/20/30 bars, exact hover targets, extreme/zero/gaps, 4 resolutions × 4 UI scales, expanded bounds, Apply/OK/Escape and teardown`);
