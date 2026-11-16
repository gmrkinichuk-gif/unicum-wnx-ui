"""Browser geometry check of actual Tab CSS/JS, without starting WoT.

Uses developer-supplied client CSS and native-shaped nodes.
It cannot establish Gameface or Scaleform behavior in a running game.
"""
import html
import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path
from checks.tab_live_tags import markup as live_markup, icon_css, BROWSER_CHECKS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/unicum/web/battle'
OUT = ROOT / 'build/checks/roster-layout'
CLIENT_CSS = None
GAME = None
EDGE = Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')


def fixture(baseline=None):
    names = ['Short', 'Average_Nickname_0857', 'Maximum_length_player_name_With_Clan',
             'ClanOnlyRegression', 'NoRating', 'Hidden_Player', 'NoClan', 'LiveTagPlayer']
    colours = ['#7a4fb2', '#4a92b7', '#5c9f48', '#c6a72c', None, None, '#c55b3d', '#5c9f48']
    players, teams = {}, []
    for side in ['allies', 'enemies']:
        rows = []
        for index, name in enumerate(names + names[:7]):
            i = index % len(names)
            nick = html.escape(name)
            clan = '' if i in (0, 6) else '[LONGCLANTAG]'
            badge = '<div class="UserInfo_badge_b0d39">B</div>' if i % 2 else ''
            hidden = (f'<div data-bind-value="{{{{item.value.hiddenUserName}}}}">{nick}</div>' if i == 5
                      else f'<div class="UserInfo_userName_ff8dc"><div class="UserInfo_tooltip_trigger_e6ce7">{nick}</div></div>')
            user = f'<div class="UserInfo_user_info_ee23d {("UserInfo_user_info__right_d5b63" if side == "enemies" else "")}">{badge}<div class="UserInfo_nickname_wrapper_af103"><div class="UserInfo_userNameWrapper_ddc08">{hidden}</div><div class="UserInfo_clanTag_f913f">{clan}</div></div></div>'
            # Preserve the native absolute LiveTag ancestry from Du/It in TabView.js.
            live = live_markup() if side == 'allies' else ''
            rows.append(f'<div class="Player_base_fe348" data-qa="{side}-{index}">{live}<div class="Player_platoon_wrapper_acdb5"><button>+</button></div>{user}<div class="Player_vehicleNameWrapper_f1c80"><div class="Player_vehicleName_aa673">Very long vehicle name</div></div><div class="Player_vehicleType_e6ff5">◆</div><div class="Player_chatIndicators_b56cd"></div><div class="Player_vehicleContour_ed4d4"><div class="Player_vehicleContour_wrapper_bc8e4"><div class="Player_vehicleContour_image_a35ee">▰</div><div class="Player_vehicleContour_level_f720e">VIII</div></div></div><div class="Player_kills_bc5c1">2</div><div class="Player_playerStatus_e6e86">⚔</div></div>')
            players[name] = {'wnxAvailable': colours[i] is not None, 'bandColor': colours[i]}
            if colours[i]:
                players[name].update(wnx=[3400, 2180, 1450, 980, 0, 0, 600, 12345][i], winrate='62.4%', battles='160.3k')
        direction = 'Player_right_da422' if side == 'enemies' else ''
        teams.append(f'<div class="FullStatsApp_{side}_{('f0875' if side == 'allies' else 'd1768')} {direction}">'+''.join(rows)+'</div>')
    native_css = CLIENT_CSS.read_text(encoding='utf-8')
    style = (SOURCE/'tab_screen.css').read_text(encoding='utf-8')
    if re.search(r':not\s*\(', style, re.I):
        raise AssertionError('Mod CSS must not use unsupported Coherent negation selectors')
    script = (SOURCE/'tab_screen.js').read_text(encoding='utf-8')
    if baseline:
        with zipfile.ZipFile(baseline) as package:
            script = package.read('res/scripts/client/unicum/web/battle/tab_screen.js').decode('utf-8')
            style = package.read('res/scripts/client/unicum/web/battle/tab_screen.css').decode('utf-8')
    data = {'redesignEnabled': True, 'shown': True, 'indicatorEnabled': True, 'players': players}
    body = '<div class="FullStatsApp_view_f1db1"><div class="FullStatsApp_fullStats_edb96"><div class="FullStatsApp_fullStats_header_a7205"><div>Allies</div><div>Enemies</div></div><div class="FullStatsApp_teams_ab459">'+''.join(teams)+'</div></div></div><pre id="qa-result"></pre>'
    verify = """
const ownRow=document.querySelector('[data-qa="allies-4"]');
ownRow.classList.add('Player_base__current_b9e88');
setTimeout(() => {
 const errors = [], metrics = [];
 function deathCycle(done) {
   const records=['allies-0','enemies-0'].map(id=>{
     const row=document.querySelector('[data-qa="'+id+'"]');
     return {row,icon:row.querySelector('[class*=Player_vehicleContour_ed]'),stats:row.querySelector('.unicum-roster-stats'),
       image:row.style.backgroundImage,color:row.style.backgroundColor,shadow:row.style.boxShadow,left:row.style.borderLeftColor,right:row.style.borderRightColor};
   });
   records.forEach(record=>{record.iconHTML=record.icon.outerHTML;record.row.classList.add('Player_base__killed_e2818');});
   setTimeout(()=>{
     for(const record of records){
       const row=record.row;
       if(row.style.backgroundImage!==record.image || row.style.backgroundColor!==record.color) errors.push('death lost WNX fill '+row.dataset.qa);
       const wash=getComputedStyle(row).boxShadow;
       if(wash.indexOf('rgba(160, 25, 30, 0.24)')<0 || wash.indexOf('inset')<0) errors.push('dead row missing translucent red wash '+row.dataset.qa);
       if(row.style.borderLeftColor!==record.left || row.style.borderRightColor!==record.right) errors.push('death changed WNX border '+row.dataset.qa);
       if(record.icon.outerHTML!==record.iconHTML || row.querySelector('[class*=Player_vehicleContour_ed]')!==record.icon) errors.push('death replaced native icon '+row.dataset.qa);
       if(row.querySelector('.unicum-roster-stats')!==record.stats || row.querySelectorAll('.unicum-roster-stats').length!==1) errors.push('death duplicated stats '+row.dataset.qa);
       row.classList.remove('Player_base__killed_e2818');
     }
     setTimeout(()=>{
       for(const record of records){
         const row=record.row;
         if(row.style.backgroundImage!==record.image || row.style.backgroundColor!==record.color) errors.push('revival did not restore WNX fill '+row.dataset.qa);
         if(row.style.boxShadow!==record.shadow) errors.push('revival left the red wash behind '+row.dataset.qa);
         if(record.icon.outerHTML!==record.iconHTML || row.querySelector('.unicum-roster-stats')!==record.stats) errors.push('revival replaced native node '+row.dataset.qa);
       }
       done();
     },250);
   },250);
 }
 for (const node of Array.from(document.querySelectorAll('[class*="FullStatsApp_fullStats_"]'))) {
   const native=node.getAttribute('class') || '';
   const wanted=native.indexOf('header')<0 && native.indexOf('list')<0;
   if(node.classList.contains('unicum-roster-content')!==wanted) errors.push('content positive-class filtering');
 }
 for (const node of Array.from(document.querySelectorAll('[class*="Player_vehicleContour_"]'))) {
   const native=node.getAttribute('class') || '';
   const wanted=['wrapper','image','level','voice'].every(part=>native.indexOf(part)<0);
   if(node.classList.contains('unicum-roster-contour')!==wanted) errors.push('contour positive-class filtering');
 }
 const box = node => node.getBoundingClientRect();
 const intersect = (a,b) => Math.min(a.right,b.right)-Math.max(a.left,b.left)>1 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1;
 for (const row of Array.from(document.querySelectorAll('[data-qa]'))) {
   const style=getComputedStyle(row);
   const enemy=row.dataset.qa.indexOf('enemies')===0;
   if(parseFloat(enemy?style.borderRightWidth:style.borderLeftWidth)!==4 || parseFloat(enemy?style.borderLeftWidth:style.borderRightWidth)!==0) errors.push('stripe mirror '+row.dataset.qa);
   const medal=row.querySelector('[class*=UserInfo_badge_]');
   if(medal && Math.abs(box(medal).top+box(medal).height/2-box(row).top-box(row).height/2)>1) errors.push('medal not centred '+row.dataset.qa);
   const user = row.querySelector('[class*=UserInfo_user_info_]');
   const stats = row.querySelector('.unicum-roster-stats');
   const name = row.querySelector('[class*=UserInfo_userNameWrapper_]');
   const tank = row.querySelector('[class*=Player_vehicleNameWrapper_]');
   const icon = row.querySelector('[class*=Player_vehicleContour_ed]');
   const nickArea = row.querySelector('[class*=UserInfo_nickname_wrapper_]');
   const objects = [nickArea, stats, tank, icon].map(box);
   for(let i=0;i<objects.length;i++) for(let j=i+1;j<objects.length;j++) if(intersect(objects[i],objects[j])) errors.push(row.dataset.qa+' overlapping areas '+i+'/'+j);
   if(box(row).left<0 || box(row).right>innerWidth) errors.push('outside viewport '+row.dataset.qa);
   if(box(stats).height>box(row).height) errors.push('wrapped stats '+row.dataset.qa);
   if(box(name).width<30 && name.textContent.length>5) errors.push('collapsed name '+row.dataset.qa);
   if(!originalNames.includes(name.textContent)) errors.push('nickname source mutated '+name.textContent);
   const nickText=row.querySelector('[class*="UserInfo_userName_"] > [class*="UserInfo_tooltip_trigger_"], [data-bind-value*=".hiddenUserName"]');
   if(row===ownRow && getComputedStyle(nickText).color!=='rgb(240, 183, 95)') errors.push('current player native gold not preserved');
   if(row===ownRow) for(const element of [row.querySelector('[class*="UserInfo_clanTag_"]'),row.querySelector('[class*="Player_vehicleName_"]'),stats,...stats.children]) {
     if(getComputedStyle(element).color!=='rgb(240, 183, 95)') errors.push('current clan/vehicle/stat not native gold');
   }
   if(row!==ownRow && getComputedStyle(nickText).color!=='rgb(242, 243, 245)') errors.push('other player colour changed');
   if(stats.parentElement!==user) errors.push('stats not beside nickname '+row.dataset.qa);
   const live=row.querySelector('[class*=LiveTag_liveTag__wrapper_]');
   if(live){
     if(!row.querySelector('.unicum-roster-live-host')) errors.push('native Live Tags host missing '+row.dataset.qa);
     if(!live.querySelector('[class*="PrimitiveTooltip_body_"]')) errors.push('native live-tag tooltip lost');
   }
   metrics.push({row:row.dataset.qa,nameWidth:box(name).width,userWidth:box(user).width,statsWidth:box(stats).width});
 }
 if(document.querySelectorAll('.unicum-roster-stats').length!==document.querySelectorAll('[data-qa]').length) errors.push('duplicated/missing stats');
 const old = JSON.parse(api.model.model.data);
 const firstIcon = document.querySelector('[class*=Player_vehicleContour_ed]');
 const oldIcon = firstIcon.outerHTML;
 const originalCount = document.querySelectorAll('[data-qa]').length;
 const changed = JSON.parse(api.model.model.data);
 changed.players.Short.wnx = 7777;
 api.model.model.data = JSON.stringify(changed);
 setTimeout(() => {
   const first = document.querySelector('.unicum-roster-stats');
   if(!first.textContent.includes('7 777')) errors.push('late update did not redraw');
   if(document.querySelectorAll('.unicum-roster-stats').length !== originalCount) errors.push('update duplicated rows');
   if(firstIcon.outerHTML !== oldIcon) errors.push('native icon mutated');
   liveCycle(errors,()=>{deathCycle(()=>{
   part.stop();
   if(document.querySelectorAll('.unicum-roster-stats,.unicum-roster-live-slot,.unicum-roster-live-host,.unicum-roster-live-tag,.unicum-roster-row,.unicum-roster-view,.unicum-roster-content,.unicum-roster-contour').length) errors.push('teardown leaked decoration');
   api.model.model.data=JSON.stringify(old);
   part=(new Function('api',source))(api);
   document.querySelector('#qa-result').textContent=JSON.stringify({errors,metrics,liveEvidence,viewport:innerWidth,maxPollMs:Math.max(...pollTimes)});
   });});
 },250);
},600);
"""
    overrides = 'html{font-size:1px} body{margin:0;font:13px Arial;background:#777} .FullStatsApp_view_f1db1{padding-top:120px} .Player_vehicleContour_image_a35ee{color:white} #qa-result{font:10px monospace;position:absolute;top:800px;color:white;max-width:100%;white-space:pre-wrap} button{width:20px}'
    compatibility = 'Object.defineProperty(CSSStyleDeclaration.prototype,"getPropertyPriority",{value:undefined,configurable:true});Object.defineProperty(Node.prototype,"isConnected",{value:undefined,configurable:true});Object.defineProperty(NodeList.prototype,Symbol.iterator,{value:undefined,configurable:true});'
    instrumentation = 'const pollTimes=[];const nativeInterval=window.setInterval;window.setInterval=(fn,delay)=>nativeInterval(()=>{const t=performance.now();fn();pollTimes.push(performance.now()-t)},delay);'
    images = icon_css(str(GAME))
    return '<!doctype html><meta charset="utf-8"><style>'+native_css+style+overrides+images+'</style>'+body+'<script>const originalNames='+json.dumps(names)+';const api={model:{model:{data:'+json.dumps(json.dumps(data))+'}},report:console.log};const source='+json.dumps(script)+';'+compatibility+instrumentation+'let part=(new Function("api",source))(api);'+BROWSER_CHECKS+verify+'</script>'


