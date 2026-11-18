package unicum.tracker
{
   import flash.display.Sprite;
   import flash.display.InteractiveObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.DisplayObject;
   import flash.events.MouseEvent;
   import flash.events.KeyboardEvent;
   import flash.geom.Rectangle;
   import flash.geom.Point;
   import flash.text.TextField;
   import flash.text.TextFieldType;
   import flash.utils.getTimer;

   public class TrackerSettings extends Sprite
   {
      public static const WIDTH:int = 720;
      public static const HEIGHT:int = 560;
      private var _owner:TrackerRoot;
      private var _state:Object;
      private var _draft:Object = {};
      private var _category:int = 0;
      private var _viewport:Sprite;
      private var _content:Sprite;
      private var _scroll:Number = 0;
      private var _limit:Number = 0;
      private var _popup:Sprite;
      private var _modal:String;
      private var _previousFocus:InteractiveObject;
      private var _apply:Sprite;
      private var _choice:Object;
      private var _choiceStart:int;
      private var _choicePoint:Point;
      private var _lastEscape:int = -1000;

      public function TrackerSettings(owner:TrackerRoot, state:Object)
      {
         _owner = owner;
         _state = state;
         tabEnabled = true;
         addEventListener(MouseEvent.MOUSE_WHEEL, wheel);
         addEventListener(MouseEvent.MOUSE_DOWN, absorb);
         addEventListener(MouseEvent.CLICK, absorb);
      }

      public function activate() : void
      {
         if(stage != null)
         {
            _previousFocus = stage.focus;
            stage.focus = this;
            stage.addEventListener(KeyboardEvent.KEY_DOWN, key, true, 100);
         }
         draw();
      }

      private function absorb(event:MouseEvent) : void { event.stopPropagation(); }

      public function update(state:Object) : void
      {
         _state = state;
         draw();
      }

      public function discard() : void
      {
         _draft = {};
         _modal = null;
         draw();
      }

      public function value(item:Object) : *
      {
         return _draft.hasOwnProperty(item.var) ? _draft[item.var] : item.value;
      }

      public function change(variable:String, value:*, redraw:Boolean = true) : void
      {
         _draft[variable] = value;
         if(_apply != null) _apply.alpha = 1;
         if(redraw) draw();
      }

      private function save(close:Boolean) : void
      {
         _owner.send({kind:"apply",values:_draft});
         _draft = {};
         if(close) _owner.closeSettings();
         else draw();
      }

      public function action(variable:String) : void
      {
         if(variable == "tracker_reset" || variable == "resetDefaults")
         {
            _modal = variable;
            confirmation();
         }
         else _owner.send({kind:"button","var":variable});
      }

      private function chooseCategory(index:int) : void
      {
         _category = index;
         _scroll = 0;
         draw();
      }

      private function tabButton(index:int) : void
      {
         Glass.button(this, _state.categories[index].title, 12, 68 + index * 42, 170,
                      function():void { chooseCategory(index); }, false, index == _category, 34);
      }

      private function draw() : void
      {
         closePopup();
         Glass.clear(this);
         Glass.panel(this, WIDTH, HEIGHT, uint(String(_state.color).replace("#", "0x")), 0.96);
         Glass.text(this, "Unicum WNX UI  \u00b7  " + _owner.word("Settings"), 22, 15, 640, 30, 18);
         Glass.button(this, "\u00d7", 678, 14, 26, function():void { _owner.closeSettings(); });
         graphics.lineStyle(1, 0x8794a5, 0.2);
         graphics.moveTo(194, 60); graphics.lineTo(194, 506);
         graphics.moveTo(20, 510); graphics.lineTo(700, 510);
         for(var i:int = 0; i < _state.categories.length; i++) tabButton(i);
         _viewport = new Sprite();
         _viewport.x = 214;
         _viewport.y = 66;
         _viewport.scrollRect = new Rectangle(0, 0, 490, 430);
         addChild(_viewport);
         _content = new Sprite();
         _viewport.addChild(_content);
         var position:Number = 0;
         var group:String = "";
         var controls:SettingsControls = new SettingsControls(this);
         for each(var item:Object in _state.categories[_category].rows)
         {
            if(item.group != group && item.group != "")
            {
               group = item.group;
               Glass.text(_content, group, 0, position + 4, 480, 24, 13, 0xb4bbca);
               position += 34;
            }
            position += controls.row(_content, item, position);
         }
         _limit = Math.max(0, position - 430);
         scrollTo(_scroll);
         Glass.button(this, _owner.word("Cancel"), 386, 523, 100, function():void { _owner.closeSettings(); });
         _apply = Glass.button(this, _owner.word("Apply"), 494, 523, 114, function():void { save(false); });
         _apply.alpha = dirty() ? 1 : 0.5;
         Glass.button(this, _owner.word("OK"), 616, 523, 84, function():void { save(true); });
         if(_modal != null) confirmation();
      }

      private function dirty() : Boolean
      {
         for(var key:String in _draft) return true;
         return false;
      }

      private function scrollTo(value:Number) : void
      {
         _scroll = Math.max(0, Math.min(value, _limit));
         if(_content != null) _content.y = -_scroll;
         // A thin scrollbar signals long categories without occupying a row.
         if(_viewport != null)
         {
            _viewport.graphics.clear();
            if(_limit > 0)
            {
               _viewport.graphics.beginFill(0xb2baca, 0.4);
               _viewport.graphics.drawRect(486, (_scroll / _limit) * 370, 2, 60);
               _viewport.graphics.endFill();
            }
         }
      }

      private function wheel(event:MouseEvent) : void
      {
         event.stopImmediatePropagation();
         if(_modal == null && _choice == null) scrollTo(_scroll - event.delta * 30);
      }

      public function openChoices(item:Object, point:Point) : void
      {
         closePopup();
         _choice = item;
         _choicePoint = point;
         _choiceStart = Math.max(0, Math.min(item.options.length - 6, int(value(item)) - int(item.offset) - 2));
         drawChoices();
      }

      private function drawChoices() : void
      {
         if(_popup != null && _popup.parent == this) removeChild(_popup);
         _popup = new Sprite();
         addChild(_popup);
         _popup.graphics.beginFill(0, 0.001);
         _popup.graphics.drawRect(0, 0, WIDTH, HEIGHT);
         _popup.graphics.endFill();
         _popup.addEventListener(MouseEvent.CLICK, function(event:MouseEvent):void { event.stopPropagation(); closePopup(); });
         var menu:Sprite = new Sprite();
         menu.x = Math.max(202, Math.min(_choicePoint.x, WIDTH - 498));
         var length:int = Math.min(6, _choice.options.length);
         menu.y = Math.max(60, Math.min(_choicePoint.y, HEIGHT - 52 - length * 30));
         Glass.panel(menu, 488, length * 30 + 6, 0x697183, 1);
         _popup.addChild(menu);
         for(var i:int = 0; i < length; i++) choiceButton(menu, i + _choiceStart, i);
         _popup.addEventListener(MouseEvent.MOUSE_WHEEL, function(event:MouseEvent):void {
            event.stopImmediatePropagation();
            _choiceStart = Math.max(0, Math.min(_choice.options.length - length, _choiceStart - event.delta));
            drawChoices();
         });
      }

      private function choiceButton(menu:Sprite, index:int, position:int) : void
      {
         Glass.button(menu, _choice.options[index], 4, 3 + position * 30, 480, function():void {
            var variable:String = _choice.var;
            var selected:int = index + int(_choice.offset);
            closePopup();
            change(variable, selected);
         }, false, index == int(value(_choice)) - int(_choice.offset));
      }

      private function closePopup() : void
      {
         if(_popup != null && _popup.parent == this) removeChild(_popup);
         _popup = null;
         _choice = null;
      }

      private function confirmation() : void
      {
         closePopup();
         _popup = new Sprite();
         addChild(_popup);
         _popup.graphics.beginFill(0x080b10, 0.72);
         _popup.graphics.drawRoundRect(0, 0, WIDTH, HEIGHT, 12, 12);
         _popup.graphics.endFill();
         var box:Sprite = new Sprite();
         box.x = 96;
         box.y = 136;
         _popup.addChild(box);
         Glass.panel(box, 528, 278, uint(String(_state.color).replace("#", "0x")), 1);
         var history:Boolean = _modal == "tracker_reset";
         Glass.text(box, _owner.word(history ? "Reset statistics?" : "Reset mod settings?"), 22, 18, 480, 30, 19);
         Glass.text(box, _owner.word("This action cannot be undone."), 22, 57, 480, 26, 13, 0xe0a5a5);
         Glass.text(box, _owner.word(history ? "All local random-battle history for the current account will be deleted. Graphs and session WNX will start again." : "Restore mod defaults? Tracker history and account link remain unchanged."), 22, 92, 480, 74, 13);
         if(history) Glass.text(box, _owner.word("Total WNX on Unicum.gg, replays and mod settings remain unchanged."), 22, 168, 480, 45, 12, 0xa3acbb);
         Glass.button(box, "\u00d7", 488, 16, 24, cancelModal);
         Glass.button(box, _owner.word("Cancel"), 264, 232, 116, cancelModal);
         Glass.button(box, _owner.word("Reset"), 390, 232, 116, function():void {
            var variable:String = _modal;
            cancelModal();
            _owner.send({kind:"confirmed","var":variable});
         }, true);
      }

      private function cancelModal() : void { _modal = null; closePopup(); }

      public function escape() : void
      {
         var now:int = getTimer();
         if(now - _lastEscape < 150) return;
         _lastEscape = now;
         if(_modal != null) cancelModal();
         else if(_popup != null) closePopup();
         else _owner.closeSettings();
      }

      private function key(event:KeyboardEvent) : void
      {
         if(event.keyCode == 27)
         {
            event.stopImmediatePropagation();
            escape();
         }
         else if(event.keyCode == 9)
         {
            event.preventDefault();
            event.stopImmediatePropagation();
            var available:Array = [];
            collect(_popup != null ? _popup : this, available);
            if(available.length == 0) return;
            var index:int = available.indexOf(stage.focus);
            index = (index + (event.shiftKey ? available.length - 1 : 1)) % available.length;
            var target:InteractiveObject = available[index];
            stage.focus = target;
            if(_popup == null && _content.contains(target))
            {
               var point:Point = _content.globalToLocal(target.localToGlobal(new Point()));
               if(point.y < _scroll) scrollTo(point.y);
               else if(point.y + target.height > _scroll + 430) scrollTo(point.y + target.height - 430);
            }
         }
         else if((event.keyCode == 13 || event.keyCode == 32) && stage.focus is Sprite && contains(stage.focus))
         {
            event.stopImmediatePropagation();
            stage.focus.dispatchEvent(new MouseEvent(MouseEvent.CLICK));
         }
         else event.stopPropagation();
      }

      private function collect(parent:DisplayObjectContainer, output:Array) : void
      {
         for(var i:int = 0; i < parent.numChildren; i++)
         {
            var child:DisplayObject = parent.getChildAt(i);
            if(!child.visible) continue;
            if(child is InteractiveObject && InteractiveObject(child).tabEnabled) output.push(child);
            else if(child is TextField && TextField(child).type == TextFieldType.INPUT) output.push(child);
            if(child is DisplayObjectContainer) collect(DisplayObjectContainer(child), output);
         }
      }

      public function dispose() : void
      {
         if(stage != null)
         {
            stage.removeEventListener(KeyboardEvent.KEY_DOWN, key, true);
            try { stage.focus = _previousFocus; } catch(error:Error) { }
         }
         removeEventListener(MouseEvent.MOUSE_WHEEL, wheel);
         removeEventListener(MouseEvent.MOUSE_DOWN, absorb);
         removeEventListener(MouseEvent.CLICK, absorb);
         Glass.clear(this);
      }
   }
}
