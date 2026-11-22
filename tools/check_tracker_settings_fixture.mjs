import fs from 'node:fs';

export function checkTrackerSettings({compile,deps,Sprite,Point,ok,modes,TrackerIcons,gradient,dirty,MouseEvent}){
 class SettingsControls{
  static WIDTH=520;
  constructor(window){this._window=window;this.WIDTH=SettingsControls.WIDTH;}
 }
 const Keyboard={LEFT:37,RIGHT:39,HOME:36,END:35};
 const sliderDeps={...deps,Point,Keyboard,FocusEvent:{FOCUS_IN:'focusIn',FOCUS_OUT:'focusOut'},
  Event:{REMOVED_FROM_STAGE:'removed',MOUSE_LEAVE:'leave'}};
 const sliderMethods=Object.fromEntries(['paint','beginDrag','focusChanged','moveDrag','release','detachDrag','stepAt','setIndex','adjust']
  .map(name=>[name,compile('OpacitySlider',name,sliderDeps)]));
 const initSlider=compile('OpacitySlider','OpacitySlider',sliderDeps);
 class OpacitySlider extends Sprite{
  constructor(...args){
   super();
   Object.assign(this,{START:8,stage:null,_dragStage:null,_width:0,_end:0,_options:[],_index:0,_accent:0,_changed:null});
   for(const [name,method] of Object.entries(sliderMethods))this[name]=method.bind(this);
   initSlider.apply(this,args);
  }
 }
 const sliderCast=new Proxy(OpacitySlider,{apply(_target,_this,args){return args[0];}});
 const uiDeps={...deps,SettingsControls,OpacitySlider:sliderCast,Point,int:Math.trunc,TextFieldType:{INPUT:'input'},Event:{CHANGE:'change'}};
 for(const name of ['row','segments','select','opacity','choices'])
  SettingsControls.prototype[name]=compile('SettingsControls',name,uiDeps);
 const settingsSource=fs.readFileSync(new URL('../as3/src/unicum/tracker/TrackerSettings.as',import.meta.url),'utf8');
 const dimensions=Object.fromEntries([...settingsSource.matchAll(/const (WIDTH|HEIGHT|VIEW_HEIGHT|CHOICE_COUNT|CHOICE_ROW):int = (\d+);/g)]
  .map(([,key,value])=>[key,Number(value)]));
 const trackerWords=Object.fromEntries([...fs.readFileSync(new URL('../src/unicum/tracker/localize.py',import.meta.url),'utf8')
  .matchAll(/'([^'\n]+)': u'([^'\n]+)'/g)].map(([,key,value])=>[key,value]));
 const windowMethods={};
 for(const name of ['draw','drawSaveStatus','chooseCategory','tabButton','closePopup','scrollTo','openChoices','drawChoices',
  'choiceButton','confirmation','action','cancelModal','accent','value','change'])
  windowMethods[name]=compile('TrackerSettings',name,uiDeps);
 function windowFixture(locale,color='#a481bd'){
  const word=key=>locale==='uk'?trackerWords[key]??key:key;
  const row=(kind,variable,label,extra)=>({kind,var:variable,label:word(label),group:'',...extra});
  const trackerRows=[
   row('dropdown','tracker_mode','Display mode',{options:modes.map(word),value:2,offset:0}),
   row('dropdown','tracker_count','Random battles in window',{options:['10','20','30'],value:1,offset:0}),
   row('dropdown','tracker_opacity','Background opacity',{options:['40%','50%','60%','70%','80%','90%'],value:2,offset:0}),
   row('button','tracker_reset','Reset statistics...',{word:word('Reset'),danger:true}),
   row('button','tracker_position','Reset position',{word:word('Restore')}),
   row('text',undefined,word('Expected values')+' · 2026-11-22')
  ];
  const categories=[
   {title:word('General'),rows:[row('dropdown','settingsLanguage','Settings language',{options:['English','Українська'],value:0,offset:0})]},
   {title:word('WNX Tracker'),rows:trackerRows},
   {title:word('Battle'),rows:[
    ...['loading','panel','tab'].map(surface=>row('dropdown','wnx_'+surface+'_opacity','Background opacity',
     {options:Array.from({length:11},(_,i)=>i*10+'%'),value:6,offset:0})),
    ...Array.from({length:12},(_,i)=>row('checkbox','battle'+i,'WNX',{value:i===0}))
   ]},
   {title:word('Garage'),rows:[]}
  ];
  const sent=[],window=new Sprite();
  Object.assign(window,dimensions,windowMethods,{_state:{categories,color},_owner:{word,send:action=>sent.push(action)},_category:1,
   _scroll:0,_limit:0,_popup:null,_modal:null,_choice:null,_choiceStart:0,_choicePoint:null,_choiceBottom:0,_content:null,_viewport:null,
   _apply:null,_saveRequest:0,_saveError:'',_draft:{},dismiss(){sent.push('cancel');},save(close){sent.push(close);},dirty});
  for(const name of Object.keys(windowMethods)) window[name]=window[name].bind(window);
  window.draw();
  return {window,sent};
 }
 function press(button){button.handlers.click({stopPropagation(){}});}
 function buttonLabel(button){return button.children[0]?.value;}
 function buttons(parent){return parent.children.filter(child=>child.handlers?.click);}
 function fill(sprite){return sprite.ops.find(op=>op[0]==='fill')?.[1];}
 function drawnButtonsFit(parent,width,height){
  return buttons(parent).every(child=>{
   const [, , , w,h]=child.ops.find(op=>op[0]==='round');
   const field=child.children[0];
   return child.x>=0 && child.y>=0 && child.x+w<=width && child.y+h<=height &&
    (!field || (field.textWidth+4<=field.width && field.y+field.height<=h));
  });
 }
 for(const locale of ['en','uk']){
  const {window,sent}=windowFixture(locale);
  ok(drawnButtonsFit(window,window.WIDTH,window.HEIGHT),'localized navigation and footer fit the settings window');
  ok(window.children.some(child=>child.icon===TrackerIcons.SETTINGS),'settings header shares the native gear');
  const rowButtons=buttons(window._content);
  ok(drawnButtonsFit(window._content,SettingsControls.WIDTH,window.VIEW_HEIGHT),'localized tracker option and action buttons fit');
  ok(rowButtons.filter(button=>button.ops.some(op=>op[0]==='line')).map(buttonLabel).join()===
   [locale==='uk'?'Тренд':'Trend','20'].join(),'the current mode and count are distinctly selected');
  const slider=window._content.children.find(child=>child instanceof OpacitySlider);
  ok(rowButtons.length===9 && slider.children[0].value==='60%' && window._limit===0,
   'the slider and other controls are visible without Tracker scrolling');
  slider.adjust(Keyboard.END);
  ok(window._draft.tracker_opacity===5 && window._apply.alpha===1 && slider.children[0].value==='90%',
   'the slider keeps the canonical index in the draft and updates the readout');
  const reset=buttons(window._content).find(child=>fill(child)===0x642c32);
  press(reset);
  const dialog=window._popup.children[0];
  ok(window._modal==='tracker_reset' && drawnButtonsFit(dialog,528,278),'destructive action opens a bounded confirmation');
  press(buttons(dialog)[1]);
  ok(window._popup===null && sent.length===0,'cancel in the confirmation does not reset');
  press(buttons(window).at(-2));press(buttons(window).at(-1));
  ok(sent.join()==='false,true','Apply and OK retain their distinct actions');
  window.chooseCategory(0);
  press(buttons(window._content)[0]);
  const menu=window._popup.children[0];
  ok(menu.x+520<=window.WIDTH && menu.y===165 && drawnButtonsFit(menu,520,72),'general dropdown fits below its field');
  ok(gradient(menu.children[0]) && gradient(buttons(menu)[0]),'dropdown and selected option use the raised glass palette');
  press(buttons(menu)[1]);
  ok(window._draft.settingsLanguage===1 && window._popup===null,'normal dropdown still edits the draft');
  window.openChoices({var:'fixtureList',offset:0,value:0,options:Array.from({length:11},(_,i)=>String(i+1))},
   new Point(208,415),445);
  const longMenu=window._popup.children[0];
  ok(longMenu.y+192<415 && buttons(longMenu).length===6 && longMenu.children[0].ops.some(op=>op[0]==='round'&&op[3]===2),
   'long dropdown flips above the field and displays a scrollbar');
  window._popup.handlers.wheel({delta:-3,stopImmediatePropagation(){}});
  ok(buttonLabel(buttons(window._popup.children[0])[0])==='4','scroll exposes more options without changing the draft');
  window.closePopup();
  window.chooseCategory(2);
  const battleSliders=window._content.children.filter(child=>child instanceof OpacitySlider);
  battleSliders[0].adjust(Keyboard.HOME);
  battleSliders[2].adjust(Keyboard.END);
  ok(battleSliders.length===3 && battleSliders[0].children[0].value==='0%' && battleSliders[2].children[0].value==='100%' &&
   window._draft.wnx_loading_opacity===0 && window._draft.wnx_tab_opacity===10,
   'battle surface sliders retain the distinct 0–100% ranges');
  window.scrollTo(655);
  ok(window._scroll===window._limit && window._content.y===-window._limit && window._limit>0,'long categories can scroll to the bottom');
 }
 const purpleSettings=windowFixture('uk').window,greenSettings=windowFixture('uk','#789d62').window;
 ok(gradient(purpleSettings.children[0])[2][1]!==gradient(greenSettings.children[0])[2][1] &&
  gradient(purpleSettings._apply)[2][1]!==gradient(greenSettings._apply)[2][1],
  'window and Apply colors follow the rating tint');
 ok(purpleSettings.children[0].filters.length===1 && purpleSettings.children[0].mouseEnabled===false,
  'settings has one non-interactive shadow behind its controls');
 ok(buttons(greenSettings._content).some(child=>fill(child)===0x642c32),'reset fill stays red independent of theme');
 const dragWindow=windowFixture('uk').window;
 dragWindow.scaleX=dragWindow.scaleY=1.5;
 const dragSlider=dragWindow._content.children.find(child=>child instanceof OpacitySlider);
 const capture=new Map();
 dragSlider.stage={
  focus:null,
  addEventListener(type,fn,useCapture=false){capture.set(type,[fn,useCapture]);},
  removeEventListener(type,fn,useCapture=false){
   const listener=capture.get(type);
   if(listener?.[0]===fn && listener[1]===useCapture) capture.delete(type);
  }
 };
 function dragEvent(x){
  const point=dragSlider.localToGlobal({x,y:16});
  return {stageX:point.x,stageY:point.y,stopPropagation(){}};
 }
 dragSlider.handlers.down(dragEvent(8));
 ok(dragSlider.stage.focus===dragSlider && capture.get('move')[1] && dragSlider.children[0].value==='40%',
  'clicking the rail sets focus and snaps to the minimum at non-default UI scale');
 capture.get('move')[0](dragEvent(161));
 ok(dragSlider.children[0].value==='70%','drag snaps to the nearest ten-percentage-point step');
 capture.get('up')[0](dragEvent(280));
 ok(!capture.size && dragSlider.children[0].value==='90%','release outside the rail clamps and clears stage listeners');
 dragSlider.handlers.down(dragEvent(8));
 dragSlider.handlers.removed();
 ok(!capture.size,'removal during an active drag clears stage listeners');
 dragSlider.handlers.down(dragEvent(8));
 capture.get('leave')[0]();
 ok(!capture.size,'leaving the game window clears stage listeners');
 const windowKey=compile('TrackerSettings','key',{Sprite,InteractiveObject:class{},MouseEvent,OpacitySlider:sliderCast});
 let consumed=false;
 dragWindow.stage=dragSlider.stage;
 dragWindow.contains=target=>target===dragSlider;
 windowKey.call(dragWindow,{keyCode:Keyboard.RIGHT,preventDefault(){},stopImmediatePropagation(){consumed=true;}});
 ok(consumed && dragSlider.children[0].value==='50%','the settings key dispatcher routes arrows to the focused slider');
 return {windowFixture,windowKey,press,buttons};
}
