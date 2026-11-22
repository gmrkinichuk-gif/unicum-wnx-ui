package unicum.tracker
{
   import flash.display.Sprite;
   import flash.events.MouseEvent;
   import flash.geom.Point;

   public class Widget extends Sprite
   {
      private var _owner:TrackerRoot;
      private var _state:Object;
      private var _body:Sprite = new Sprite();
      private var _drag:Point;
      private var _start:Point;
      private var _moved:Boolean;
      public var panelWidth:Number = 272;
      public var panelHeight:Number = 76;

      public function Widget(owner:TrackerRoot)
      {
         _owner = owner;
         addChild(_body);
      }

      public function update(state:Object) : void
      {
         _state = state;
         _owner.tooltip(null, false, this);
         draw();
      }

      private function draw() : void
      {
         if(_state == null) return;
         Glass.clear(_body);
         var mini:Boolean = _state.mode == "Mini";
         var chart:Boolean = _state.mode == "Trend" || _state.mode == "Battles";
         var ready:Boolean = _state.progress == _state.count;
         panelHeight = chart ? (ready ? 200 : 106) : 76;
         var color:uint = uint(String(_state.color).replace("#", "0x"));
         var surface:Sprite = Glass.raisedPanel(_body, panelWidth, panelHeight, color, _state.opacity / 100);
         var handle:Sprite = new Sprite();
         handle.graphics.beginFill(0, 0.001);
         handle.graphics.drawRect(0, 0, 20, 29);
         handle.graphics.endFill();
         handle.addEventListener(MouseEvent.MOUSE_DOWN, beginDrag);
         _body.addChild(handle);
         Card.line(_body, "\u283f", 2, 4, 18, 22, 12, 0x9ba5b4);
         drawModeTabs(color);
         Card.rule(surface, 10, 29, panelWidth - 20, 0);
         drawScore(surface, mini, color);
         if(chart && ready)
         {
            addGraph(_body, 75, _state.mode == "Battles");
            Card.rule(surface, 10, 169, panelWidth - 20, 0);
            Card.rule(surface, panelWidth / 2, 176, 0, 16);
            Card.metric(_body, TrackerIcons.DAMAGE, _state.damage, 73, 171);
            Card.metric(_body, TrackerIcons.ASSIST, _state.assist, 199, 171);
         }
         else if(chart)
            Card.line(_body, _state.message, 10, 77, panelWidth - 20, 24, 12, 0x9ba5b4);
         _owner.layout();
      }

      private function drawScore(surface:Sprite, mini:Boolean, color:uint) : void
      {
         var width:Number = mini ? panelWidth - 20 : panelWidth / 2 - 10;
         Card.line(_body, "WNX", 10, 33, width, 15, 10, 0xaeb9c8);
         Card.line(_body, Glass.number(mini ? _state.total : _state.wnx), 10, 44, width, 30, 22, color);
         if(mini) return;
         var delta:* = _state.delta;
         var change:String = delta == null ? "\u2014" : (delta > 0 ? "+" : "") + Glass.number(delta);
         var waiting:Boolean = _state.progress < _state.count;
         var right:Number = panelWidth / 2;
         Card.rule(surface, right, 37, 0, 17);
         Card.line(_body, change, right, waiting ? 34 : 35, width, waiting ? 24 : 33, 16,
                   delta == null || delta == 0 ? 0x9ba5b4 : (delta > 0 ? 0x8fbc9d : 0xd08b8d));
         if(waiting)
         {
            Card.line(_body, _state.progress + "/" + _state.count, right, 56, width, 15, 10, 0x9ba5b4);
            surface.graphics.lineStyle();
            surface.graphics.beginFill(color, 0.7);
            surface.graphics.drawRect(right + (width - 60) / 2, 72, 60 * _state.progress / _state.count, 2);
            surface.graphics.endFill();
         }
         if(_state.error) Card.line(_body, "!", panelWidth - 18, 32, 12, 16, 12, 0xe0a5a5);
      }

      private function drawModeTabs(color:uint) : void
      {
         var modes:Array = ["Mini", "Compact", "Trend", "Battles"];
         var widths:Array = [42, 64, 49, 52];
         var left:Number = 20;
         for(var i:int = 0; i < modes.length; i++)
         {
            var mode:String = modes[i];
            Card.control(_body, _owner.word(mode), left, widths[i], selectMode(mode), mode == _state.mode, color);
            left += widths[i] + 2;
         }
         Card.control(_body, "", panelWidth - 31, 26, function():void { _owner.openSettings(); }, false, color, true);
      }

      private function selectMode(mode:String) : Function
      {
         return function():void { _owner.send({kind:"mode",value:mode}); };
      }

      private function addGraph(target:Sprite, y:Number, bars:Boolean) : void
      {
         var graph:Graph = new Graph(bars ? _state.bars : _state.points, bars,
                                    uint(String(_state.color).replace("#", "0x")), _owner.tooltip);
         graph.x = 10;
         graph.y = y;
         target.addChild(graph);
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
      }

      public function suspend() : void
      {
         if(stage != null)
         {
            stage.removeEventListener(MouseEvent.MOUSE_MOVE, moveDrag);
            stage.removeEventListener(MouseEvent.MOUSE_UP, endDrag);
         }
         _drag = null;
         _moved = false;
      }
   }
}
