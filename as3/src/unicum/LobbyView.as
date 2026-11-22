package unicum
{
   import net.wg.infrastructure.base.AbstractView;
   import unicum.tracker.TrackerRoot;

   // Lobby host for the hangar Tracker.
   public class LobbyView extends AbstractView
   {
      private var _tracker:TrackerRoot;

      public function setTrackerState(value:String) : void
      {
         if(_tracker != null) _tracker.update(value);
      }

      public function takeTrackerOut() : String
      {
         return _tracker != null ? _tracker.take() : "";
      }

      public function hideTracker() : void { if(_tracker != null) _tracker.hide(); }
      public function resetTrackerPosition() : void { if(_tracker != null) _tracker.resetPosition(); }
      public function discardTrackerDraft() : void { if(_tracker != null) _tracker.discardDraft(); }
      public function escapeTrackerSettings() : Boolean { return _tracker != null && _tracker.escapeSettings(); }

      public function LobbyView()
      {
         super();
      }

      override protected function configUI() : void
      {
         super.configUI();
         mouseEnabled = false;
         this._tracker = new TrackerRoot(this);
      }

      override protected function onDispose() : void
      {
         if(this._tracker != null) this._tracker.dispose();
         super.onDispose();
      }
   }
}
