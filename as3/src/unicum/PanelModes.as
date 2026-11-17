package unicum
{
   import flash.text.TextField;
   import net.wg.data.constants.generated.PLAYERS_PANEL_STATE;

   public class PanelModes
   {
      public static function target(row:Object) : TextField
      {
         // Other battle types can expose icon rows without the random
         // battle's public state API. Leave their native text untouched.
         try
         {
         switch(int(row.state))
         {
            case PLAYERS_PANEL_STATE.MEDIUM:
            case PLAYERS_PANEL_STATE.MEDIUM_NO_BADGES:
               return row.playerNameCutTF as TextField;
            case PLAYERS_PANEL_STATE.LONG:
            case PLAYERS_PANEL_STATE.LONG_NO_BADGES:
               return row.vehicleTF as TextField;
            case PLAYERS_PANEL_STATE.FULL:
            case PLAYERS_PANEL_STATE.FULL_NO_BADGES:
               return row.playerNameFullTF as TextField;
         }
         }
         catch(error:Error) { }
         return null;
      }

      public static function statistics(row:Object, marker:Array) : String
      {
         if(marker == null) return "\u2014";
         if(RosterOptions.altStats >= 1 && RosterOptions.altStats <= 3)
            return String(marker[10 + RosterOptions.altStats] || "\u2014");
         if(RosterOptions.altStats == 4) return marker.hasStats ? marker.statsLine : "\u2014";
         try
         {
            var full:Boolean = int(row.state) == PLAYERS_PANEL_STATE.FULL ||
                               int(row.state) == PLAYERS_PANEL_STATE.FULL_NO_BADGES;
            // Medium and Long have deliberately narrow native text slots.
            // Keep the rating legible instead of compressing three values.
            if(full) return marker.hasStats ? marker.statsLine : "\u2014";
            return String(marker[11] || "\u2014");
         }
         catch(error:Error) { }
         return "";
      }
   }
}
