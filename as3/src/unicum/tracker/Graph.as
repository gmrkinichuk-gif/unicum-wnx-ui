package unicum.tracker
{
   import flash.display.Sprite;
   import flash.events.MouseEvent;
   import flash.geom.Rectangle;

   public class Graph extends Sprite
   {
      public static const WIDTH:Number = 252;
      public static const HEIGHT:Number = 60;

      public function Graph(rows:Array, bars:Boolean, color:uint, hover:Function)
      {
         var plot:Sprite = new Sprite();
         plot.scrollRect = new Rectangle(0, 0, WIDTH, HEIGHT);
         plot.y = 15;
         addChild(plot);
         var maximum:Number = 1;
         for each(var row:Object in rows)
            if(row.wnx != null && isFinite(Number(row.wnx))) maximum = Math.max(maximum, Number(row.wnx));
         maximum = Math.ceil(maximum / 500) * 500;
         Glass.text(this, Glass.number(maximum), 0, 0, 80, 15, 10, 0x909aa8);
         plot.graphics.lineStyle(1, 0x8794a5, 0.14);
         for(var grid:int = 0; grid < 3; grid++)
         {
            plot.graphics.moveTo(0, grid * (HEIGHT - 1) / 2);
            plot.graphics.lineTo(WIDTH, grid * (HEIGHT - 1) / 2);
         }
         var count:int = rows.length;
         if(count == 0) return;
         var step:Number = Geometry.step(WIDTH, count);
         var previous:Boolean = false;
         for(var i:int = 0; i < count; i++)
         {
            row = rows[i];
            var valid:Boolean = row.wnx != null && isFinite(Number(row.wnx));
            var px:Number = bars ? (i + 0.5) * step : (count == 1 ? WIDTH / 2 : i * (WIDTH - 2) / (count - 1) + 1);
            var py:Number = valid ? HEIGHT - 2 - Math.max(0, Number(row.wnx)) / maximum * (HEIGHT - 4) : HEIGHT - 2;
            var ink:uint = row.color != null ? uint(String(row.color).replace("#", "0x")) : color;
            if(bars)
            {
               var bw:Number = Geometry.barWidth(WIDTH, count);
               plot.graphics.lineStyle();
               plot.graphics.beginFill(valid ? Glass.mix(0x8f99a8, ink, 0.65) : 0x8794a5, valid ? 0.85 : 0.35);
               // Unknown is a gap marker, while a real zero gets a solid baseline.
               plot.graphics.drawRect(i * step + (step - bw) / 2, py, bw, valid ? Math.max(1, HEIGHT - 1 - py) : 1);
               plot.graphics.endFill();
            }
            else if(valid)
            {
               plot.graphics.lineStyle(1.5, Glass.mix(0xa8b1bf, color, 0.55), 0.9);
               if(previous) plot.graphics.lineTo(px, py);
               else plot.graphics.moveTo(px, py);
               plot.graphics.beginFill(0xd0d5de);
               plot.graphics.drawCircle(px, py, 1.5);
               plot.graphics.endFill();
               plot.graphics.moveTo(px, py);
            }
            previous = valid;
            var hit:Sprite = new Sprite();
            hit.x = i * step;
            hit.graphics.beginFill(0, 0.001);
            // Adjacent half-open intervals meet but never overlap.
            hit.graphics.drawRect(0, 0, step, HEIGHT);
            hit.graphics.endFill();
            bind(hit, row, hover, bars);
            plot.addChild(hit);
            if(i == 0 || (i + 1) % 5 == 0 || i == count - 1)
               Card.line(this, String(i + 1), Math.max(0, Math.min(WIDTH - 25, px - 12.5)),
                         HEIGHT + 16, 25, 15, 10, 0x909aa8);
         }
      }

      private function bind(hit:Sprite, row:Object, hover:Function, bars:Boolean) : void
      {
         hit.addEventListener(MouseEvent.MOUSE_OVER, function(event:MouseEvent):void { hover(row, bars, hit); });
         hit.addEventListener(MouseEvent.MOUSE_OUT, function(event:MouseEvent):void { hover(null, bars, hit); });
      }
   }
}
