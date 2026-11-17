package unicum
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Sprite;
   import flash.filters.DropShadowFilter;
   import flash.geom.Point;
   import flash.geom.Rectangle;
   import flash.text.TextField;
   import flash.text.TextFormat;
   import flash.utils.Dictionary;

   // Passive underlays and separate loading statistics. Native icon/tier/status
   // objects are kept, including their source, transforms and mouse handlers.
   public class RosterRows
   {
      private var _rows:Dictionary = new Dictionary(true);
      private var _effects:Dictionary = new Dictionary(true);
      private var _geometry:Dictionary = new Dictionary(true);

      private var _layout:RosterLayout = new RosterLayout();
      private var _names:RosterNames = new RosterNames();
      private var _loading:Object = {};
      private var _columns:Object = {};

      public function panelGrid(found:Array) : Rectangle
      {
         return this._layout.panel(found);
      }

      public function prepareLoading(allies:Object, enemies:Object) : void
      {
         this._loading = this._layout.loading(allies, enemies);
         this._columns = {};
         for each(var side:String in ["Ally", "Enemy"])
         {
            var icons:Object = side == "Ally" ? allies : enemies;
            if(icons == null) continue;
            var x:Number = Infinity;
            var width:Number = 0;
            for(var i:int = 0; i < icons.length; i++)
            {
               var icon:DisplayObject = icons[i] as DisplayObject;
               if(icon == null || icon.parent == null) continue;
               var suffix:String = icon.name.substr(("vehicleIcon" + side).length);
               var vehicle:TextField = getField(icon.parent, "vehicleField" + side + suffix) as TextField;
               if(vehicle == null) continue;
               light(vehicle);
               var saved:Object = geometry(vehicle);
               x = Math.min(x, saved.x);
               width = Math.max(width, saved.width);
            }
            this._columns[side] = {x:x, width:width};
         }
      }

      public function panel(icon:DisplayObject, row:Object, marker:Array, enabled:Boolean,
                            ally:Boolean, bounds:Rectangle) : void
      {
         if(!enabled || icon == null || icon.parent == null || bounds == null)
         {
            hide(icon);
            return;
         }
         light(getField(row, "playerNameFullTF") as TextField);
         light(getField(row, "playerNameCutTF") as TextField);
         light(getField(row, "vehicleTF") as TextField);
         draw(icon, bounds, marker, true, ally);
      }

      public function loading(icon:DisplayObject, name:TextField, vehicle:TextField,
                              side:String, suffix:String, marker:Array, enabled:Boolean,
                              showStats:Boolean) : Boolean
      {
         if(icon == null || name == null || vehicle == null || icon.parent == null ||
            name.parent != icon.parent || vehicle.parent != icon.parent) return false;
         var grid:Rectangle = this._loading[side] as Rectangle;
         var column:Object = this._columns[side];
         if(!enabled || grid == null || column == null)
         {
            hide(icon);
            return false;
         }
         var parent:DisplayObjectContainer = icon.parent;
         // Disable autosizing before assigning geometry; otherwise a previous
         // native formatter can immediately shrink our newly allocated field.
         light(name);
         light(vehicle);
         geometry(name);
         geometry(vehicle);
         setGeometry(vehicle, column.x, column.width);
         var ally:Boolean = side == "Ally";
         var cells:Object = RosterGrid.loading(grid.left, grid.right,
                            column.x, column.x + column.width, ally, showStats);
         setGeometry(name, cells.nameX, cells.nameWidth);
         this._names.apply(name, marker);
         for each(var prefix:String in ["badge", "squad"])
         {
            var item:DisplayObject = getField(parent, prefix + side + suffix) as DisplayObject;
            if(item != null) centre(item, prefix == "badge" ? cells.badgeX : cells.squadX,
                                    icon.y + grid.height / 2);
         }
         var bounds:Rectangle = new Rectangle(grid.x, icon.y, grid.width, grid.height);
         var state:Object = draw(icon, bounds, marker, false, !ally);
         var statColor:uint = marker != null && marker.currentPlayer ?
                              RosterTextColors.currentColor(name) : 0xf2f3f5;
         for(var i:int = 0; i < 3; i++)
         {
            var tf:TextField = state.stats[i];
            if(tf.textColor != statColor) tf.textColor = statColor;
            var label:String = marker != null && marker.length > 11 + i ? String(marker[11+i]) : "";
            var value:String = label.length ? label : "\u2014";
            if(tf.text != value) tf.text = value;
            if(tf.x != cells.statsX + i * 42) tf.x = cells.statsX + i * 42;
            if(tf.y != icon.y + 2) tf.y = icon.y + 2;
            tf.visible = showStats && icon.visible && name.visible;
         }
         return true;
      }

      private function centre(item:DisplayObject, x:Number, y:Number) : void
      {
         var saved:Object = geometry(item);
         var bounds:Rectangle = item.getBounds(item.parent);
         item.x += x - (bounds.left + bounds.right) / 2;
         item.y += y - (bounds.top + bounds.bottom) / 2;
         saved.lastX = item.x;
         saved.lastY = item.y;
      }

      private function geometry(item:DisplayObject) : Object
      {
         var saved:Object = this._geometry[item];
         if(saved == null)
         {
            saved = {x:item.x, y:item.y, width:item.width, lastX:item.x, lastY:item.y, lastWidth:item.width};
            this._geometry[item] = saved;
         }
         // A client resolution/layout update becomes the new restore target.
         if(item.x != saved.lastX) saved.x = item.x;
         if(item.y != saved.lastY) saved.y = item.y;
         if(item.width != saved.lastWidth) saved.width = item.width;
         return saved;
      }

      private function setGeometry(item:DisplayObject, x:Number, width:Number, resize:Boolean = true) : void
      {
         var saved:Object = this._geometry[item];
         if(item.x != x) item.x = x;
         if(resize && item.width != width) item.width = width;
         saved.lastX = item.x;
         saved.lastWidth = item.width;
      }

      private function light(tf:TextField) : void
      {
         if(tf == null) return;
         if(this._effects[tf] == null)
         {
            this._effects[tf] = {alpha:tf.alpha, filters:tf.filters,
                                wrap:tf.wordWrap, multiline:tf.multiline, auto:tf.autoSize};
            tf.filters = tf.filters.concat([new DropShadowFilter(1, 90, 0, 1, 1, 1, 2, 1)]);
         }
         if(!PanelTextSwap.owns(tf) && tf.alpha != 1) tf.alpha = 1;
         if(tf.wordWrap) tf.wordWrap = false;
         if(tf.multiline) tf.multiline = false;
         if(tf.autoSize != "none") tf.autoSize = "none";
      }

      private function draw(icon:DisplayObject, bounds:Rectangle, marker:Array, compact:Boolean,
                            stripeRight:Boolean) : Object
      {
         var state:Object = this._rows[icon];
         var parent:DisplayObjectContainer = icon.parent;
         if(state == null)
         {
            var bg:Sprite = new Sprite();
            bg.name = "unicumRosterBackground";
            bg.mouseEnabled = false;
            bg.mouseChildren = false;
            state = {bg:bg, stats:[], signature:""};
            this._rows[icon] = state;
         }
         if(!compact && state.stats.length == 0)
         {
            for(var i:int = 0; i < 3; i++)
            {
               var tf:TextField = new TextField();
               tf.name = "unicumRosterStat";
               tf.mouseEnabled = false;
               tf.selectable = false;
               tf.multiline = false;
               tf.wordWrap = false;
               tf.width = 42;
               tf.height = 21;
               tf.defaultTextFormat = new TextFormat("$FieldFont", 12, 0xf2f3f5, true, null, null, null, null, "center");
               tf.filters = [new DropShadowFilter(1, 90, 0, 1, 1, 1, 2, 1)];
               tf.visible = false;
               state.stats.push(tf);
            }
         }
         if(state.bg.parent != parent) parent.addChildAt(state.bg, 0);
         if(!compact) for each(var stat:TextField in state.stats) if(stat.parent != parent) parent.addChild(stat);
         var band:String = marker != null && marker.length > 10 ? String(marker[10]) : "";
         var color:uint = /^#[0-9a-f]{6}$/i.test(band) ? uint(parseInt(band.substr(1),16)) : 0x666b73;
         var signature:String = [bounds.x,bounds.y,bounds.width,bounds.height,color,compact,stripeRight].join(":");
         if(state.signature != signature)
         {
            var bgSprite:Sprite = state.bg as Sprite;
            bgSprite.graphics.clear();
            bgSprite.graphics.beginFill(0x10141b, compact ? 0.90 : 0.96);
            bgSprite.graphics.drawRect(bounds.x,bounds.y,bounds.width,bounds.height);
            bgSprite.graphics.endFill();
            bgSprite.graphics.beginFill(color, compact ? 0.40 : 0.50);
            bgSprite.graphics.drawRect(bounds.x,bounds.y,bounds.width,bounds.height);
            bgSprite.graphics.endFill();
            bgSprite.graphics.beginFill(color,1);
            bgSprite.graphics.drawRect(RosterGrid.stripe(bounds.left,bounds.right,stripeRight),bounds.y,3,bounds.height);
            bgSprite.graphics.endFill();
            state.signature = signature;
         }
         state.bg.visible = icon.visible;
         return state;
      }

      private function hide(icon:DisplayObject) : void
      {
         var state:Object = this._rows[icon];
         if(state == null) return;
         state.bg.visible = false;
         for each(var tf:TextField in state.stats) tf.visible = false;
      }

      public function dispose() : void
      {
         for(var key:Object in this._rows)
         {
            var state:Object = this._rows[key];
            if(state.bg.parent != null) state.bg.parent.removeChild(state.bg);
            for each(var stat:TextField in state.stats) if(stat.parent != null) stat.parent.removeChild(stat);
         }
         this._names.dispose();
         for(key in this._geometry)
         {
            var item:DisplayObject = key as DisplayObject;
            var saved:Object = this._geometry[key];
            if(item.x == saved.lastX) item.x = saved.x;
            if(item.y == saved.lastY) item.y = saved.y;
            if(item.width == saved.lastWidth && item is TextField) item.width = saved.width;
         }
         for(key in this._effects)
         {
            var tf:TextField = key as TextField;
            var effect:Object = this._effects[key];
            tf.alpha = effect.alpha;
            tf.filters = effect.filters;
            tf.wordWrap = effect.wrap;
            tf.multiline = effect.multiline;
            tf.autoSize = effect.auto;
         }
         this._rows = new Dictionary(true);
         this._geometry = new Dictionary(true);
         this._effects = new Dictionary(true);
         this._layout = new RosterLayout();
         this._loading = {};
         this._columns = {};
      }

      private static function getField(target:Object, name:String) : Object
      {
         try { return target[name]; } catch(error:Error) { return null; }
      }
   }
}
