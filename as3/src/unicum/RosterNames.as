package unicum
{
   import flash.text.TextField;
   import flash.utils.Dictionary;
   import net.wg.data.constants.UserTags;
   import net.wg.infrastructure.interfaces.IUserProps;

   // Re-run the client's own formatter after layout. Its previous output has
   // already lost the truncated suffix, so changing width alone cannot recover it.
   public class RosterNames
   {
      private var _saved:Dictionary = new Dictionary(true);

      public static function isCurrent(marker:Array) : Boolean
      {
         return marker != null && marker.length >= 20 &&
                UserTags.isCurrentPlayer(String(marker[18]).length ? String(marker[18]).split(",") : []);
      }

      public function apply(tf:TextField, marker:Array) : void
      {
         if(tf == null || marker == null || marker.length < 20 || marker[19] != "1") return;
         var tags:Array = String(marker[18]).length ? String(marker[18]).split(",") : [];
         var self:Boolean = UserTags.isCurrentPlayer(tags);
         var token:String = marker.slice(14,20).join("\t") + ":" + tf.width;
         var state:Object = this._saved[tf];
         if(state != null && state.token == token && tf.text == state.applied) return;
         if(state == null)
         {
            state = {original:tf.htmlText};
            this._saved[tf] = state;
         }
         else if(tf.text != state.applied) state.original = tf.htmlText;
         var props:IUserProps = App.utils.commons.getUserProps(String(marker[14]),
            String(marker[16]), String(marker[17]), 0, tags, String(marker[15]));
         App.utils.commons.formatPlayerName(tf, props, !self, self);
         state.token = token;
         state.applied = tf.text;
      }

      public function dispose() : void
      {
         for(var key:Object in this._saved)
         {
            var tf:TextField = key as TextField;
            var state:Object = this._saved[key];
            if(tf.text == state.applied) tf.htmlText = state.original;
         }
         this._saved = new Dictionary(true);
      }
   }
}
