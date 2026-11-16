package unicum
{
   import flash.display.DisplayObjectContainer;
   import flash.display.Sprite;
   import flash.display.Stage;
   import flash.events.Event;
   import flash.geom.Rectangle;
   import flash.text.TextField;
   import flash.text.TextFormat;
   import flash.utils.Dictionary;
   import flash.utils.getTimer;

   // One passive field per row occupies the native text rectangle. The native
   // field keeps its text and geometry so client updates and hit targets survive.
   public class PanelTextSwap
   {
      private static var _owners:Dictionary = new Dictionary(true);
      private var _rows:Dictionary = new Dictionary(true);
      private var _active:Dictionary = new Dictionary(true);
      private var _stage:Stage;
      private var _focus:Boolean = true;
      private var _blocked:Boolean = false;
      private var _held:Boolean = false;
      private var _generation:int = 0;
      private var _created:int = 0;
      private var _ticks:int = 0;
      private var _draws:int = 0;

      public static function owns(tf:TextField) : Boolean
      {
         return _owners[tf] === true;
      }

      public function install(stage:Stage) : void
      {
         if(this._stage != null || stage == null) return;
         this._stage = stage;
         stage.addEventListener(Event.DEACTIVATE, this.deactivate, false, 0, true);
         stage.addEventListener(Event.ACTIVATE, this.activate, false, 0, true);
      }

      private function deactivate(event:Event) : void
      {
         this._focus = false;
         this._blocked = true;
         this.cancel();
      }

      private function activate(event:Event) : void
      {
         this._focus = true;
         // A stale held value must not reappear after Alt+Tab. Release first.
         this._blocked = true;
      }

      public function begin(held:Boolean) : void
      {
         if(!held) this._blocked = false;
         this._held = held && this._focus && !this._blocked;
         this._generation++;
      }

      public function bind(row:DisplayObjectContainer, tf:TextField, id:String,
                           stats:String, enabled:Boolean, statsColor:uint = 0xf2f3f5) : void
      {
         var state:Object = this._rows[row];
         if(row == null || tf == null || tf.parent == null || !tf.visible || !enabled)
         {
            if(state != null) { state.seen = this._generation; release(state); }
            return;
         }
         if(state == null)
         {
            // Lazily allocate on the first Alt hold, never for untouched rows.
            if(!this._held) return;
            var clip:Sprite = new Sprite();
            clip.name = "unicumPanelText";
            clip.mouseEnabled = false;
            clip.mouseChildren = false;
            var text:TextField = new TextField();
            text.mouseEnabled = false;
            text.selectable = false;
            text.multiline = false;
            text.wordWrap = false;
            clip.addChild(text);
            state = {clip:clip, text:text, source:null, position:0, target:0,
                     phase:-1, original:"", stats:"", geometry:"", fit:1, last:getTimer()};
            this._rows[row] = state;
            this._created++;
         }
         state.seen = this._generation;
         if(state.source != tf || state.id != id)
         {
            release(state);
            state.source = tf;
            state.id = id;
            state.alpha = tf.alpha;
            state.original = "";
            state.format = null;
            state.geometry = "";
            state.phase = -1;
         }
         // Native bind/death updates may change the source while it is hidden.
         if(tf.alpha != 0 && owns(tf)) state.alpha = tf.alpha;
         var changed:Boolean = false;
         if(state.original != tf.htmlText || state.format == null || state.statsColor !== statsColor)
         {
            state.original = tf.htmlText;
            state.format = tf.getTextFormat();
            var base:TextFormat = state.format as TextFormat;
            state.statsFormat = new TextFormat(base.font, base.size, statsColor, true,
                                             null, null, null, null, base.align);
            state.statsColor = statsColor;
            state.text.filters = tf.filters;
            changed = true;
         }
         if(state.stats != stats) { state.stats = stats; changed = true; }
         var geometry:String = [tf.x,tf.y,tf.width,tf.height].join(":");
         if(state.geometry != geometry)
         {
            state.geometry = geometry;
            state.clip.x = tf.x;
            state.clip.y = tf.y;
            state.width = tf.width;
            state.text.width = tf.width;
            state.text.height = tf.height;
            state.clip.scrollRect = new Rectangle(0,0,tf.width,tf.height);
            changed = true;
         }
         if(state.clip.parent != tf.parent) tf.parent.addChild(state.clip);
         var target:Number = this._held ? 1 : 0;
         if(state.target != target)
         {
            advance(state, getTimer());
            state.target = target;
            state.last = getTimer();
         }
         if(state.position != state.target) this._active[state] = true;
         if(state.position != 0 || state.target != 0)
         {
            _owners[tf] = true;
            tf.alpha = 0;
            var opening:Boolean = !state.clip.visible;
            state.clip.visible = true;
            if(changed || opening || state.position != state.target) paint(state, changed);
         }
         else release(state);
      }

      public function end() : void
      {
         for(var key:Object in this._rows)
         {
            var state:Object = this._rows[key];
            var row:DisplayObjectContainer = key as DisplayObjectContainer;
            if(state.seen != this._generation || row.stage == null)
            {
               release(state);
               if(state.clip.parent != null) state.clip.parent.removeChild(state.clip);
               delete this._rows[key];
            }
         }
      }

      public function tick(now:int) : void
      {
         for(var key:Object in this._active)
         {
            this._ticks++;
            advance(key, now);
            paint(key, false);
            if(key.position == key.target)
            {
               delete this._active[key];
               if(key.position == 0) release(key);
            }
         }
      }

      private function advance(state:Object, now:int) : void
      {
         state.position = PanelFlip.step(state.position, state.target, now - state.last);
         state.last = now;
      }

      private function paint(state:Object, changed:Boolean) : void
      {
         var phase:int = state.position >= 0.5 ? 1 : 0;
         var tf:TextField = state.text as TextField;
         if(state.phase != phase || changed)
         {
            state.phase = phase;
            if(phase == 1)
            {
               tf.defaultTextFormat = state.statsFormat as TextFormat;
               tf.text = state.stats;
               tf.setTextFormat(state.statsFormat as TextFormat);
            }
            else
            {
               tf.defaultTextFormat = state.format as TextFormat;
               tf.htmlText = state.original;
            }
            state.fit = Math.min(1, state.width / Math.max(1,tf.textWidth + 4));
         }
         var scale:Number = PanelFlip.scale(state.position) * state.fit;
         tf.scaleX = scale;
         tf.x = (state.width - state.width * scale) / 2;
         tf.alpha = PanelFlip.opacity(state.position);
         if(state.source != null) state.source.alpha = 0;
         this._draws++;
      }

      private function release(state:Object) : void
      {
         if(state.source != null && owns(state.source))
         {
            state.source.alpha = state.alpha;
            delete _owners[state.source];
         }
         state.clip.visible = false;
         state.position = state.target = 0;
         state.phase = -1;
         state.last = getTimer();
         delete this._active[state];
      }

      public function cancel() : void
      {
         for(var key:Object in this._rows) release(this._rows[key]);
         this._active = new Dictionary(true);
      }

      public function metrics() : String
      {
         var active:int = 0;
         for(var key:Object in this._active) active++;
         var sample:String = "";
         for(var row:Object in this._rows)
         {
            var state:Object = this._rows[row];
            if(state.target == 1)
            {
               sample = " sample=" + state.stats + " width=" + state.width +
                        " fit=" + state.fit + " progress=" + state.position;
               break;
            }
         }
         return "created=" + this._created + " active=" + active +
                " ticks=" + this._ticks + " draws=" + this._draws + sample;
      }

      public function dispose() : void
      {
         this.cancel();
         for(var key:Object in this._rows)
         {
            var clip:Sprite = this._rows[key].clip as Sprite;
            if(clip.parent != null) clip.parent.removeChild(clip);
         }
         this._rows = new Dictionary(true);
         if(this._stage != null)
         {
            this._stage.removeEventListener(Event.DEACTIVATE, this.deactivate);
            this._stage.removeEventListener(Event.ACTIVATE, this.activate);
            this._stage = null;
         }
      }
   }
}
