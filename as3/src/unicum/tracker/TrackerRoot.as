package unicum.tracker
{
   import flash.display.DisplayObjectContainer;
   import flash.display.DisplayObject;
   import flash.display.Sprite;
   import flash.events.Event;
   import flash.events.MouseEvent;
   import flash.geom.Point;
   import flash.utils.getQualifiedClassName;
   import flash.utils.Dictionary;

   public class TrackerRoot extends Sprite
   {
      private var _host:DisplayObjectContainer;
      private var _widget:Widget;
      private var _settings:TrackerSettings;
      private var _shield:Sprite;
      private var _tooltip:Sprite = new Sprite();
      private var _state:Object;
      private var _out:String = "";
      private var _saved:String = "";
      private var _viewportWidth:Number = 1920;
      private var _viewportHeight:Number = 1080;
      private var _placed:Boolean = false;
      private var _inGarage:Boolean = false;
      private var _nativeWindows:Dictionary = new Dictionary(true);

      public function TrackerRoot(host:DisplayObjectContainer)
      {
         _host = host;
         mouseEnabled = false;
         _widget = new Widget(this);
         addChild(_widget);
         _tooltip.mouseEnabled = false;
         _tooltip.mouseChildren = false;
         addChild(_tooltip);
         host.addChild(this);
         visible = false;
         if(stage != null) stage.addEventListener(Event.RESIZE, resized);
         if(stage != null) stage.addEventListener(Event.ADDED_TO_STAGE, nativeWindow, true, 0, true);
      }

      public function word(value:String) : String
      {
         return _state != null && _state.labels[value] != null ? _state.labels[value] : value;
      }

      public function send(action:Object) : void
      {
         if(_state != null) { action.account = _state.account; action.region = _state.region; }
         _out += Wire.stringify(action) + "\n";
      }

      public function take() : String
      {
         var value:String = _out;
         _out = "";
         return value;
      }

      public function update(value:String) : void
      {
         try
         {
            var state:Object = Wire.parse(value);
            if(_state != null && (state.account != _state.account || state.region != _state.region))
            {
               closeSettings();
               _placed = false;
            }
            _state = state;
            _inGarage = true;
            updateVisibility();
            _widget.update(state);
            var saved:String = Wire.stringify(state.position);
            if(!_placed || _saved != saved)
            {
               _saved = saved;
               _placed = true;
               _widget.x = state.position == null ? defaultX() : state.position[0] * Math.max(0, _viewportWidth - _widget.panelWidth - 16) + 8;
               _widget.y = state.position == null ? 150 : state.position[1] * Math.max(0, _viewportHeight - _widget.panelHeight - 16) + 8;
            }
            if(_settings != null) _settings.update(state);
            layout();
         }
         catch(error:Error) { send({kind:"log",message:"update: " + error.message}); }
      }

      public function layout() : void
      {
         if(stage == null) return;
         var origin:Point = _host.globalToLocal(new Point(0, 0));
         var end:Point = _host.globalToLocal(new Point(stage.stageWidth, stage.stageHeight));
         x = origin.x;
         y = origin.y;
         _viewportWidth = Math.max(1, end.x - origin.x);
         _viewportHeight = Math.max(1, end.y - origin.y);
         clampWidget();
         if(_settings != null)
         {
            var scale:Number = Geometry.fit(_viewportWidth, _viewportHeight, TrackerSettings.WIDTH, TrackerSettings.HEIGHT);
            _settings.scaleX = _settings.scaleY = scale;
            _settings.x = (_viewportWidth - TrackerSettings.WIDTH * scale) / 2;
            _settings.y = (_viewportHeight - TrackerSettings.HEIGHT * scale) / 2;
            _shield.graphics.clear();
            _shield.graphics.beginFill(0, 0.18);
            _shield.graphics.drawRect(0, 0, _viewportWidth, _viewportHeight);
            _shield.graphics.endFill();
         }
      }

      public function clampWidget() : void
      {
         var scale:Number = Geometry.fit(_viewportWidth, _viewportHeight, _widget.panelWidth, _widget.totalHeight);
         _widget.scaleX = _widget.scaleY = scale;
         _widget.x = Geometry.clamp(_widget.x, _viewportWidth, _widget.panelWidth * scale);
         _widget.y = Geometry.clamp(_widget.y, _viewportHeight, _widget.panelHeight * scale);
         _widget.placeDetails(_viewportHeight);
      }

      public function savePosition() : void
      {
         clampWidget();
         var position:Array = [Math.max(0, Math.min(1, (_widget.x - 8) / Math.max(1, _viewportWidth - _widget.panelWidth * _widget.scaleX - 16))),
                               Math.max(0, Math.min(1, (_widget.y - 8) / Math.max(1, _viewportHeight - _widget.panelHeight * _widget.scaleY - 16)))];
         _saved = Wire.stringify(position);
         send({kind:"position",value:position});
      }

      public function resetPosition() : void
      {
         _widget.x = defaultX();
         _widget.y = 150;
         _placed = false;
         clampWidget();
      }

      private function defaultX() : Number { return Math.min(390, Math.max(220, _viewportWidth * 0.2)); }

      private function resized(event:Event) : void
      {
         tooltip(null, false, this);
         layout();
         _placed = false;
         if(_state != null) update(Wire.stringify(_state));
      }

      public function openSettings() : void
      {
         if(_state == null || _settings != null) return;
         tooltip(null, false, this);
         _shield = new Sprite();
         _shield.addEventListener(MouseEvent.MOUSE_DOWN, absorb);
         _shield.addEventListener(MouseEvent.CLICK, absorb);
         _shield.addEventListener(MouseEvent.MOUSE_WHEEL, absorb);
         addChild(_shield);
         _settings = new TrackerSettings(this, _state);
         addChild(_settings);
         _settings.activate();
         layout();
         send({kind:"opened"});
      }

      private function absorb(event:MouseEvent) : void { event.stopImmediatePropagation(); }

      private function nativeWindow(event:Event) : void
      {
         var target:DisplayObject = event.target as DisplayObject;
         if(target == null) return;
         var name:String = getQualifiedClassName(target);
         if(name != "LobbyMenuUI" && name != "net.wg.gui.lobby.menu::LobbyMenu" &&
            name != "SettingsWindowUI" && name != "net.wg.gui.lobby.settings::SettingsWindow") return;
         _nativeWindows[target] = true;
         target.addEventListener(Event.REMOVED_FROM_STAGE, nativeClosed, false, 0, true);
         closeSettings();
         _widget.suspend();
         Glass.clear(_tooltip);
         updateVisibility();
      }

      private function nativeClosed(event:Event) : void
      {
         var target:DisplayObject = event.currentTarget as DisplayObject;
         target.removeEventListener(Event.REMOVED_FROM_STAGE, nativeClosed);
         delete _nativeWindows[target];
         updateVisibility();
      }

      private function updateVisibility() : void
      {
         for(var window:Object in _nativeWindows) { visible = false; return; }
         visible = _inGarage;
      }

      public function closeSettings() : void
      {
         if(_settings != null)
         {
            _settings.dispose();
            removeChild(_settings);
            _settings = null;
         }
         if(_shield != null)
         {
            removeChild(_shield);
            _shield = null;
         }
      }

      public function discardDraft() : void { if(_settings != null) _settings.discard(); }
      public function escapeSettings() : Boolean
      {
         if(_settings == null || !visible) return false;
         _settings.escape();
         return true;
      }

      public function tooltip(row:Object, bars:Boolean, target:DisplayObject) : void
      {
         Glass.clear(_tooltip);
         if(row == null || _settings != null) return;
         var color:uint = uint(String(_state.color).replace("#", "0x"));
         var lines:String = "WNX  " + Glass.number(row.wnx) + "\n" + row.time;
         if(bars)
         {
            lines = row.tankName + (row.tier != null ? "  \u00b7  " + row.tier : "") + "\n" + lines;
            if(row.winnerResult != null) lines += "  " + word(row.winnerResult);
            lines += "\n" + word("Damage") + "  " + Glass.number(row.damageDealt);
            lines += "   " + word("Assist") + "  " + Glass.number(Number(row.damageAssistedRadio) + Number(row.damageAssistedTrack));
            lines += "\n" + word("Combined") + "  " + Glass.number(Number(row.damageDealt) + Number(row.damageAssistedRadio) + Number(row.damageAssistedTrack));
         }
         else lines += "\n#" + row.arenaUniqueId;
         if(row.wnx == null) lines += "\n" + word("WNX temporarily unavailable");
         var height:Number = bars ? 158 : 96;
         Glass.panel(_tooltip, 268, height, color, 1);
         Glass.text(_tooltip, lines, 10, 8, 248, height - 12, 12);
         var point:Point = globalToLocal(target.localToGlobal(new Point(target.width / 2, target.height)));
         _tooltip.x = Geometry.clamp(point.x - 134, _viewportWidth, 268);
         var below:Number = Math.max(point.y + 14, _widget.y + 32 * _widget.scaleY);
         _tooltip.y = Geometry.clamp(below + height <= _viewportHeight - 8 ? below : _widget.y - height - 8,
                                     _viewportHeight, height);
         setChildIndex(_tooltip, numChildren - 1);
      }

      public function hide() : void
      {
         _inGarage = false;
         visible = false;
         _widget.suspend();
         closeSettings();
         Glass.clear(_tooltip);
         _out = "";
      }

      public function dispose() : void
      {
         hide();
         _widget.dispose();
         if(stage != null) stage.removeEventListener(Event.RESIZE, resized);
         if(stage != null) stage.removeEventListener(Event.ADDED_TO_STAGE, nativeWindow, true);
         for(var window:Object in _nativeWindows)
            DisplayObject(window).removeEventListener(Event.REMOVED_FROM_STAGE, nativeClosed);
         _nativeWindows = new Dictionary(true);
         if(parent != null) parent.removeChild(this);
      }
   }
}
