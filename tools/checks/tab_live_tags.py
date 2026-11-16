"""Native-shaped Live Tags and browser checks for late client bindings.

The fixture simulates client visibility changes, not server leader selection.
Class names, bindings, tooltip ancestry and icons come from 2.4.1.1 It/Du/uu.
"""
import base64
import glob
import os
import zipfile


ICONS = (('damage', 'd4cee', 'c9faa'), ('assist', 'c9cc2', 'ae6d8'),
         ('block', 'fe9e6', 'bb531'))


def markup():
    icons = []
    for kind, ally, current in ICONS:
        for own, suffix in ((False, ally), (True, current)):
            classname = 'LiveTag_liveTag_%s%s_%s' % ('current__' if own else '', kind, suffix)
            binding = '{{item.value.liveTag%s}} && %s{{item.value.isCurrentPlayer}}' % (
                kind.title(), '' if own else '!')
            icons.append('<div class="%s" data-qa-kind="%s" data-qa-own="%s" '
                         'data-bind-if="%s" style="display:none"></div>' %
                         (classname, kind, 'yes' if own else 'no', binding))
    return ('<div data-bind-if="{{model.playerList.isLiveTagsEnabled}}">'
            '<div class="LiveTag_liveTag_background_e4ec0"></div>'
            '<div class="LiveTag_liveTag__wrapper_f2eca" style="display:none" '
            'data-bind-if="{{item.value.liveTagDamage}} || {{item.value.liveTagAssist}} || {{item.value.liveTagBlock}}">'
            '<div class="PrimitiveTooltip_base_a77fb">'
            '<div class="LiveTag_tooltip_trigger_d3dfe">' + ''.join(icons) + '</div>'
            '<div class="PrimitiveTooltip_body_d49ba">'
            '<div class="PrimitiveTooltip_header_c4120" data-bind-value="{{item.value.liveTagTooltipTitle}}">Native leader</div>'
            '<div class="PrimitiveTooltip_content_c17a0" data-bind-value="{{item.value.liveTagTooltipBody}}">Native contribution tooltip</div>'
            '</div></div></div></div>')


def icon_css(game):
    """Resolve native R.images only for Edge; the game resolves its own URLs."""
    images = {}
    for path in glob.glob(os.path.join(game, 'res', 'packages', 'gui*.pkg')):
        with zipfile.ZipFile(path) as package:
            for name in package.namelist():
                if '/liveTags/' in name and name.endswith('.png'):
                    images[os.path.splitext(os.path.basename(name))[0]] = base64.b64encode(package.read(name)).decode('ascii')
    rules = []
    for kind, ally, current in ICONS:
        for own, suffix in ((False, ally), (True, current)):
            classname = 'LiveTag_liveTag_%s%s_%s' % ('current__' if own else '', kind, suffix)
            key = kind + ('CurrentPlayer' if own else 'Ally')
            rules.append('.%s{background-image:url(data:image/png;base64,%s)}' % (classname, images[key]))
    return ''.join(rules)


BROWSER_CHECKS = r"""
const liveRecords=Array.from(document.querySelectorAll('[data-qa^="allies-"]')).map(row=>{
  const live=row.querySelector('[class*="LiveTag_liveTag__wrapper_"]');
  let host=live;
  while(host.parentElement!==row) host=host.parentElement;
  return {row,live,host,parent:live.parentElement,icons:Array.from(live.querySelectorAll('[data-qa-kind]')),
    tooltip:live.querySelector('[class*="PrimitiveTooltip_body_"]'),
    bindings:Array.from(host.querySelectorAll('[data-bind-if],[data-bind-value]')).map(n=>[n,n.getAttribute('data-bind-if'),n.getAttribute('data-bind-value')])};
});
const liveEvidence=[];
function liveCycle(errors,done){
  function verifyRecord(record,enabled,kinds,current){
    const {row,live,host,icons}=record;
    if(live.parentElement!==record.parent || host.parentElement!==row) errors.push('native live-tag ancestry moved');
    if(!host.classList.contains('unicum-roster-live-host')) errors.push('hidden native root was not prepared before client data');
    for(const [node,condition,value] of record.bindings) if(node.getAttribute('data-bind-if')!==condition || node.getAttribute('data-bind-value')!==value) errors.push('native live-tag binding changed');
    const visibleIcons=icons.filter(n=>n.getBoundingClientRect().width>0);
    if(visibleIcons.length!==(enabled?kinds.length:0)) errors.push('native icon visibility overridden');
    for(const icon of visibleIcons){
      const box=icon.getBoundingClientRect(), rowBox=row.getBoundingClientRect();
      if(box.width!==16 || box.height!==16) errors.push('native icon size changed');
      if(box.left<rowBox.left || box.right>rowBox.right || box.top<rowBox.top || box.bottom>rowBox.bottom) errors.push('native leader icon clipped '+JSON.stringify({row:row.dataset.qa,icon:[box.left,box.top,box.right,box.bottom],bounds:[rowBox.left,rowBox.top,rowBox.right,rowBox.bottom]}));
      const hit=document.elementFromPoint(box.left+box.width/2,box.top+box.height/2);
      if(hit!==icon) errors.push('native leader icon covered or tooltip hit target lost');
      for(const selector of ['.unicum-roster-stats','[class*="UserInfo_nickname_wrapper_"]','[class*="Player_vehicleContour_ed"]','[class*="Player_vehicleNameWrapper_"]']){
        const b=row.querySelector(selector).getBoundingClientRect();
        if(box.left<b.right && box.right>b.left && box.top<b.bottom && box.bottom>b.top) errors.push('native leader icon overlaps '+selector);
      }
      if(getComputedStyle(icon).backgroundImage.indexOf('data:image/png')<0) errors.push('native leader image missing');
    }
    if(!enabled && host.getBoundingClientRect().width!==0) errors.push('disabled client live tags reserve space');
    if(enabled && host.getBoundingClientRect().width!==52) errors.push('native leader column width');
    if(!live.contains(record.tooltip) || !record.tooltip.textContent.includes('Native contribution tooltip')) errors.push('native tooltip lost');
  }
  const steps=[{enabled:true,kinds:['damage']},{enabled:true,kinds:['assist']},
    {enabled:true,kinds:['block']},{enabled:true,kinds:['damage','assist','block']},
    {enabled:true,kinds:[]},{enabled:false,kinds:['damage','assist','block']}];
  let index=0;
  function step(){
    const state=steps[index++];
    liveRecords.forEach((record,i)=>{
      const current=i===4;
      record.host.style.display=state.enabled?'':'none';
      record.live.style.display=state.kinds.length?'':'none';
      for(const icon of record.icons) icon.style.display=state.kinds.includes(icon.dataset.qaKind) && (icon.dataset.qaOwn==='yes')===current?'':'none';
      // Inspect immediately after the client's binding, before the next mod
      // timer. The old conditional absolute-position correction missed this.
      verifyRecord(record,state.enabled,state.kinds,current);
    });
    liveEvidence.push({enabled:state.enabled,kinds:state.kinds,rows:liveRecords.length});
    setTimeout(()=>{liveRecords.forEach((r,i)=>verifyRecord(r,state.enabled,state.kinds,i===4));if(index<steps.length)step();else {
      liveRecords.forEach((record,i)=>{
        record.host.style.display='';record.live.style.display='';
        for(const icon of record.icons) icon.style.display=(icon.dataset.qaOwn==='yes')===(i===4)?'':'none';
      });
      done();
    }},250);
  }
  step();
}
"""
