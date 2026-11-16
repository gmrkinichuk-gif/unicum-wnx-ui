package unicum.markers
{
   import flash.display.DisplayObject;
   import flash.display.Sprite;
   import flash.events.Event;
   import flash.text.TextField;

   // What our marker classes add to the client's vehicle marker: the latest
   // NameMarkerView from unicum.markers.swf, right of the marker's own player
   // name, and every call Python makes for it. The view is rebuilt when that
   // SWF is loaded again (see MarkersBoot.as), and the calls replayed.
   //
   // It reads where the name is drawn from the marker itself, every frame, so
   // it follows whatever the marker shows: ALT, settings, a shortened name.
   public class NameMarkerAddon
   {
      private var _marker:Sprite;

      private var _view:DisplayObject = null;

      private var _calls:Object = {};

      private var _disposed:Boolean = false;

      private var _layout:Function;

      private var _anchorPoll:int = 0;

      public function NameMarkerAddon(marker:Sprite)
      {
         super();
         this._marker = marker;
         MarkersBoot.addons[this] = true;
         MarkersBoot.ensureLoaded();
         this.rebuild();
      }

      public function dispose() : void
      {
         if(this._disposed)
         {
            return;
         }
         this._disposed = true;
         delete MarkersBoot.addons[this];
         this.removeView();
         this._calls = {};
         this._layout = null;
         this._player = null;
         this._vehicle = null;
         this._marker = null;
      }

      public function call(name:String, args:Array) : void
      {
         if(this._disposed)
         {
            return;
         }
         this._calls[name] = args;
         this.forward(name, args);
      }

      public function rebuild() : void
      {
         this.removeView();
         if(this._disposed || MarkersBoot.view == null)
         {
            return;
         }
         this._view = new MarkersBoot.view() as DisplayObject;
         if(this._view == null)
         {
            return;
         }
         this._marker.addChild(this._view);
         try { this._layout = Object(this._view)["layout"] as Function; }
         catch(error:Error) { this._layout = null; }
         this._view.addEventListener(Event.ENTER_FRAME, this.onFrame);
         this.anchors();
         for(var name:String in this._calls)
         {
            this.forward(name, this._calls[name]);
         }
      }

      private function nameField() : TextField
      {
         try
         {
            return Object(this._marker)["playerNameField"] as TextField;
         }
         catch(e:Error)
         {
         }
         return null;
      }

      private function onFrame(event:Event) : void
      {
         // Symbols normally keep the same fields for the marker's lifetime.
         // Recheck often enough to catch a client mode rebuild, without two
         // dynamic property lookups for every marker on every frame.
         this._anchorPoll++;
         if(this._anchorPoll >= 6 || this._player == null || this._vehicle == null)
         {
            this._anchorPoll = 0;
            if(this.nameField() != this._player || this.vehicleField() != this._vehicle)
               this.anchors();
         }
         try
         {
            if(this._layout != null) this._layout.call(this._view);
         }
         catch(error:Error)
         {
         }
      }

      private var _player:TextField;
      private var _vehicle:TextField;

      private function vehicleField() : TextField
      {
         try { return Object(this._marker)["vehicleNameField"] as TextField; }
         catch(error:Error) { }
         return null;
      }

      private function anchors() : void
      {
         this._player = this.nameField();
         this._vehicle = this.vehicleField();
         this.forward("setAnchor", [this._player]);
         var health:DisplayObject;
         var typeIcon:DisplayObject;
         try { health = Object(this._marker)["healthBar"] as DisplayObject; }
         catch(error:Error) { }
         try { typeIcon = Object(this._marker)["marker2"] as DisplayObject; }
         catch(error:Error) { }
         this.forward("setVehicleAnchor", [this._vehicle, health, typeIcon]);
      }

      private function removeView() : void
      {
         if(this._view != null)
         {
            this._view.removeEventListener(Event.ENTER_FRAME, this.onFrame);
            this.forward("dispose", []);
            if(this._view.parent != null)
            {
               this._view.parent.removeChild(this._view);
            }
            this._view = null;
            this._layout = null;
            this._anchorPoll = 0;
         }
      }

      private function forward(name:String, args:Array) : void
      {
         if(this._view == null)
         {
            return;
         }
         try
         {
            var method:Function = Object(this._view)[name] as Function;
            if(method != null)
            {
               method.apply(this._view, args);
            }
         }
         catch(e:Error)
         {
         }
      }
   }
}
