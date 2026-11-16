package unicum
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.geom.Point;
   import flash.geom.Rectangle;
   import flash.text.TextField;
   import flash.utils.Dictionary;
   import flash.utils.getTimer;

   // Measure a whole team, never one player's texture or already shortened text.
   public class RosterLayout
   {
      private var _panels:Dictionary = new Dictionary(true);
      private var _loading:Object = null;
      private var _loadingAt:int = 0;
      private var _loadingToken:String = "";

      public function panel(found:Array) : Rectangle
      {
         if(!found.length) return null;
         var key:Object = found[0].row;
         var mode:String = "";
         try { mode = String(found[0].row.state); } catch(error:Error) { }
         var token:String = [found[0].icon.x, found.length, mode].join(":");
         var old:Object = this._panels[key];
         if(old != null && old.token == token && getTimer() - old.time < 200) return old.bounds;
         var bounds:Rectangle = null;
         var pitch:Number = found.length > 1 ? Math.abs(found[1].row.y - found[0].row.y) : 25;
         for each(var item:Object in found)
         {
            var row:DisplayObjectContainer = item.row as DisplayObjectContainer;
            for(var i:int = 0; i < row.numChildren; i++)
            {
               var child:DisplayObject = row.getChildAt(i);
               var text:TextField = child as TextField;
               // Atlas backgrounds and hit rectangles include reserved
               // interaction space rather than just visible row content.
               if(!child.visible || (child.alpha <= 0 && !PanelTextSwap.owns(text)) ||
                  child.name.indexOf("unicum") == 0 ||
                  /(^hit$|bg$)/i.test(child.name) ||
                  child.width <= 0 || child.height <= 0 || child.width > 1000) continue;
               var rect:Rectangle = child.getBounds(row);
               bounds = bounds == null ? rect : bounds.union(rect);
            }
         }
         if(bounds == null) return null;
         bounds.y = 0;
         bounds.height = Math.max(1, Math.min(24, pitch - 1));
         this._panels[key] = {bounds:bounds, token:token, time:getTimer()};
         return bounds;
      }

      public function loading(allies:Object, enemies:Object) : Object
      {
         var first:DisplayObject = allies != null && allies.length ? allies[0] as DisplayObject : null;
         var token:String = first != null && first.stage != null ?
            [first.stage.stageWidth, first.parent != null ? first.parent.x : 0, first.x].join(":") : "";
         if(this._loading != null && token == this._loadingToken && getTimer() - this._loadingAt < 200)
            return this._loading;
         var left:Object = team(allies, true);
         var right:Object = team(enemies, false);
         if(left == null || right == null) return {};
         // One shared width in stage coordinates makes both teams symmetric.
         var width:Number = Math.max(0, Math.min(600 * Math.min(left.unit, right.unit),
                     left.inner - 16, right.stageWidth - right.inner - 16));
         this._loading = {Ally:box(left, left.inner - width, left.inner),
                          Enemy:box(right, right.inner, right.inner + width)};
         this._loadingAt = getTimer();
         this._loadingToken = token;
         return this._loading;
      }

      private static function team(icons:Object, ally:Boolean) : Object
      {
         if(icons == null || !icons.length) return null;
         var first:DisplayObject = icons[0] as DisplayObject;
         if(first == null || first.parent == null || first.stage == null) return null;
         var parent:DisplayObjectContainer = first.parent;
         var inner:Number = ally ? -Infinity : Infinity;
         var ys:Array = [];
         for(var i:int = 0; i < icons.length; i++)
         {
            var icon:DisplayObject = icons[i] as DisplayObject;
            if(icon == null || icon.parent != parent) continue;
            var bounds:Rectangle = icon.getBounds(icon.stage);
            inner = ally ? Math.max(inner, bounds.right + 4) : Math.min(inner, bounds.left - 4);
            ys.push(icon.y);
         }
         ys.sort(Array.NUMERIC);
         var pitch:Number = 25;
         for(i = 1; i < ys.length; i++) if(ys[i] > ys[i-1]) pitch = Math.min(pitch, ys[i] - ys[i-1]);
         var origin:Point = parent.localToGlobal(new Point(0,0));
         var unit:Number = Math.abs(parent.localToGlobal(new Point(1,0)).x - origin.x);
         return {parent:parent, inner:inner, unit:Math.max(0.01,unit),
                 stageWidth:first.stage.stageWidth, height:Math.max(1,Math.min(24,pitch-1))};
      }

      private static function box(team:Object, left:Number, right:Number) : Rectangle
      {
         var parent:DisplayObjectContainer = team.parent as DisplayObjectContainer;
         var x:Number = parent.globalToLocal(new Point(left,0)).x;
         var end:Number = parent.globalToLocal(new Point(right,0)).x;
         return new Rectangle(x, 0, end - x, team.height);
      }
   }
}
