package unicum
{
   import flash.text.TextField;
   import flash.text.TextFormat;
   import flash.utils.Dictionary;

   // The 2.4.1.1 roster and loading SWFs expose named text fields. Only those
   // fields are touched; badges, icons, backgrounds and row geometry remain
   // owned by the client.
   public class RosterTextColors
   {
      private var _original:Dictionary = new Dictionary(true);

      private var _applied:Dictionary = new Dictionary(true);

      private var _text:Dictionary = new Dictionary(true);

      private var _ranges:Dictionary = new Dictionary(true);

      public function apply(row:Object, color:String, names:Boolean, clans:Boolean,
                            vehicles:Boolean, clanTag:String = null,
                            playerName:String = null, fakeName:String = null,
                            currentPlayer:Boolean = false) : void
      {
         var full:TextField = field(row, "playerNameFullTF") as TextField;
         var cut:TextField = field(row, "playerNameCutTF") as TextField;
         var name:TextField = field(row, "playerNameField") as TextField;
         if(name == null)
         {
            name = field(row, "playerNameTF") as TextField;
         }
         if(full == null && name != null)
         {
            full = name;
         }
         if(cut == null && full == null && name != null)
         {
            cut = name;
         }
         var vehicle:TextField = field(row, "vehicleTF") as TextField;
         if(vehicle == null)
         {
            vehicle = field(row, "vehicleNameField") as TextField;
         }
         if(vehicle == null)
         {
            vehicle = field(row, "vehicleNameTF") as TextField;
         }
         var aliases:Array = [playerName, fakeName];
         // Keep the client's current-player colour (including colourblind
         // settings) instead of overwriting the local nickname with white.
         this.setNameColor(full, color, names && !currentPlayer, clans && !currentPlayer, clanTag, aliases);
         if(cut != full)
         {
            this.setNameColor(cut, color, names && !currentPlayer, clans && !currentPlayer, clanTag, aliases);
         }
         this.setColor(vehicle, vehicles && !currentPlayer ? color : null);
      }

      public static function currentColor(field:TextField) : uint
      {
         if(field == null) return 0xf2f3f5;
         var color:Object = field.length ? field.getTextFormat(0,1).color : null;
         return color != null ? uint(color) : field.textColor;
      }

      public function dispose() : void
      {
         for(var key:Object in this._ranges)
         {
            this.restoreRanges(key as TextField);
         }
         for(key in this._original)
         {
            this.write(key as TextField, uint(this._original[key]));
         }
         this._original = new Dictionary(true);
         this._applied = new Dictionary(true);
         this._text = new Dictionary(true);
         this._ranges = new Dictionary(true);
      }

      private function setNameColor(field:TextField, color:String, names:Boolean,
                                    clans:Boolean, clanTag:String, aliases:Array) : void
      {
         if(field == null)
         {
            return;
         }
         var valid:Boolean = color != null && /^#[0-9a-f]{6}$/i.test(color);
         var rgb:uint = valid ? uint(parseInt(color.substr(1), 16)) : 0;
         var ranges:Array = [];
         if(valid && names)
         {
            var player:Object = RosterTextColors.findAlias(field.text, aliases);
            if(player != null)
            {
               ranges.push(player);
            }
            else if(field.length > 0)
            {
               // Older clients can omit the displayed name from the VO. The
               // field is still the player's name cell, so retain a useful
               // colour fallback for that client layout.
               ranges.push({start:0, end:field.length});
            }
         }
         if(valid && clans && clanTag)
         {
            var clan:Object = RosterTextColors.findClan(field.text, clanTag);
            if(clan != null)
            {
               ranges.push(clan);
            }
         }
         this.setRanges(field, rgb, ranges);
      }

      private function setRanges(field:TextField, color:uint, ranges:Array) : void
      {
         var signature:String = String(color) + ":";
         for each(var range:Object in ranges)
         {
            signature += range.start + "-" + range.end + ";";
         }
         var previous:Object = this._ranges[field];
         if(previous != null && previous.text == field.text && previous.signature == signature)
         {
            // The client reapplies some row text formats after setting the
            // same text. Reassert only when its format has replaced our WNX
            // colour; keep the client's new font/weight as the restore value.
            for each(var kept:Object in previous.items)
            {
               var current:TextFormat = field.getTextFormat(kept.start, kept.end);
               if(current.color !== color)
               {
                  kept.format = current;
                  field.setTextFormat(withColor(current, color), kept.start, kept.end);
               }
            }
            return;
         }
         this.restoreRanges(field);
         if(ranges.length == 0 || field.length == 0)
         {
            return;
         }
         var saved:Array = [];
         for each(range in ranges)
         {
            var start:int = Math.max(0, int(range.start));
            var end:int = Math.min(field.length, int(range.end));
            if(end <= start)
            {
               continue;
            }
            var original:TextFormat = field.getTextFormat(start, end);
            saved.push({start:start, end:end, format:original});
            field.setTextFormat(withColor(original, color), start, end);
         }
         if(saved.length > 0)
         {
            this._ranges[field] = {text:field.text, signature:signature,
                                   color:color, items:saved};
         }
      }

      private function restoreRanges(field:TextField) : void
      {
         var state:Object = this._ranges[field];
         if(state == null)
         {
            return;
         }
         if(field != null && field.text == state.text)
         {
            for each(var range:Object in state.items)
            {
               field.setTextFormat(range.format as TextFormat, range.start, range.end);
            }
         }
         delete this._ranges[field];
      }

      private static function withColor(source:TextFormat, color:uint) : TextFormat
      {
         return new TextFormat(source.font, source.size, color, source.bold,
                               source.italic, source.underline, source.url,
                               source.target, source.align, source.leftMargin,
                               source.rightMargin, source.indent, source.leading);
      }

      private static function findAlias(text:String, aliases:Array) : Object
      {
         for each(var alias:Object in aliases)
         {
            if(alias == null || String(alias).length == 0)
            {
               continue;
            }
            var at:int = text.indexOf(String(alias));
            if(at >= 0)
            {
               return {start:at, end:at + String(alias).length};
            }
         }
         return null;
      }

      private static function findClan(text:String, clanTag:String) : Object
      {
         var at:int = text.indexOf(clanTag);
         if(at < 0)
         {
            return null;
         }
         var start:int = at;
         var end:int = at + clanTag.length;
         if(start > 0 && text.charAt(start - 1) == "[")
         {
            start--;
         }
         if(end < text.length && text.charAt(end) == "]")
         {
            end++;
         }
         return {start:start, end:end};
      }

      private function setColor(field:TextField, color:String) : void
      {
         if(field == null)
         {
            return;
         }
         var original:Object = this._original[field];
         if(color == null || !/^#[0-9a-f]{6}$/i.test(color))
         {
            if(original != null)
            {
               this.write(field, uint(original));
               delete this._original[field];
               delete this._applied[field];
               delete this._text[field];
            }
            return;
         }
         var rgb:uint = uint(parseInt(color.substr(1), 16));
         if(original == null)
         {
            this._original[field] = field.textColor;
         }
         var overwritten:Boolean = field.length > 0 &&
                                   field.getTextFormat(0, field.length).color !== rgb;
         if(this._applied[field] !== rgb || this._text[field] != field.text || overwritten)
         {
            this.write(field, rgb);
            this._applied[field] = rgb;
            this._text[field] = field.text;
         }
      }

      private function write(field:TextField, color:uint) : void
      {
         if(field == null)
         {
            return;
         }
         field.textColor = color;
         if(field.length > 0)
         {
            field.setTextFormat(new TextFormat(null, null, color));
         }
      }

      private static function field(target:Object, name:String) : Object
      {
         try
         {
            return target[name];
         }
         catch(e:Error)
         {
            return null;
         }
         return null;
      }
   }
}
