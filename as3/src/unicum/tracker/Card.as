package unicum.tracker
{
   import flash.display.Sprite;
   import flash.events.MouseEvent;
   import flash.text.TextField;
   import flash.text.TextFormat;

   public class Card
   {
      public static function line(parent:Sprite, value:String, x:Number, y:Number, w:Number,
                                  h:Number, size:int, color:uint, align:String = "center") : void
      {
         var field:TextField = Glass.text(parent, value, x, y, w, h, size, color);
         field.multiline = false;
         field.wordWrap = false;
         var format:TextFormat = field.defaultTextFormat;
         format.align = align;
         field.setTextFormat(format);
         // Scaleform text fields reserve two pixels on each side.
         while(field.textWidth + 4 > w && size > 8)
         {
            format.size = --size;
            field.setTextFormat(format);
         }
         var offset:Number = Math.max(0, Math.floor((h - field.textHeight - 4) / 2));
         field.y = y + offset;
         field.height = h - offset;
      }

      public static function rule(parent:Sprite, x:Number, y:Number, dx:Number, dy:Number) : void
      {
         parent.graphics.lineStyle(1, 0xaab6c8, 0.22);
         parent.graphics.moveTo(x, y);
         parent.graphics.lineTo(x + dx, y + dy);
      }

      public static function control(parent:Sprite, label:String, x:Number, w:Number,
                                     callback:Function, selected:Boolean, accent:uint,
                                     gear:Boolean = false) : void
      {
         var tab:Sprite = button(parent, label, x, 4, w, 22, callback, accent, selected ? "selected" : "tab");
         if(gear) TrackerIcons.draw(tab, TrackerIcons.SETTINGS, (w - 14) / 2, 4, 14);
      }

      public static function button(parent:Sprite, label:String, x:Number, y:Number, w:Number, h:Number,
                                    callback:Function, accent:uint, style:String = "neutral",
                                    align:String = "center", dropdown:Boolean = false) : Sprite
      {
         var target:Sprite = new Sprite();
         target.x = x;
         target.y = y;
         target.buttonMode = true;
         target.tabEnabled = true;
         target.mouseChildren = false;
         var selected:Boolean = style == "selected";
         var highlighted:Boolean = selected || style == "primary";
         var danger:Boolean = style == "danger";
         var fill:uint = danger ? 0x642c32 : Glass.mix(0x282e39, accent, highlighted ? 0.32 : 0.06);
         var stroke:uint = danger ? 0xb84d51 : Glass.mix(0x7c8798, accent, highlighted ? 0.52 : 0.16);
         function paint(hover:Boolean):void
         {
            target.graphics.clear();
            if(style != "tab") target.graphics.lineStyle(1, stroke, highlighted || danger || hover ? 0.85 : 0.35);
            var opacity:Number = highlighted || danger ? (hover ? 1 : 0.92) : (hover ? 0.72 : 0.28);
            if(highlighted)
               Glass.verticalFill(target, w, h, [Glass.mix(fill, 0xd9e4f7, 0.16), fill], opacity, [0, 255]);
            else target.graphics.beginFill(fill, opacity);
            target.graphics.drawRoundRect(0, 0, w, h, 8, 8);
            target.graphics.endFill();
            if(highlighted)
            {
               target.graphics.lineStyle(1, Glass.mix(0xd4dbeb, accent, 0.40), 0.62);
               target.graphics.moveTo(5, 1);
               target.graphics.lineTo(w - 5, 1);
            }
            if(selected)
            {
               target.graphics.lineStyle(1, Glass.mix(0xd4dbeb, accent, 0.5), 0.85);
               target.graphics.moveTo(7, h - 2);
               target.graphics.lineTo(w - 7, h - 2);
            }
            if(dropdown)
            {
               target.graphics.lineStyle(1.5, 0xc5cfdd, 0.85);
               target.graphics.moveTo(w - 21, h / 2 - 2);
               target.graphics.lineTo(w - 17, h / 2 + 2);
               target.graphics.lineTo(w - 13, h / 2 - 2);
            }
         }
         paint(false);
         if(label != "")
         {
            var inset:Number = align == "left" ? 12 : 2;
            line(target, label, inset, 0, w - inset * 2 - (dropdown ? 16 : 0), h, h > 24 ? 14 : 12,
                 danger ? 0xf0a0a3 : (highlighted ? 0xf3f5fa : 0xc5cfdd), align);
         }
         target.addEventListener(MouseEvent.ROLL_OVER, function(event:MouseEvent):void { paint(true); });
         target.addEventListener(MouseEvent.ROLL_OUT, function(event:MouseEvent):void { paint(false); });
         target.addEventListener(MouseEvent.MOUSE_DOWN, function(event:MouseEvent):void { event.stopPropagation(); });
         target.addEventListener(MouseEvent.CLICK, function(event:MouseEvent):void {
            event.stopPropagation(); callback();
         });
         parent.addChild(target);
         return target;
      }

      public static function metric(parent:Sprite, path:String, value:*, center:Number, y:Number) : void
      {
         TrackerIcons.draw(parent, path, center - 35, y + 1, 24);
         line(parent, Glass.number(value), center - 11, y, 44, 26, 16, 0xe3e8f2);
      }
   }
}
