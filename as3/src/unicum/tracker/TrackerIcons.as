package unicum.tracker
{
   import flash.display.Bitmap;
   import flash.display.BitmapData;
   import flash.display.Loader;
   import flash.display.Sprite;
   import flash.events.Event;
   import flash.events.IOErrorEvent;
   import flash.events.SecurityErrorEvent;
   import flash.net.URLRequest;

   public class TrackerIcons
   {
      public static const DAMAGE:String = "../maps/icons/statistic/avgDamage24.png";
      public static const ASSIST:String = "../maps/icons/statistic/assist24.png";
      public static const SETTINGS:String = "../maps/icons/buttons/settings.png";
      private static var _cache:Object = {};

      public static function draw(parent:Sprite, path:String, x:Number, y:Number, size:Number) : void
      {
         var target:Sprite = new Sprite();
         target.mouseEnabled = target.mouseChildren = false;
         target.x = x;
         target.y = y;
         parent.addChild(target);
         var held:* = _cache[path];
         if(held is BitmapData) add(target, BitmapData(held), size);
         else if(held is Array) held.push([target, size]);
         else if(held !== false)
         {
            _cache[path] = [[target, size]];
            load(path);
         }
      }

      private static function add(target:Sprite, data:BitmapData, size:Number) : void
      {
         if(target.parent == null) return;
         var icon:Bitmap = new Bitmap(data);
         icon.smoothing = true;
         icon.width = icon.height = size;
         target.addChild(icon);
      }

      private static function load(path:String) : void
      {
         var loader:Loader = new Loader();
         var finish:Function = function(event:Event = null):void
         {
            loader.contentLoaderInfo.removeEventListener(Event.COMPLETE, finish);
            loader.contentLoaderInfo.removeEventListener(IOErrorEvent.IO_ERROR, finish);
            loader.contentLoaderInfo.removeEventListener(SecurityErrorEvent.SECURITY_ERROR, finish);
            var bitmap:Bitmap = event != null && event.type == Event.COMPLETE ? loader.content as Bitmap : null;
            var waiting:Array = _cache[path] as Array;
            _cache[path] = bitmap != null ? bitmap.bitmapData : false;
            if(bitmap != null)
               for each(var request:Array in waiting) add(request[0], bitmap.bitmapData, request[1]);
         };
         loader.contentLoaderInfo.addEventListener(Event.COMPLETE, finish);
         loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, finish);
         loader.contentLoaderInfo.addEventListener(SecurityErrorEvent.SECURITY_ERROR, finish);
         try { loader.load(new URLRequest(path)); }
         catch(error:Error) { finish(); }
      }
   }
}
