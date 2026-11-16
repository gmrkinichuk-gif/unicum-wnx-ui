package unicum
{
   // Pure geometry, also exercised by the offline regression harness.
   public class RosterGrid
   {
      public static function loading(left:Number, right:Number, vehicleLeft:Number,
                                     vehicleRight:Number, ally:Boolean, shown:Boolean) : Object
      {
         var stats:Number = shown ? 126 : 0;
         var statX:Number = ally ? vehicleLeft - 6 - stats : vehicleRight + 6;
         var nameLeft:Number = ally ? left + 64 : statX + stats + 6;
         var nameRight:Number = ally ? statX - 6 : right - 64;
         return {nameX:nameLeft, nameWidth:Math.max(0, nameRight - nameLeft),
                 statsX:statX, badgeX:ally ? left + 44 : right - 44,
                 squadX:ally ? left + 14 : right - 14};
      }

      public static function stripe(left:Number, right:Number, atRight:Boolean) : Number
      {
         return atRight ? right - 3 : left;
      }
   }
}
