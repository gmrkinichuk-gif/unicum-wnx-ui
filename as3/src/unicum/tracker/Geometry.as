package unicum.tracker
{
   public class Geometry
   {
      public static function clamp(value:Number, extent:Number, size:Number, margin:Number = 8) : Number
      {
         return Math.max(margin, Math.min(value, Math.max(margin, extent - size - margin)));
      }

      public static function step(width:Number, count:int) : Number
      {
         return width / count;
      }

      public static function barWidth(width:Number, count:int) : Number
      {
         return step(width, count) * 0.66;
      }

      public static function fit(viewWidth:Number, viewHeight:Number, width:Number, height:Number) : Number
      {
         return Math.min(1, Math.max(0.01, Math.min((viewWidth - 16) / width, (viewHeight - 16) / height)));
      }
   }
}
