package unicum.tracker
{
   import flash.display.GradientType;
   import flash.display.Sprite;
   import flash.filters.DropShadowFilter;
   import flash.geom.Matrix;
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

      public static function verticalFill(target:Sprite, w:Number, h:Number, colors:Array,
                                          opacity:Number, stops:Array) : void
      {
         var matrix:Matrix = new Matrix();
         matrix.createGradientBox(w, h, Math.PI / 2);
         var alphas:Array = [];
         for each(var color:uint in colors) alphas.push(opacity);
         target.graphics.beginGradientFill(GradientType.LINEAR, colors, alphas, stops, matrix);
      }

      public static function raisedPanel(target:Sprite, w:Number, h:Number, color:uint, opacity:Number) : Sprite
      {
         // Keep the hit surface at the card's dimensions, outside the shadow.
         target.graphics.clear();
         target.graphics.beginFill(0, 0.001);
         target.graphics.drawRoundRect(0, 0, w, h, 12, 12);
         target.graphics.endFill();

         var surface:Sprite = new Sprite();
         surface.mouseEnabled = surface.mouseChildren = false;
         surface.filters = [new DropShadowFilter(4, 90, 0x04070c, 0.42, 8, 8)];
         surface.graphics.lineStyle(1, mix(0x66717e, color, 0.3), 0.6 * opacity);
         verticalFill(surface, w, h, [mix(0x303948, color, 0.23), tint(color), mix(0x10141d, color, 0.12)],
                      opacity, [0, 106, 255]);
         surface.graphics.drawRoundRect(0, 0, w, h, 12, 12);
         surface.graphics.endFill();
         surface.graphics.lineStyle(1, mix(0xdde7f6, color, 0.42), 0.64 * opacity);
         surface.graphics.moveTo(7, 1);
         surface.graphics.lineTo(w - 7, 1);
         surface.graphics.lineStyle(1, 0x05070d, 0.65 * opacity);
         surface.graphics.moveTo(7, h - 1);
         surface.graphics.lineTo(w - 7, h - 1);
         target.addChildAt(surface, 0);
         return surface;
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
