package unicum
{
   // Primitive bridge fields shared by loading rows and native panel overlays.
   public class RosterOptions
   {
      public static var signature:String = "";
      public static var loadingBackground:Boolean = true;
      public static var loadingStripe:Boolean = true;
      public static var loadingOpacity:Number = 0.5;
      public static var loadingStats:Array = [true, true, true];
      public static var panelBackground:Boolean = true;
      public static var panelStripe:Boolean = true;
      public static var panelOpacity:Number = 0.4;
      public static var altStats:int = 0;
      public static var animation:Boolean = true;
      public static var duration:Number = 150;

      public static function read(value:String) : Boolean
      {
         if(value == signature || value == null || value.length == 0) return false;
         var fields:Array = value.split(",");
         if(fields.length != 12) return false;
         signature = value;
         loadingBackground = fields[0] == "1";
         loadingStripe = fields[1] == "1";
         loadingOpacity = Math.max(0, Math.min(100, Number(fields[2]))) / 100;
         loadingStats = [fields[3] == "1", fields[4] == "1", fields[5] == "1"];
         panelBackground = fields[6] == "1";
         panelStripe = fields[7] == "1";
         panelOpacity = Math.max(0, Math.min(100, Number(fields[8]))) / 100;
         altStats = Math.max(0, Math.min(4, int(fields[9])));
         animation = fields[10] == "1";
         duration = Math.max(50, Math.min(300, Number(fields[11])));
         return true;
      }
   }
}
