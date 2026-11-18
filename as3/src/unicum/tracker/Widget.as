package unicum.tracker
{
   import flash.display.Sprite;
   import flash.events.MouseEvent;
   import flash.geom.Point;

   public class Widget extends Sprite
   {
      private var _owner:TrackerRoot;
      private var _state:Object;
      private var _expanded:Boolean = false;
      private var _pinned:Boolean = false;
      private var _body:Sprite = new Sprite();
      private var _details:Sprite = new Sprite();
      private var _drag:Point;
      private var _start:Point;
      private var _moved:Boolean;
      public var panelWidth:Number = 320;
      public var panelHeight:Number = 84;

      public function Widget(owner:TrackerRoot)
      {
         _owner = owner;
         addChild(_body);
         addChild(_details);
         addEventListener(MouseEvent.ROLL_OUT, out);
      }

      public function update(state:Object) : void
      {
         _state = state;
         if(state.mode == "Mini") _expanded = _pinned = false;
         draw();
      }

      public function get totalHeight() : Number
      {
         return panelHeight + (_expanded ? 160 : 0);
      }

      private function draw(detailsOnly:Boolean = false) : void
      {
         if(_state == null) return;
         if(!detailsOnly) Glass.clear(_body);
         Glass.clear(_details);
         var mini:Boolean = _state.mode == "Mini";
         var graph:Boolean = _state.mode == "Trend" || _state.mode == "Battles";
         panelWidth = mini ? 210 : 320;
         panelHeight = graph && _state.progress == _state.count ? 202 : (mini ? 66 : 100);
         var color:uint = uint(String(_state.color).replace("#", "0x"));
         if(!detailsOnly)
         {
         Glass.panel(_body, panelWidth, panelHeight, color, _state.opacity / 100);
         var handle:Sprite = new Sprite();
         handle.graphics.beginFill(0, 0.001);
         handle.graphics.drawRect(0, 0, panelWidth - 94, 30);
         handle.graphics.endFill();
         handle.addEventListener(MouseEvent.MOUSE_DOWN, beginDrag);
         _body.addChild(handle);
         Glass.text(_body, mini ? "WNX" : "\u283f  WNX Tracker", 10, 5, panelWidth - 104, 22, 12);
         Glass.button(_body, "\u2039", panelWidth - 88, 4, 23, function():void { _owner.send({kind:"mode",step:-1}); }, false, false, 23);
         Glass.button(_body, "\u203a", panelWidth - 61, 4, 23, function():void { _owner.send({kind:"mode",step:1}); }, false, false, 23);
         Glass.button(_body, "\u2699", panelWidth - 34, 4, 25, function():void { _owner.openSettings(); }, false, false, 23);
         var info:Sprite = new Sprite();
         info.y = 31;
         info.graphics.beginFill(0, 0.001);
         info.graphics.drawRect(0, 0, panelWidth, mini ? 33 : 64);
         info.graphics.endFill();
         _body.addChild(info);
         if(!mini)
         {
            info.addEventListener(MouseEvent.CLICK, pin);
            info.addEventListener(MouseEvent.ROLL_OVER, over);
         }
         if(mini)
            Glass.text(info, Glass.number(_state.total), 10, -2, 185, 35, 24);
         else if(_state.progress < _state.count)
         {
            Glass.text(info, _state.message, 10, 0, 300, 39, 12);
            info.graphics.beginFill(0x788496, 0.2);
            info.graphics.drawRect(10, 46, 259, 2);
            info.graphics.endFill();
            info.graphics.beginFill(color, 0.8);
            info.graphics.drawRect(10, 46, 259 * _state.progress / _state.count, 2);
            info.graphics.endFill();
            Glass.text(info, _state.progress + "/" + _state.count, 273, 36, 40, 20, 10);
         }
         else
         {
            Glass.text(info, Glass.number(_state.wnx), 10, -1, 150, 38, 26);
            var delta:* = _state.delta;
            var change:String = delta == null ? "\u2014" : (delta > 0 ? "\u2191 +" : delta < 0 ? "\u2193 " : "") + Glass.number(delta);
            Glass.text(info, change, 168, 5, 140, 27, 17, delta == null || delta == 0 ? 0x9ba5b4 : (delta > 0 ? 0x8fbc9d : 0xd08b8d));
            Glass.text(info, _state.wnx == null ? _state.message : _state.mode + "  \u00b7  " + _state.count,
                       10, 37, 300, 26, 11, 0x9ba5b4);
         }
         if(graph && _state.progress == _state.count) addGraph(_body, 90, _state.mode == "Battles");
         }
         if(_expanded)
         {
            Glass.panel(_details, panelWidth, 156, color, Math.max(0.82, _state.opacity / 100));
            if(_state.progress == _state.count)
            {
               if(!graph) addGraph(_details, 2, false);
               var yy:int = graph ? 16 : 111;
               Glass.text(_details, "WNX  " + Glass.number(_state.wnx) + "    " + _owner.word("Average damage") + "  " + Glass.number(_state.damage), 10, yy, 300, 20, 11);
               Glass.text(_details, _owner.word("Average assist") + "  " + Glass.number(_state.assist) + "    " + _owner.word("Combined") + "  " + Glass.number(_state.combined), 10, yy + 20, 300, 20, 11);
               if(graph) Glass.text(_details, _owner.word("Combined = damage + radio + track; not the official gun-mark calculation."), 10, 64, 300, 62, 11, 0x9ba5b4);
            }
            else Glass.text(_details, _state.message, 10, 15, 300, 60, 12);
            if(_state.error) Glass.text(_details, _state.error, 10, 133, 300, 20, 10, 0xe0a5a5);
         }
         _details.visible = _expanded;
         _owner.layout();
      }

      private function addGraph(target:Sprite, y:Number, bars:Boolean) : void
      {
         var graph:Graph = new Graph(bars ? _state.bars : _state.points, bars,
                                    uint(String(_state.color).replace("#", "0x")), _owner.tooltip);
         graph.x = 10;
         graph.y = y;
         graph.addEventListener(MouseEvent.ROLL_OVER, over);
         target.addChild(graph);
      }

      public function placeDetails(viewHeight:Number) : void
      {
         _details.y = y + (panelHeight + 160) * scaleY <= viewHeight - 8 ? panelHeight + 4 : -160;
         if(_expanded && _details.y < 0 && y - 160 * scaleY < 8) y = 8 + 160 * scaleY;
         graphics.clear();
         if(_expanded)
         {
            graphics.beginFill(0, 0.001);
            graphics.drawRect(0, Math.min(0, _details.y), panelWidth, totalHeight);
            graphics.endFill();
         }
      }

      private function over(event:MouseEvent) : void
      {
         if(_state != null && _state.mode != "Mini" && !_expanded && _drag == null)
         { _expanded = true; draw(true); }
      }

      private function out(event:MouseEvent) : void
      {
         if(!_pinned && _expanded && _drag == null) { _expanded = false; draw(true); }
         _owner.tooltip(null, false, this);
      }

      private function pin(event:MouseEvent) : void
      {
         event.stopPropagation();
         _pinned = !_pinned;
         _expanded = _pinned;
         draw(true);
      }

      private function beginDrag(event:MouseEvent) : void
      {
         if(stage == null) return;
         event.stopPropagation();
         _drag = _owner.globalToLocal(new Point(event.stageX, event.stageY));
         _start = new Point(x, y);
         _moved = false;
         stage.addEventListener(MouseEvent.MOUSE_MOVE, moveDrag);
         stage.addEventListener(MouseEvent.MOUSE_UP, endDrag);
      }

      private function moveDrag(event:MouseEvent) : void
      {
         var point:Point = _owner.globalToLocal(new Point(event.stageX, event.stageY));
         if(!_moved && Point.distance(point, _drag) < 4) return;
         _moved = true;
         x = _start.x + point.x - _drag.x;
         y = _start.y + point.y - _drag.y;
         _owner.clampWidget();
      }

      private function endDrag(event:MouseEvent) : void
      {
         if(stage != null)
         {
            stage.removeEventListener(MouseEvent.MOUSE_MOVE, moveDrag);
            stage.removeEventListener(MouseEvent.MOUSE_UP, endDrag);
         }
         _drag = null;
         if(_moved) _owner.savePosition();
      }

      public function dispose() : void
      {
         suspend();
         removeEventListener(MouseEvent.ROLL_OUT, out);
      }

      public function suspend() : void
      {
         if(stage != null)
         {
            stage.removeEventListener(MouseEvent.MOUSE_MOVE, moveDrag);
            stage.removeEventListener(MouseEvent.MOUSE_UP, endDrag);
         }
         _drag = null;
         _expanded = _pinned = false;
      }
   }
}