def main():
    global OUT, CLIENT_CSS, GAME, EDGE
    parser = argparse.ArgumentParser()
    parser.add_argument('--client-css', type=Path, required=True)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--browser', type=Path, default=EDGE)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--width', type=int, action='append')
    args = parser.parse_args()
    CLIENT_CSS, GAME, EDGE = args.client_css, args.game, args.browser
    if args.baseline:
        OUT = ROOT/'build/checks/roster-layout-baseline'
    OUT.mkdir(parents=True, exist_ok=True)
    page = OUT/'fixture.html'
    page.write_text(fixture(args.baseline), encoding='utf-8')
    results = []
    for width in (args.width or (1280, 1366, 1920, 2560)):
        command = [str(EDGE), '--headless=new', '--disable-gpu', '--no-first-run',
                   '--disable-extensions', '--hide-scrollbars', '--allow-file-access-from-files',
                   '--user-data-dir='+str(OUT/'edge-profile'), '--virtual-time-budget=4000',
                   '--window-size=%d,1080'%width, '--dump-dom',
                   '--screenshot='+str(OUT/('tab-%d.png'%width)), page.as_uri()]
        proc = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace', timeout=40,
                              creationflags=subprocess.CREATE_NO_WINDOW)
        (OUT/('browser-%d.log'%width)).write_text(proc.stderr,encoding='utf-8')
        (OUT/('dom-%d.html'%width)).write_text(proc.stdout,encoding='utf-8')
        match = re.search(r'<pre id="qa-result">(.*?)</pre>', proc.stdout, re.S)
        if not match:
            raise SystemExit('No geometry result from Edge; see browser log')
        result = json.loads(html.unescape(match.group(1)))
        results.append(result)
        print(width, 'error count:',len(result['errors']), 'first errors:',result['errors'][:3],
              'min nickname width:', min(v['nameWidth'] for v in result['metrics']))
    (OUT/'geometry.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    if any(x['errors'] for x in results): raise SystemExit(1)


if __name__ == '__main__':
    main()
