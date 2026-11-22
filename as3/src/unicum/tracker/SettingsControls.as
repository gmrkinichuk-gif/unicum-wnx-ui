package unicum.tracker
{
   import flash.display.Sprite;
   import flash.events.Event;
   import flash.events.MouseEvent;
   import flash.geom.Point;
   import flash.text.TextField;
   import flash.text.TextFieldType;

   public class SettingsControls
   {
      public static const WIDTH:Number = 520;
      private var _window:TrackerSettings;

      public function SettingsControls(window:TrackerSettings)
      {
         _window = window;
      }

      public function row(parent:Sprite, item:Object, y:Number) : Number
      {
         var kind:String = item.kind;
         var value:* = _window.value(item);
         var color:uint = _window.accent();
         if(kind == "checkbox")
         {
            Card.button(parent, value ? "\u2713" : "", 0, y + 5, 26, 26,
               function():void { _window.change(item.var, !Boolean(_window.value(item))); },
               color, value ? "primary" : "neutral");
            Glass.text(parent, item.label, 38, y + 8, WIDTH - 38, 35, 13);
            return 46;
         }
         if(kind == "dropdown")
         {
            if(String(item.var).slice(-8) == "_opacity") return opacity(parent, item, y, color);
            if(item.var.indexOf("tracker_") == 0) return segments(parent, item, y, color);
            Glass.text(parent, item.label, 0, y, WIDTH, 24, 13);
            var selected:int = int(value) - int(item.offset);
            var button:Sprite = Card.button(parent, item.options[selected], 0, y + 25, WIDTH, 30,
               function():void { choices(button, item); }, color, "neutral", "left", true);
            return 65;
         }
         if(kind == "input")
         {
            Glass.text(parent, item.label, 0, y, WIDTH, 24, 13);
            var input:TextField = Glass.text(parent, String(value), 0, y + 25, WIDTH, 30, 13);
            input.type = TextFieldType.INPUT;
            input.mouseEnabled = input.selectable = true;
            input.background = true;
            input.backgroundColor = Glass.mix(0x242a34, color, 0.12);
            input.border = true;
            input.borderColor = Glass.mix(0x465060, color, 0.25);
            input.multiline = false;
            input.wordWrap = false;
            input.maxChars = 120;
            input.addEventListener(Event.CHANGE, function(event:Event):void { _window.change(item.var, input.text, false); });
            return 65;
         }
         if(kind == "button")
         {
            Card.rule(parent, 0, y, WIDTH, 0);
            Glass.text(parent, item.label, 0, y + 15, 350, 35, 13);
            Card.button(parent, item.word, 370, y + 9, 150, 32,
                        function():void { _window.action(item.var); }, color, item.danger ? "danger" : "neutral");
            return 52;
         }
         Card.line(parent, item.label, 0, y + 2, WIDTH, 28, 12, 0x9aa5b4, "left");
         return 32;
      }

      private function segments(parent:Sprite, item:Object, y:Number, color:uint) : Number
      {
         var left:Number = 214;
         Card.line(parent, item.label, 0, y + 6, left - 12, 32, 14, 0xe3e8f2, "left");
         var width:Number = (WIDTH - left) / item.options.length;
         var selected:int = int(_window.value(item)) - int(item.offset);
         for(var index:int = 0; index < item.options.length; index++)
            Card.button(parent, item.options[index], left + index * width, y + 6, width - 3, 32,
                        select(item, index), color, index == selected ? "selected" : "neutral");
         return 50;
      }

      private function select(item:Object, index:int) : Function
      {
         return function():void { _window.change(item.var, index + int(item.offset)); };
      }

      private function opacity(parent:Sprite, item:Object, y:Number, color:uint) : Number
      {
         var left:Number = 214;
         Card.line(parent, item.label, 0, y + 6, left - 12, 32, 14, 0xe3e8f2, "left");
         var offset:int = int(item.offset);
         var slider:OpacitySlider = new OpacitySlider(WIDTH - left, item.options, int(_window.value(item)) - offset,
            color, function(index:int):void { _window.change(item.var, index + offset, false); });
         slider.x = left;
         slider.y = y + 6;
         parent.addChild(slider);
         return 50;
      }

      private function choices(button:Sprite, item:Object) : void
      {
         var top:Point = _window.globalToLocal(button.localToGlobal(new Point()));
         var bottom:Point = _window.globalToLocal(button.localToGlobal(new Point(0, button.height)));
         _window.openChoices(item, top, bottom.y);
      }
   }
}
