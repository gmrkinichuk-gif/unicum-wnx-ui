package unicum
{
   import flash.display.DisplayObject;
   import flash.display.Sprite;
   import flash.geom.Rectangle;
   import flash.text.TextField;
   import flash.text.TextFormatAlign;

   // Passive vertical WNX accent beside the visible native marker text.
   public class NameMarkerStripe extends Sprite
   {
      private var _signature:String = "";
      private var _token:String = "";
      private var _field:TextField;
      private var _host:DisplayObject;
      private var _health:DisplayObject;
      private var _obstacle:DisplayObject;
      private var _right:Number = 0;

      public function get contentRight() : Number { return this._right; }

      public function NameMarkerStripe()
      {
         mouseEnabled = false;
         mouseChildren = false;
         visible = false;
      }

      public function update(player:TextField, vehicle:TextField,
                             health:DisplayObject, color:Number, obstacle:DisplayObject = null) : void
      {
         // Same neutral grey as the players-panel and Tab row accents.
         // -1 means unavailable WNX; -2 keeps a disabled marker hidden.
         if(color == -1) color = 0x666b73;
         var field:TextField = player != null && player.visible && player.text.length ? player : vehicle;
         if(parent == null || parent.parent == null || field == null || field.parent == null ||
            !field.visible || !field.text.length || isNaN(color) || color < 0 || color > 0xffffff)
         {
            visible = false;
            return;
         }
         var other:TextField = field == player ? vehicle : player;
         var token:String = [field.x,field.y,field.width,field.height,field.scaleX,field.scaleY,field.textWidth,field.textHeight,
            field.rotation,field.htmlText,parent.x,parent.y,parent.scaleX,parent.scaleY,color,
            other != null ? [other.x,other.y,other.width,other.height,other.visible,other.htmlText,other.textWidth,other.textHeight].join(":") : "",
            obstacle != null ? [obstacle.x,obstacle.y,obstacle.width,obstacle.height,obstacle.visible].join(":") : "",
            health != null ? [health.x,health.y,health.width,health.height,health.visible].join(":") : ""].join(":");
         if(this._field == field && this._host == parent && this._health == health &&
            this._obstacle == obstacle && this._token == token)
         {
            visible = true;
            return;
         }
         this._field = field;
         this._host = parent;
         this._health = health;
         this._obstacle = obstacle;
         this._token = token;
         var box:Rectangle = field.getBounds(parent);
         var height:Number = Math.max(1,Math.min(box.height - 4,
                                   Math.max(8,field.textHeight * Math.abs(field.scaleY))));
         var left:Number = this.textRight(field) + 3;
         var top:Number = box.top + (box.height - height) / 2;
         // Shift only our accent sideways if a native label or icon shares
         // its vertical band. Never consume the HP/type-icon area below it.
         if(other != null && other.parent != null && other.visible && other.text.length)
         {
            var label:Rectangle = other.getBounds(parent);
            if(top - 1 < label.bottom && top + height + 1 > label.top)
               left = Math.max(left,this.textRight(other) + 3);
         }
         if(health != null && health.parent != null && health.visible)
         {
            var bar:Rectangle = health.getBounds(parent);
            if(top - 1 < bar.bottom && top + height + 1 > bar.top)
               left = Math.max(left,bar.right + 3);
         }
         var cut:Rectangle = obstacle != null && obstacle.parent != null && obstacle.visible ? obstacle.getBounds(parent) : null;
         if(cut != null && top - 1 < cut.bottom && top + height + 1 > cut.top)
            left = Math.max(left,cut.right + 3);
         left = Math.round(left);
         top = Math.round(top);
         height = Math.round(height);
         this._right = left + 4;
         var signature:String = [left,top,height,color].join(":");
         if(signature != this._signature)
         {
            graphics.clear();
            graphics.beginFill(0x000000,0.95);
            graphics.drawRect(left-1,top-1,5,height+2);
            graphics.endFill();
            graphics.beginFill(uint(color),1);
            graphics.drawRect(left,top,3,height);
            graphics.endFill();
            this._signature = signature;
         }
         visible = true;
      }

      private function textRight(field:TextField) : Number
      {
         var box:Rectangle = field.getBounds(parent);
         var width:Number = Math.min(box.width,(field.textWidth + 4) * Math.abs(field.scaleX));
         var align:String = field.getTextFormat().align;
         if(align == TextFormatAlign.RIGHT) return box.right;
         if(align == TextFormatAlign.CENTER) return box.left + (box.width + width) / 2;
         return box.left + width;
      }

      public function dispose() : void
      {
         this._field = null;
         this._host = null;
         this._health = null;
         this._obstacle = null;
         this._token = this._signature = "";
         this._right = 0;
         graphics.clear();
         visible = false;
      }
   }
}
