package unicum.tracker
{
   // Avoid a dependency on Flash 11's native JSON in the client's GFx runtime.
   // This bounded codec handles only the JSON primitives our Python bridge uses.
   public class Wire
   {
      private var _text:String;
      private var _at:int = 0;

      public function Wire(text:String) { _text = text; }

      public static function parse(text:String) : Object
      {
         var reader:Wire = new Wire(text);
         var value:Object = reader.read(0);
         reader.space();
         if(reader._at != text.length) throw new Error("Trailing bridge data");
         return value;
      }

      private function space() : void
      {
         while(_at < _text.length && _text.charCodeAt(_at) <= 32) _at++;
      }

      private function read(depth:int) : *
      {
         if(depth > 24) throw new Error("Bridge nesting too deep");
         space();
         var ch:String = _text.charAt(_at);
         if(ch == '"') return stringValue();
         if(ch == "{" || ch == "[")
         {
            _at++;
            var array:Boolean = ch == "[";
            var result:Object = array ? [] : {};
            var close:String = array ? "]" : "}";
            space();
            if(_text.charAt(_at) == close) { _at++; return result; }
            while(_at < _text.length)
            {
               var key:String = "";
               if(!array)
               {
                  space();
                  if(_text.charAt(_at) != '"') throw new Error("Invalid bridge key");
                  key = stringValue();
                  space();
                  if(_text.charAt(_at++) != ":") throw new Error("Missing bridge colon");
               }
               var value:* = read(depth + 1);
               if(array) result.push(value);
               else result[key] = value;
               space();
               ch = _text.charAt(_at++);
               if(ch == close) return result;
               if(ch != ",") throw new Error("Invalid bridge separator");
            }
            throw new Error("Incomplete bridge container");
         }
         for each(var literal:String in ["true", "false", "null"])
         {
            if(_text.substr(_at, literal.length) == literal)
            {
               _at += literal.length;
               return literal == "true" ? true : literal == "false" ? false : null;
            }
         }
         var start:int = _at;
         while(_at < _text.length && "-+0123456789.eE".indexOf(_text.charAt(_at)) >= 0) _at++;
         var token:String = _text.substring(start, _at);
         if(!/^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$/.test(token)) throw new Error("Invalid bridge number");
         var number:Number = Number(token);
         if(!isFinite(number)) throw new Error("Non-finite bridge number");
         return number;
      }

      private function stringValue() : String
      {
         _at++;
         var result:String = "";
         while(_at < _text.length)
         {
            var ch:String = _text.charAt(_at++);
            if(ch == '"') return result;
            if(ch == "\\")
            {
               ch = _text.charAt(_at++);
               var index:int = '"\\/bfnrt'.indexOf(ch);
               if(ch == "u")
               {
                  var hex:String = _text.substr(_at, 4);
                  if(!/^[0-9a-fA-F]{4}$/.test(hex)) throw new Error("Invalid bridge Unicode");
                  result += String.fromCharCode(parseInt(hex, 16));
                  _at += 4;
               }
               else if(index >= 0) result += ['"', "\\", "/", "\b", "\f", "\n", "\r", "\t"][index];
               else throw new Error("Invalid bridge escape");
            }
            else
            {
               if(ch.charCodeAt(0) < 32) throw new Error("Invalid bridge string");
               result += ch;
            }
         }
         throw new Error("Incomplete bridge string");
      }

      public static function stringify(value:*) : String
      {
         if(value == null) return "null";
         if(value is String)
         {
            var escaped:String = '"';
            for(var i:int = 0; i < value.length; i++)
            {
               var ch:String = value.charAt(i);
               var code:int = value.charCodeAt(i);
               if(ch == '"' || ch == "\\") escaped += "\\" + ch;
               else if(code < 32) escaped += "\\u" + ("000" + code.toString(16)).substr(-4);
               else escaped += ch;
            }
            return escaped + '"';
         }
         if(value is Boolean) return value ? "true" : "false";
         if(value is Number) return isFinite(Number(value)) ? String(value) : "null";
         var parts:Array = [];
         if(value is Array)
         {
            for each(var element:* in value) parts.push(stringify(element));
            return "[" + parts.join(",") + "]";
         }
         for(var key:String in value) parts.push(stringify(key) + ":" + stringify(value[key]));
         return "{" + parts.join(",") + "}";
      }
   }
}
