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
      public static const WIDTH:int = 760;
      public static const HEIGHT:int = 516;
      private static const VIEW_HEIGHT:int = 350;
      private static const CHOICE_COUNT:int = 6;
      private static const CHOICE_ROW:int = 30;
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
      private var _choiceBottom:Number;
      private var _lastEscape:int = -1000;
      private var _saveRequest:uint;
      private var _closeAfterSave:Boolean;
      private var _saveError:String = "";

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
         if(_saveRequest == 0) draw();
         else if(state.saveResult != null && state.saveResult.request == _saveRequest)
            finishSave(state.saveResult);
      }

      public function discard() : void
      {
         _draft = {};
         _modal = null;
         _saveError = "";
         draw();
      }

      public function value(item:Object) : *
      {
         return _draft.hasOwnProperty(item.var) ? _draft[item.var] : item.value;
      }

      public function accent() : uint
      {
         return uint(String(_state.color).replace("#", "0x"));
      }

      public function change(variable:String, nextValue:*, redraw:Boolean = true) : void
      {
         if(_saveRequest != 0) return;
         _draft[variable] = nextValue;
         if(_apply != null) _apply.alpha = 1;
         if(redraw) draw();
      }

      private function save(close:Boolean) : void
      {
         if(_saveRequest != 0) return;
         if(!dirty())
         {
            if(close) dismiss();
            return;
         }
         _closeAfterSave = close;
         _saveError = "";
         _saveRequest = _owner.applySettings(_draft);
         draw();
      }

      private function finishSave(result:Object) : void
      {
         _saveRequest = 0;
         _saveError = result.error;
         if(_saveError == "") _draft = {};
         else if(_saveError == "account")
         {
            var remaining:Object = {};
            for each(var key:String in result.retry)
               if(_draft.hasOwnProperty(key)) remaining[key] = _draft[key];
            _draft = remaining;
         }
         if(_saveError == "" && _closeAfterSave) dismiss();
         else draw();
      }

      private function dismiss() : void
      {
         if(_saveRequest == 0) _owner.closeSettings();
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

      private function tabButton(index:int, color:uint) : void
      {
         Card.button(this, _state.categories[index].title, 14, 66 + index * 42, 166, 36,
                     function():void { chooseCategory(index); }, color, index == _category ? "selected" : "tab", "left");
      }

      private function draw() : void
      {
         closePopup();
         Glass.clear(this);
         var color:uint = accent();
         var surface:Sprite = Glass.raisedPanel(this, WIDTH, HEIGHT, color, 0.96);
         TrackerIcons.draw(this, TrackerIcons.SETTINGS, 18, 17, 20);
         Card.line(this, "Unicum WNX UI  \u00b7  " + _owner.word("Settings"), 47, 10, 630, 34, 19, 0xe3e8f2, "left");
         Card.button(this, "\u00d7", WIDTH - 45, 12, 30, 30, dismiss, color, "tab");
         Card.rule(surface, 14, 54, WIDTH - 28, 0);
         Card.rule(surface, 190, 54, 0, 409);
         Card.rule(surface, 14, 463, WIDTH - 28, 0);
         for(var i:int = 0; i < _state.categories.length; i++) tabButton(i, color);
         var category:Object = _state.categories[_category];
         Card.line(this, category.title, 208, 65, 526, 28, 18, 0xe3e8f2, "left");
         Card.rule(surface, 208, 96, 526, 0);
         _viewport = new Sprite();
         _viewport.x = 208;
         _viewport.y = 105;
         _viewport.scrollRect = new Rectangle(0, 0, 534, VIEW_HEIGHT);
         addChild(_viewport);
         _content = new Sprite();
         _viewport.addChild(_content);
         var position:Number = 0;
         var group:String = "";
         var controls:SettingsControls = new SettingsControls(this);
         for each(var item:Object in category.rows)
         {
            if(item.group != group && item.group != "")
            {
               group = item.group;
               Card.line(_content, group, 0, position + 3, SettingsControls.WIDTH, 24, 13, 0xaeb9c8, "left");
               position += 34;
            }
            position += controls.row(_content, item, position);
         }
         _limit = Math.max(0, position - VIEW_HEIGHT);
         scrollTo(_scroll);
         Card.button(this, _owner.word("Cancel"), 399, 476, 112, 30, dismiss, color);
         _apply = Card.button(this, _owner.word("Apply"), 521, 476, 124, 30,
                              function():void { save(false); }, color, "primary");
         _apply.alpha = dirty() ? 1 : 0.5;
         Card.button(this, _owner.word("OK"), 655, 476, 87, 30, function():void { save(true); }, color);
         if(_modal != null) confirmation();
         drawSaveStatus();
      }

      private function drawSaveStatus() : void
      {
         if(_saveRequest != 0)
         {
            Card.line(this, _owner.word("Saving settings..."), 16, 475, 369, 30, 12, 0xa3acbb, "left");
            var lock:Sprite = new Sprite();
            lock.graphics.beginFill(0, 0.001);
            lock.graphics.drawRect(0, 0, WIDTH, HEIGHT);
            lock.graphics.endFill();
            addChild(lock);
         }
         else if(_saveError != "")
         {
            var message:String = _saveError == "account" ? "Could not save some account settings. Try again." :
                                 "Could not save settings. Try again.";
            Glass.text(this, _owner.word(message), 16, 472, 369, 38, 12, 0xe0a5a5);
         }
      }

      private function dirty() : Boolean
      {
         for(var key:String in _draft) return true;
         return false;
      }

      private function scrollTo(offset:Number) : void
      {
         _scroll = Math.max(0, Math.min(offset, _limit));
         if(_content != null) _content.y = -_scroll;
         // A thin scrollbar signals long categories without occupying a row.
         if(_viewport != null)
         {
            _viewport.graphics.clear();
            if(_limit > 0)
            {
               _viewport.graphics.beginFill(0xb2baca, 0.4);
               _viewport.graphics.drawRect(529, (_scroll / _limit) * (VIEW_HEIGHT - 50), 2, 50);
               _viewport.graphics.endFill();
            }
         }
      }

      private function wheel(event:MouseEvent) : void
      {
         event.stopImmediatePropagation();
         if(_modal == null && _choice == null) scrollTo(_scroll - event.delta * 30);
      }

      public function openChoices(item:Object, top:Point, bottom:Number) : void
      {
         closePopup();
         _choice = item;
         _choicePoint = top;
         _choiceBottom = bottom;
         _choiceStart = Math.max(0, Math.min(item.options.length - CHOICE_COUNT, int(value(item)) - int(item.offset) - 2));
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
         var menuWidth:Number = SettingsControls.WIDTH;
         var length:int = Math.min(CHOICE_COUNT, _choice.options.length);
         var menuHeight:Number = length * CHOICE_ROW + 12;
         var below:Number = _choiceBottom + 5;
         menu.x = Math.max(208, Math.min(_choicePoint.x, WIDTH - menuWidth - 16));
         menu.y = below + menuHeight <= _viewport.y + VIEW_HEIGHT ? below :
                  Math.max(_viewport.y, _choicePoint.y - menuHeight - 5);
         var surface:Sprite = Glass.raisedPanel(menu, menuWidth, menuHeight, accent(), 0.99);
         _popup.addChild(menu);
         for(var i:int = 0; i < length; i++) choiceButton(menu, i + _choiceStart, i);
         var limit:int = _choice.options.length - length;
         if(limit > 0)
         {
            var track:Number = menuHeight - 14;
            var thumb:Number = track * length / _choice.options.length;
            surface.graphics.lineStyle();
            surface.graphics.beginFill(Glass.mix(0xb2baca, accent(), 0.30), 0.62);
            surface.graphics.drawRoundRect(menuWidth - 8, 7 + (track - thumb) * _choiceStart / limit, 2, thumb, 2, 2);
            surface.graphics.endFill();
         }
         _popup.addEventListener(MouseEvent.MOUSE_WHEEL, function(event:MouseEvent):void {
            event.stopImmediatePropagation();
            var next:int = Math.max(0, Math.min(limit, _choiceStart - event.delta));
            if(next == _choiceStart) return;
            _choiceStart = next;
            drawChoices();
         });
      }

      private function choiceButton(menu:Sprite, index:int, position:int) : void
      {
         var width:Number = SettingsControls.WIDTH - (_choice.options.length > CHOICE_COUNT ? 18 : 12);
         Card.button(menu, _choice.options[index], 6, 6 + position * CHOICE_ROW, width, CHOICE_ROW - 2, function():void {
            var variable:String = _choice.var;
            var selected:int = index + int(_choice.offset);
            closePopup();
            change(variable, selected);
         }, accent(), index == int(value(_choice)) - int(_choice.offset) ? "selected" : "tab", "left");
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
         box.x = (WIDTH - 528) / 2;
         box.y = (HEIGHT - 278) / 2;
         _popup.addChild(box);
         var color:uint = accent();
         var surface:Sprite = Glass.raisedPanel(box, 528, 278, color, 1);
         var history:Boolean = _modal == "tracker_reset";
         Card.line(box, _owner.word(history ? "Reset statistics?" : "Reset mod settings?"), 20, 12, 461, 30, 19, 0xe3e8f2, "left");
         Card.rule(surface, 18, 48, 492, 0);
         Glass.text(box, _owner.word("This action cannot be undone."), 22, 57, 480, 26, 13, 0xe0a5a5);
         Glass.text(box, _owner.word(history ? "All local random-battle history for the current account will be deleted. Graphs and session WNX will start again." : "Restore mod defaults? Tracker history and account link remain unchanged."), 22, 92, 480, 74, 13);
         if(history) Glass.text(box, _owner.word("Total WNX on Unicum.gg, replays and mod settings remain unchanged."), 22, 168, 480, 45, 12, 0xa3acbb);
         Card.rule(surface, 18, 221, 492, 0);
         Card.button(box, "\u00d7", 488, 12, 24, 30, cancelModal, color, "tab");
         Card.button(box, _owner.word("Cancel"), 264, 232, 116, 30, cancelModal, color);
         Card.button(box, _owner.word("Reset"), 390, 232, 116, 30, function():void {
            var variable:String = _modal;
            cancelModal();
            _owner.send({kind:"confirmed","var":variable});
         }, color, "danger");
      }

      private function cancelModal() : void
      {
         _modal = null;
         closePopup();
      }

      public function escape() : void
      {
         if(_saveRequest != 0) return;
         var now:int = getTimer();
         if(now - _lastEscape < 150) return;
         _lastEscape = now;
         if(_modal != null) cancelModal();
         else if(_popup != null) closePopup();
         else dismiss();
      }

      private function key(event:KeyboardEvent) : void
      {
         if(_saveRequest != 0)
         {
            event.stopImmediatePropagation();
            event.preventDefault();
            return;
         }
         if(_popup == null && stage != null && stage.focus is OpacitySlider && contains(stage.focus) &&
            OpacitySlider(stage.focus).adjust(event.keyCode))
         {
            event.preventDefault();
            event.stopImmediatePropagation();
            return;
         }
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
               else if(point.y + target.height > _scroll + VIEW_HEIGHT) scrollTo(point.y + target.height - VIEW_HEIGHT);
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
