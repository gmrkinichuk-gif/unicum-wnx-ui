package unicum
{
   // Pure reversible progress, shared with the browser regression harness.
   public class PanelFlip
   {
      public static const DURATION:Number = 150;

      public static function step(position:Number, target:Number, elapsed:Number, duration:Number = 150) : Number
      {
         var distance:Number = Math.max(0, elapsed) / Math.max(50, Math.min(300, duration));
         return target > position ? Math.min(target, position + distance) :
                                    Math.max(target, position - distance);
      }

      public static function scale(position:Number) : Number
      {
         var value:Number = Math.abs(position * 2 - 1);
         return 0.04 + 0.96 * value * value * (3 - 2 * value);
      }

      public static function opacity(position:Number) : Number
      {
         return Math.min(1, Math.abs(position * 2 - 1) * 1.8);
      }
   }
}
