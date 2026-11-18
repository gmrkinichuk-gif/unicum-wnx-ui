package unicum.tracker
{
   import flash.display.Sprite;
   import flash.events.MouseEvent;
   import flash.text.TextField;
   import flash.text.TextFormat;

   public class Glass
   {
      public static function tint(color:uint) : uint
      {
         return mix(0x161b22, color, 0.14);
      }

      public static function mix(base:uint, color:uint, amount:Number) : uint
      {
         return uint(((base >> 16 & 255) * (1 - amount) + (color >> 16 & 255) * amount)) << 16 |
                uint(((base >> 8 & 255) * (1 - amount) + (color >> 8 & 255) * amount)) << 8 |
                uint(((base & 255) * (1 - amount) + (color & 255) * amount));
      }

      public static function panel(target:Sprite, w:Number, h:Number, color:uint, opacity:Number = 0.9) : void
      {
         target.graphics.clear();
         target.graphics.lineStyle(1, mix(0x66717e, color, 0.3), 0.55);
         target.graphics.beginFill(tint(color), opacity);
         target.graphics.drawRoundRect(0, 0, w, h, 12, 12);
         target.graphics.endFill();
      }

      public static function text(parent:Sprite, value:String, x:Number, y:Number,
                                  w:Number, h:Number = 22, size:int = 13, color:uint = 0xd9dde4) : TextField
      {
         var field:TextField = new TextField();
         field.defaultTextFormat = new TextFormat("$TextFont", size, color);
         field.text = value;
         field.x = x;
         field.y = y;
         field.width = w;
         field.height = h;
         field.multiline = true;
         field.wordWrap = true;
         field.selectable = false;
         field.mouseEnabled = false;
         parent.addChild(field);
         return field;
      }

      public static function button(parent:Sprite, label:String, x:Number, y:Number,
                                    w:Number, callback:Function, danger:Boolean = false,
                                    selected:Boolean = false, h:Number = 28) : Sprite
      {
         var button:Sprite = new Sprite();
         button.x = x;
         button.y = y;
         button.buttonMode = true;
         button.tabEnabled = true;
         button.graphics.lineStyle(1, danger ? 0xb84d51 : 0x7c8494, danger ? 0.8 : 0.35);
         button.graphics.beginFill(danger ? 0x642c32 : (selected ? 0x4a465b : 0x2e3440), 0.75);
         button.graphics.drawRoundRect(0, 0, w, h, 6, 6);
         button.graphics.endFill();
         var field:TextField = text(button, label, 6, (h - 22) / 2, w - 12, 22, 12,
                                    danger ? 0xf0a0a3 : 0xd9dde4);
         var format:TextFormat = field.defaultTextFormat;
         format.align = "center";
         field.setTextFormat(format);
         button.addEventListener(MouseEvent.MOUSE_DOWN, function(event:MouseEvent):void { event.stopPropagation(); });
         button.addEventListener(MouseEvent.CLICK, function(event:MouseEvent):void {
            event.stopPropagation(); callback();
         });
         parent.addChild(button);
         return button;
      }

      public static function clear(target:Sprite) : void
      {
         while(target.numChildren > 0) target.removeChildAt(0);
         target.graphics.clear();
      }

      public static function number(value:*) : String
      {
         return value == null || !isFinite(Number(value)) ? "\u2014" : String(Math.round(Number(value)));
      }
   }
}
