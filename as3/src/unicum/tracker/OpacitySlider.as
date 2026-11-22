package unicum.tracker
{
   import flash.display.Sprite;
   import flash.display.Stage;
   import flash.events.Event;
   import flash.events.FocusEvent;
   import flash.events.MouseEvent;
   import flash.geom.Point;
   import flash.ui.Keyboard;

   public class OpacitySlider extends Sprite
   {
      private static const START:Number = 8;
      private var _width:Number;
      private var _end:Number;
      private var _options:Array;
      private var _index:int;
      private var _accent:uint;
      private var _changed:Function;
      private var _dragStage:Stage;

      public function OpacitySlider(w:Number, options:Array, selected:int, accent:uint, changed:Function)
      {
         _width = w;
         _end = w - 70;
         _options = options;
         _index = selected;
         _accent = accent;
         _changed = changed;
         buttonMode = true;
         mouseChildren = false;
         tabEnabled = true;
         addEventListener(MouseEvent.MOUSE_DOWN, beginDrag);
         addEventListener(FocusEvent.FOCUS_IN, focusChanged);
         addEventListener(FocusEvent.FOCUS_OUT, focusChanged);
         addEventListener(Event.REMOVED_FROM_STAGE, detachDrag);
         paint();
      }

      private function paint() : void
      {
         Glass.clear(this);
         graphics.beginFill(0, 0.001);
         graphics.drawRect(0, 0, _end + 8, 32);
         graphics.endFill();
         graphics.beginFill(Glass.mix(0x50596a, _accent, 0.2), 0.64);
         graphics.drawRoundRect(START, 13, _end - START, 6, 6, 6);
         graphics.endFill();
         var thumb:Number = START + (_end - START) * _index / Math.max(1, _options.length - 1);
         if(thumb > START)
         {
            graphics.beginFill(Glass.mix(0xa5b6d4, _accent, 0.56), 0.95);
            graphics.drawRoundRect(START, 13, thumb - START, 6, 6, 6);
            graphics.endFill();
         }
         graphics.lineStyle(stage != null && stage.focus == this ? 2 : 1, 0xe4ebf8, 0.85);
         graphics.beginFill(Glass.mix(0xd5dfef, _accent, 0.42));
         graphics.drawCircle(thumb, 16, 7);
         graphics.endFill();
         graphics.lineStyle(1, Glass.mix(0x778397, _accent, 0.24), 0.49);
         graphics.beginFill(Glass.mix(0x282e39, _accent, 0.14), 0.92);
         graphics.drawRoundRect(_width - 57, 4, 57, 24, 8, 8);
         graphics.endFill();
         Card.line(this, _options[_index], _width - 57, 4, 57, 24, 14, 0xe3e8f2);
      }

      private function focusChanged(event:FocusEvent) : void
      {
         paint();
      }

      private function beginDrag(event:MouseEvent) : void
      {
         event.stopPropagation();
         if(stage == null) return;
         stage.focus = this;
         var point:Point = globalToLocal(new Point(event.stageX, event.stageY));
         if(point.x > _end + 8) return;
         detachDrag();
         _dragStage = stage;
         _dragStage.addEventListener(MouseEvent.MOUSE_MOVE, moveDrag, true);
         _dragStage.addEventListener(MouseEvent.MOUSE_UP, release, true);
         _dragStage.addEventListener(Event.MOUSE_LEAVE, detachDrag);
         stepAt(point.x);
      }

      private function moveDrag(event:MouseEvent) : void
      {
         event.stopPropagation();
         stepAt(globalToLocal(new Point(event.stageX, event.stageY)).x);
      }

      private function release(event:MouseEvent) : void
      {
         moveDrag(event);
         detachDrag();
      }

      private function detachDrag(event:Event = null) : void
      {
         if(_dragStage == null) return;
         _dragStage.removeEventListener(MouseEvent.MOUSE_MOVE, moveDrag, true);
         _dragStage.removeEventListener(MouseEvent.MOUSE_UP, release, true);
         _dragStage.removeEventListener(Event.MOUSE_LEAVE, detachDrag);
         _dragStage = null;
      }

      private function stepAt(localX:Number) : void
      {
         setIndex(Math.round((localX - START) * (_options.length - 1) / (_end - START)));
      }

      private function setIndex(index:int) : void
      {
         index = Math.max(0, Math.min(index, _options.length - 1));
         if(index == _index) return;
         _index = index;
         paint();
         _changed(index);
      }

      public function adjust(keyCode:uint) : Boolean
      {
         switch(keyCode)
         {
            case Keyboard.LEFT: setIndex(_index - 1); break;
            case Keyboard.RIGHT: setIndex(_index + 1); break;
            case Keyboard.HOME: setIndex(0); break;
            case Keyboard.END: setIndex(_options.length - 1); break;
            default: return false;
         }
         return true;
      }
   }
}
