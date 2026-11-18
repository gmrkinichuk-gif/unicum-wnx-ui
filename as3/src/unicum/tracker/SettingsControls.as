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
      private var _window:TrackerSettings;

      public function SettingsControls(window:TrackerSettings)
      {
         _window = window;
      }

      public function row(parent:Sprite, item:Object, y:Number) : Number
      {
         var kind:String = item.kind;
         var value:* = _window.value(item);
         if(kind == "checkbox")
         {
            Glass.button(parent, value ? "\u2713" : "", 0, y + 5, 24,
               function():void { _window.change(item.var, !Boolean(_window.value(item))); });
            Glass.text(parent, item.label, 36, y + 8, 444, 36, 12);
            return 46;
         }
         if(kind == "dropdown")
         {
            Glass.text(parent, item.label, 0, y, 480, 20, 12);
            var selected:int = int(value) - int(item.offset);
            var button:Sprite = Glass.button(parent, item.options[selected] + "  \u2304", 0, y + 24, 480,
               function():void { choices(button, item); });
            return 65;
         }
         if(kind == "input")
         {
            Glass.text(parent, item.label, 0, y, 480, 20, 12);
            var input:TextField = Glass.text(parent, String(value), 0, y + 24, 480, 28, 13);
            input.type = TextFieldType.INPUT;
            input.mouseEnabled = input.selectable = true;
            input.background = true;
            input.backgroundColor = 0x242a34;
            input.multiline = false;
            input.wordWrap = false;
            input.maxChars = 120;
            input.addEventListener(Event.CHANGE, function(event:Event):void { _window.change(item.var, input.text, false); });
            return 65;
         }
         if(kind == "button")
         {
            Glass.text(parent, item.label, 0, y + 4, 315, 43, 12);
            Glass.button(parent, item.word, 330, y + 4, 150,
                         function():void { _window.action(item.var); }, Boolean(item.danger));
            return 57;
         }
         Glass.text(parent, item.label, 0, y + 2, 480, 65, 11, 0x9aa5b4);
         return 70;
      }

      private function choices(button:Sprite, item:Object) : void
      {
         var point:Point = _window.globalToLocal(button.localToGlobal(new Point(0, button.height + 2)));
         _window.openChoices(item, point);
      }
   }
}
