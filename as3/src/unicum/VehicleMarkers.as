package unicum
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.events.Event;
   import flash.geom.Point;
   import flash.geom.Rectangle;
   import flash.text.TextField;
   import flash.text.TextFormatAlign;
   import flash.utils.Dictionary;
   import flash.utils.getTimer;

   // Rating badge and flags for each player in the battle's Scaleform
   // screens, the badge nearest the row. In the players panel they sit beside
   // the vehicle icon: right of it for allies, left of it for enemies, where
   // the icon is nearest the middle of the screen. A Tab table packs a row
   // from edge to edge, so there they sit outside each team's rows, where the
   // team's average joins its badge column on the team name's line.
   //
   // Part of the battle view (TeamNamesHtml.as); Python (src/unicum/battle.py)
   // gives the markup per vehicle and the order of each team.
   //
   // No row names its vehicle, but every one of these screens lays a team out
   // in the order the statistics controller sends (leftItemsIDs /
   // rightItemsIDs), so a row's place gives its vehicle:
   //
   //   players panel   an object with listLeft and listRight; each list has
   //                   a container of rows, each with its vehicleIcon, set at
   //                   the row height times its place in that order; rows in
   //                   more than one column are left alone
   //   Tab (tables)    an object with vehicleIconCollection, one icon per
   //                   row of both teams; which half is which varies by mode,
   //                   so a team is the icons on its side of the screen
   //   loading screen  an object with vehicleIconsAlly and vehicleIconsEnemy
   //
   // The random battle's Tab is Gameface and has no such objects.
   //
   // A team's markers form two columns, badges then flags, so they line up
   // however wide each vehicle's icon is drawn or each rating is written.
   //
   // The client already puts things on that side of the icon -- health bars,
   // chat command pings, spotted indicators, prestige -- and each mode or mod
   // may add its own. So rather than a list per mode, the columns start past
   // the farthest visible neighbour on their side, in the icons' band:
   // whatever shows there pushes them out, and they come back when it hides.
   public class VehicleMarkers
   {
      // Between the icon's edge and the badge column.
      private static const GAP:int = 6;

      // Between the badge column and the flags column.
      private static const SPACE:int = 4;

      // A TextField's gutter, before its first image.
      private static const GUTTER:int = 2;

      private static const HEIGHT:int = 20;

      // A field draws its images this much higher than its middle (measured
      // in the players panel: a badge's centre 2px above its row's), so a
      // field centred on a row is lowered by it.
      private static const IMAGE_RISE:int = 2;

      // Wider than any neighbour: a row background spans the whole row.
      private static const MAX_NEIGHBOUR_WIDTH:int = 200;

      private static const NAME:String = "unicumMarkers";

      // A team name the client set with its average: "name  <average sign> <IMG .../>".
      public static const AVERAGE:RegExp = /^(.*?)\s*\u00d8\s*(<IMG.*)$/s;

      private static const WIDTH:RegExp = /width="(\d+)"/i;

      // The same, every match of it. A team average was one badge when
      // this was written and is two since the win rate joined it, and a
      // field sized from the first `width` alone clips everything after
      // it -- the figure is drawn, in a box one badge wide.
      private static const WIDTHS:RegExp = /width="(\d+)"/gi;

      // Between two badges in one field, matching the space the markup
      // puts there and what Python measures it at (battle/markup.py).
      private static const BADGE_GAP:int = 4;

      // Backgrounds and hit areas, which lie under the icon and its neighbours.
      private static const BACKGROUND:RegExp = /(bg|hit|background)$/i;

      // vehicle id -> [badge, width, flags, width, WNX hex, clan, name,
      //                fake name, long WNX badge, width]
      private var _markers:Object = {};

      private var _left:Array = [];

      private var _right:Array = [];

      private var _given:Array = [null, null, null];

      private var _panels:Dictionary = new Dictionary(true);

      private var _tables:Dictionary = new Dictionary(true);

      private var _loadings:Dictionary = new Dictionary(true);

      // vehicle icon -> [badge field, flags field]
      private var _fields:Dictionary = new Dictionary(true);

      // field -> the markup last set on it
      private var _html:Dictionary = new Dictionary(true);

      private var _rosterColors:RosterTextColors = new RosterTextColors();

      private var _rosterRows:RosterRows = new RosterRows();

      private var _swaps:PanelTextSwap = new PanelTextSwap();

      // Native text fields do not emit CHANGE on client writes. A bounded
      // fallback catches them; only moving text is updated on every frame.
      private var _drawAt:int = 0;

      private var _redesign:Boolean = false;

      private var _rosterStats:Boolean = false;

      private var _colorNames:Boolean = false;

      private var _colorClanTags:Boolean = false;

      private var _colorVehicles:Boolean = false;

      private var _panelWnxBadgesVisible:Boolean = false;

      // team name field -> [the name left in it, the average taken out]
      private var _averages:Dictionary = new Dictionary(true);

      // team name field -> [badge field, average sign field]
      private var _averageFields:Dictionary = new Dictionary(true);

      private var _names:Dictionary = null;

      public function VehicleMarkers()
      {
         super();
      }

      private static function field(target:Object, name:String) : Object
      {
         try
         {
            return target[name];
         }
         catch(e:Error)
         {
         }
         return null;
      }

      // A hidden loading/Tab branch can remain on stage for the whole battle.
      // Its descendants inherit visibility/alpha, so updating all 30 rows at
      // 20 Hz cannot affect the screen and only burns CPU. Unknown non-display
      // hosts stay enabled for compatibility with older client proxies.
      private static function displayed(target:Object) : Boolean
      {
         var node:DisplayObject = target as DisplayObject;
         if(node == null) return true;
         if(node.stage == null) return false;
         while(node != null)
         {
            if(!node.visible || node.alpha <= 0) return false;
            node = node.parent;
         }
         return true;
      }

      // How many of the three kinds of screen the search has found. Drives the
      // rescan in TeamNamesHtml, and counts rather than answering yes/no: the
      // loading screen is the one that exists while this view is still
      // starting, so "found anything" was true from the first scan and stopped
      // the rescan before the players panel and the Tab table had ever been
      // built. The rescan then looked like it changed nothing, which is not
      // the same as there being nothing to find.
      public function found() : int
      {
         var count:int = 0;
         var key:Object = null;
         for(key in this._panels)
         {
            count++;
            break;
         }
         for(key in this._tables)
         {
            count++;
            break;
         }
         for(key in this._loadings)
         {
            count++;
            break;
         }
         return count;
      }

      public function inspect(target:Object) : void
      {
         if(field(target, "listLeft") != null && field(target, "listRight") != null)
         {
            if(!this._panels[target] && target is DisplayObjectContainer)
               target.addEventListener("stateChanged", this.panelStateChanged, false, 0, true);
            this._panels[target] = true;
            this._drawAt = 0;
         }
         if(field(target, "vehicleIconCollection") != null)
         {
            this._tables[target] = true;
         }
         if(field(target, "vehicleIconsAlly") != null && field(target, "vehicleIconsEnemy") != null)
         {
            this._loadings[target] = true;
         }
      }

      private function panelStateChanged(event:Event) : void
      {
         this._swaps.cancel();
         this._drawAt = 0;
         this._revision++;
      }

      // names: team name field -> [the text the client set, the text once
      // shown as HTML], kept by TeamNamesHtml, since a name already shown as
      // HTML no longer reads back its average's tag.
      public function update(markers:String, left:String, right:String, names:Dictionary,
                             panelHidden:Boolean = false, tabHidden:Boolean = false,
                             loadingHidden:Boolean = false, colorNames:Boolean = false,
                             colorClanTags:Boolean = false, colorVehicles:Boolean = false,
                             showBadges:Boolean = false,
                             panelWnxBadgesVisible:Boolean = false,
                             redesign:Boolean = false, rosterStats:Boolean = false) : void
      {
         var revision:int = this._revision;
         if(this._rosterStats != rosterStats)
         {
            this._rosterStats = rosterStats;
            this._revision++;
         }
         if(redesign != this._redesign)
         {
            this._swaps.cancel();
            this._rosterRows.dispose();
            this._redesign = redesign;
            this._revision++;
         }
         var hiding:String = String(panelHidden) + String(tabHidden) + String(loadingHidden);
         if(hiding != this._hiding)
         {
            this._hiding = hiding;
            this._revision++;
         }
         if(colorNames != this._colorNames || colorClanTags != this._colorClanTags ||
            colorVehicles != this._colorVehicles ||
            panelWnxBadgesVisible != this._panelWnxBadgesVisible)
         {
            this._colorNames = colorNames;
            this._colorClanTags = colorClanTags;
            this._colorVehicles = colorVehicles;
            this._panelWnxBadgesVisible = panelWnxBadgesVisible;
            this._revision++;
         }
         this._names = names;
         this.read(markers, left, right);
         var now:int = getTimer();
         this._swaps.install(App.stage);
         this._swaps.tick(now);
         if(now < this._drawAt && revision == this._revision) return;
         this._drawAt = now + 50;
         this._swaps.begin(panelWnxBadgesVisible);
         // No ids: every row's fields are hidden, as for a player with no rating.
         for(var panel:Object in this._panels)
         {
            if(!displayed(panel)) continue;
            this.drawList(field(panel, "listLeft") as DisplayObjectContainer, this._left, true, panelHidden);
            this.drawList(field(panel, "listRight") as DisplayObjectContainer, this._right, false, panelHidden);
         }
         for(var table:Object in this._tables)
         {
            if(!displayed(table)) continue;
            this.drawTable(table, tabHidden);
         }
         for(var loading:Object in this._loadings)
         {
            if(!displayed(loading)) continue;
            if(this._redesign) this._rosterRows.prepareLoading(field(loading, "vehicleIconsAlly"), field(loading, "vehicleIconsEnemy"));
            this.drawIcons(field(loading, "vehicleIconsAlly"), this._left, true, loadingHidden);
            this.drawIcons(field(loading, "vehicleIconsEnemy"), this._right, false, loadingHidden);
         }
         this._swaps.end();
      }

      public function animationMetrics() : String
      {
         return this._swaps.metrics();
      }

      public function dispose() : void
      {
         this._swaps.dispose();
         for(var panel:Object in this._panels)
            if(panel is DisplayObjectContainer)
               panel.removeEventListener("stateChanged", this.panelStateChanged);
         for each(var owned:Dictionary in [this._fields, this._averageFields])
         {
            for(var key:Object in owned)
            {
               for each(var shown:TextField in owned[key])
               {
                  if(shown.parent != null)
                  {
                     shown.parent.removeChild(shown);
                  }
               }
            }
         }
         for(var team:Object in this._averages)
         {
            // Give the name back its average, as the client set it.
            var name:TextField = team as TextField;
            if(name.text == this._averages[team][0])
            {
               name.htmlText = this._averages[team][0] + "  \u00d8 " + this._averages[team][1];
            }
         }
         this._averages = new Dictionary(true);
         this._averageFields = new Dictionary(true);
         this._fields = new Dictionary(true);
         this._html = new Dictionary(true);
         this._rosterColors.dispose();
         this._rosterRows.dispose();
         this._panels = new Dictionary(true);
         this._tables = new Dictionary(true);
         this._loadings = new Dictionary(true);
      }

      // The client's Scaleform has no JSON: markers come one vehicle a line,
      // "id TAB badge TAB badge width TAB flags TAB flags width TAB WNX hex",
      // and orders as comma separated ids.
      private function read(markers:String, left:String, right:String) : void
      {
         if(markers != this._given[0])
         {
            this._revision++;
            this._given[0] = markers;
            this._markers = {};
            for each(var line:String in (markers || "").split("\n"))
            {
               var parts:Array = line.split("\t");
               if(parts.length >= 5)
               {
                  this._markers[parts[0]] = [parts[1], Number(parts[2]), parts[3], Number(parts[4]),
                                             parts.length >= 6 ? parts[5] : "",
                                             parts.length >= 7 ? parts[6] : "",
                                             parts.length >= 8 ? parts[7] : "",
                                             parts.length >= 9 ? parts[8] : "",
                                             parts.length >= 10 ? parts[9] : "",
                                             parts.length >= 11 ? Number(parts[10]) : 0,
                                             parts.length >= 12 ? parts[11] : "",
                                             parts.length >= 13 ? parts[12] : "",
                                             parts.length >= 14 ? parts[13] : "",
                                             parts.length >= 15 ? parts[14] : "",
                                             parts.length >= 16 ? parts[15] : "",
                                             parts.length >= 17 ? parts[16] : "",
                                             parts.length >= 18 ? parts[17] : "",
                                             parts.length >= 19 ? parts[18] : "",
                                             parts.length >= 20 ? parts[19] : "",
                                             parts.length >= 21 ? parts[20] : ""];
                  var marker:Array = this._markers[parts[0]] as Array;
                  marker.hasStats = Boolean(marker[11] || marker[12] || marker[13]);
                  marker.currentPlayer = RosterNames.isCurrent(marker);
                  // Assemble once per payload, never per Alt frame. A missing
                  // value is a dash, not an invented zero or another rating.
                  marker.statsLine = [marker[11] || "\u2014", marker[12] || "\u2014",
                                      marker[13] || "\u2014"].join(" | ");
               }
            }
         }
         if(left != this._given[1])
         {
            this._revision++;
            this._given[1] = left;
            this._left = left ? left.split(",") : [];
         }
         if(right != this._given[2])
         {
            this._revision++;
            this._given[2] = right;
            this._right = right ? right.split(",") : [];
         }
      }

      private function drawList(list:DisplayObjectContainer, ids:Array, ally:Boolean, hidden:Boolean) : void
      {
         var rows:DisplayObjectContainer = rowsOf(list);
         if(rows == null)
         {
            return;
         }
         // A row's place in the team is its place from the top: the list
         // sets each row at its index times the row height, whatever that
         // height is. Rows side by side are a layout whose order is not known.
         var found:Array = [];
         for(var i:int = 0; i < rows.numChildren; i++)
         {
            var rowDisplay:DisplayObjectContainer = rows.getChildAt(i) as DisplayObjectContainer;
            var icon:DisplayObject = rowDisplay != null ? field(rowDisplay, "vehicleIcon") as DisplayObject : null;
            if(icon != null)
            {
               if(found.length > 0 && Math.round(rowDisplay.x) != Math.round(found[0].row.x))
               {
                  return;
               }
               found.push({"row":rowDisplay, "icon":icon});
            }
         }
         found.sort(function(a:Object, b:Object) : Number
         {
            return a.row.y - b.row.y;
         });
         var icons:Array = [];
         var rowIds:Array = [];
         var shown:Array = [];
         var replacement:Boolean = false;
         var grid:Rectangle = this._redesign ? this._rosterRows.panelGrid(found) : null;
         for(i = 0; i < found.length; i++)
         {
            var rosterRow:Object = found[i].row;
            var marker:Array = ids[i] != null ? this._markers[String(ids[i])] as Array : null;
            var color:String = this._redesign ? "#f2f3f5" : (marker != null ? String(marker[4]) : null);
            this._rosterColors.apply(rosterRow, color, this._colorNames, this._colorClanTags,
                                     this._colorVehicles, marker != null ? marker[5] : null,
                                     marker != null ? marker[6] : null,
                                     marker != null ? marker[7] : null,
                                     marker != null && marker.currentPlayer);
            this._rosterRows.panel(found[i].icon, rosterRow, marker, this._redesign, ally, grid);
            var text:TextField = PanelModes.target(rosterRow);
            var statistics:String = PanelModes.statistics(rosterRow, marker);
            replacement = replacement || (this._redesign && this._rosterStats && text != null);
            this._swaps.bind(rosterRow as DisplayObjectContainer, text, String(ids[i]),
                             statistics,
                             this._redesign && this._rosterStats && statistics.length > 0 &&
                             !hidden && rosterRow.visible && list.visible,
                             marker != null && marker.currentPlayer ? RosterTextColors.currentColor(text) : 0xf2f3f5);
            icons.push(found[i].icon);
            rowIds.push(ids[i]);
            shown.push(!hidden && rosterRow.visible && list.visible);
         }
         this.placeTeam(icons, rowIds, shown, ally, NaN,
                        this._panelWnxBadgesVisible && !replacement);
      }

      // The list's child whose children are rows: the list also holds the
      // voice chat button, backgrounds and indicators, in no fixed order.
      private static function rowsOf(list:DisplayObjectContainer) : DisplayObjectContainer
      {
         if(list == null)
         {
            return null;
         }
         for(var i:int = 0; i < list.numChildren; i++)
         {
            var child:DisplayObjectContainer = list.getChildAt(i) as DisplayObjectContainer;
            if(child != null && child.numChildren > 0 && field(child.getChildAt(0), "vehicleIcon") != null)
            {
               return child;
            }
         }
         return null;
      }

      private function drawTable(table:Object, hidden:Boolean) : void
      {
         var icons:Object = field(table, "vehicleIconCollection");
         var count:int = icons != null ? int(icons.length) : 0;
         this.colorTableRows(icons, count);
         // Working the teams' middle out measures every icon, and the placing
         // that follows measures every neighbour of every row, so both wait
         // for something to move. The averages are placed either way: they
         // are two fields, and a team whose average is not placed loses it.
         var kept:Object = this._placed[table];
         if(this.settled(table, this.readingOf(icons, count)) && kept != null && kept.result != null)
         {
            this.placeAverages(table, kept.result.middle, kept.result.left, kept.result.right, hidden);
            return;
         }
         var middle:Number = 0;
         var placed:int = 0;
         for(var i:int = 0; i < count; i++)
         {
            var icon:DisplayObject = icons[i] as DisplayObject;
            if(icon != null && icon.parent != null)
            {
               middle += centre(icon);
               placed++;
            }
         }
         if(placed == 0)
         {
            return;
         }
         middle /= placed;
         // Each half keeps the collection's order, which is its rows' order.
         var lefts:Array = [];
         var rights:Array = [];
         for(i = 0; i < count; i++)
         {
            icon = icons[i] as DisplayObject;
            if(icon != null && icon.parent != null)
            {
               (centre(icon) < middle ? lefts : rights).push(icon);
            }
         }
         var leftColumn:Array = this.placeTeam(lefts, hidden ? [] : this._left, null, false, middle);
         var rightColumn:Array = this.placeTeam(rights, hidden ? [] : this._right, null, true, middle);
         if(this._placed[table] != null)
         {
            this._placed[table].result = {"middle":middle, "left":leftColumn, "right":rightColumn};
         }
         this.placeAverages(table, middle, leftColumn, rightColumn, hidden);
      }

      // Each team's average, moved from its name into its badge column.
      private function placeAverages(table:Object, middle:Number, leftColumn:Array, rightColumn:Array,
                                     hidden:Boolean) : void
      {
         for each(var name:String in ["team1TF", "team2TF"])
         {
            var team:TextField = field(table, name) as TextField;
            if(team != null && team.parent != null)
            {
               var left:Boolean = centre(team) < middle;
               this.placeAverage(team, left ? leftColumn : rightColumn, !left, hidden);
            }
         }
      }

      private static function centre(item:DisplayObject) : Number
      {
         var bounds:Rectangle = item.getBounds(item.parent);
         return item.parent.localToGlobal(new Point(bounds.x + bounds.width / 2, 0)).x;
      }

      // Moves a team's average out of its name into the team's badge column,
      // the average sign where the flags go. [edge, badges width], or null
      // while no player's markers are drawn, leaves the name as it is.
      // Hidden, the average is kept out of the name and not drawn.
      private function placeAverage(team:TextField, column:Array, rightwards:Boolean, hidden:Boolean) : void
      {
         var taken:Array = this._averages[team] as Array;
         if(taken == null || team.text != taken[0])
         {
            // New text from the client since: take its average, if any.
            taken = null;
            var set:String = team.text;
            var shown:Array = this._names != null ? this._names[team] as Array : null;
            if(set.indexOf("<IMG") < 0 && shown != null && set == shown[1])
            {
               set = shown[0];
            }
            var found:Object = AVERAGE.exec(set);
            if(found != null && WIDTH.test(found[2]))
            {
               taken = [found[1], found[2]];
            }
         }
         var fields:Array = this._averageFields[team] as Array;
         if(hidden)
         {
            if(taken != null)
            {
               if(team.text != taken[0])
               {
                  team.text = taken[0];
               }
               this._averages[team] = taken;
            }
            for each(var unshown:TextField in fields)
            {
               unshown.visible = false;
            }
            return;
         }
         if(taken == null || column == null)
         {
            if(taken == null)
            {
               delete this._averages[team];
            }
            else if(team.text == taken[0])
            {
               // No column any more: the average goes back after the name.
               team.htmlText = taken[0] + "  \u00d8 " + taken[1];
               delete this._averages[team];
            }
            else
            {
               // The name is not the one the average was taken out of, so it
               // cannot go back into it yet. What was taken is kept, or the
               // average would be lost for as long as that name stands.
               this._averages[team] = taken;
            }
            for each(var gone:TextField in fields)
            {
               gone.visible = false;
            }
            return;
         }
         if(team.text != taken[0])
         {
            team.text = taken[0];
         }
         this._averages[team] = taken;
         if(fields == null)
         {
            var sign:TextField = newField();
            sign.defaultTextFormat = team.getTextFormat();
            sign.text = "\u00d8";
            fields = [newField(), sign];
            this._averageFields[team] = fields;
         }
         var parent:DisplayObjectContainer = team.parent;
         for each(var tf:TextField in fields)
         {
            if(tf.parent != parent)
            {
               parent.addChild(tf);
            }
            tf.visible = team.visible;
         }
         var bounds:Rectangle = team.getBounds(parent);
         var y:Number = Math.round(bounds.y + (bounds.height - HEIGHT) / 2) + IMAGE_RISE;
         var local:Number = parent.globalToLocal(new Point(column[0], 0)).x;
         var badgeWidth:Number = VehicleMarkers.markupWidth(taken[1]);
         var signWidth:Number = fields[1].textWidth;
         var badgeX:Number = rightwards ? local + GAP : local - GAP - badgeWidth;
         var signX:Number = rightwards ? local + GAP + column[1] + SPACE : local - GAP - column[1] - SPACE - signWidth;
         this.setField(fields[0], taken[1], badgeWidth, badgeX, y);
         fields[1].width = signWidth + GUTTER * 2 + 2;
         fields[1].x = Math.round(signX - GUTTER);
         fields[1].y = Math.round(bounds.y + (bounds.height - fields[1].height) / 2);
      }

      // Every badge in a piece of markup, plus the gaps between them.
      private static function markupWidth(markup:String) : Number
      {
         var total:Number = 0;
         var count:int = 0;
         var found:Object = null;
         WIDTHS.lastIndex = 0;
         while((found = WIDTHS.exec(markup)) != null)
         {
            total += Number(found[1]);
            count++;
         }
         return total + (count > 1 ? (count - 1) * BADGE_GAP : 0);
      }

      private function drawIcons(icons:Object, ids:Array, ally:Boolean, hidden:Boolean) : void
      {
         var count:int = icons != null ? int(icons.length) : 0;
         for(var i:int = 0; i < count; i++)
         {
            var icon:DisplayObject = icons[i] as DisplayObject;
            var marker:Array = ids[i] != null ? this._markers[String(ids[i])] as Array : null;
            this.colorLoadingRow(icon, marker, ally, i, hidden);
         }
         if(icons != null && this.settled(icons, this.readingOf(icons, count) + (ally ? 0.5 : 0)))
         {
            return;
         }
         var team:Array = [];
         for(i = 0; i < count; i++)
         {
            team.push(icons[i]);
         }
         this.placeTeam(team, hidden ? [] : ids, null, ally, NaN, !this._redesign);
      }

      private function colorLoadingRow(icon:DisplayObject, marker:Array, ally:Boolean, index:int, hidden:Boolean) : void
      {
         if(icon == null)
         {
            return;
         }
         var suffix:String = String(index);
         var named:String = icon.name != null ? icon.name : "";
         var side:String = ally ? "Ally" : "Enemy";
         var prefix:String = "vehicleIcon" + side;
         if(named.indexOf(prefix) == 0)
         {
            suffix = named.substr(prefix.length);
         }
         var player:TextField = this.namedText(icon, "textField" + side + suffix);
         var vehicle:TextField = this.namedText(icon, "vehicleField" + side + suffix);
         var row:Object = {playerNameFullTF:player, vehicleTF:vehicle};
         this._rosterRows.loading(icon, player, vehicle, side, suffix, marker,
                                  this._redesign, !hidden && this._rosterStats);
         this._rosterColors.apply(row, this._redesign ? "#f2f3f5" : (marker != null ? String(marker[4]) : null),
                                 this._colorNames, this._colorClanTags,
                                 this._colorVehicles, marker != null ? marker[5] : null,
                                 marker != null ? marker[6] : null,
                                 marker != null ? marker[7] : null,
                                 marker != null && marker.currentPlayer);
      }

      private function colorTableRows(icons:Object, count:int) : void
      {
         var middle:Number = 0;
         var placed:int = 0;
         for(var j:int = 0; j < count; j++)
         {
            var measured:DisplayObject = icons[j] as DisplayObject;
            if(measured != null && measured.parent != null)
            {
               middle += centre(measured);
               placed++;
            }
         }
         if(placed == 0)
         {
            return;
         }
         middle /= placed;
         var leftIndex:int = 0;
         var rightIndex:int = 0;
         for(var i:int = 0; i < count; i++)
         {
            var icon:DisplayObject = icons[i] as DisplayObject;
            if(icon == null)
            {
               continue;
            }
            var suffix:String = String(i);
            var named:String = icon.name != null ? icon.name : "";
            var start:int = named.indexOf("vehicleIcon_");
            if(start >= 0)
            {
               suffix = named.substr(start + 12);
            }
            var isLeft:Boolean = centre(icon) < middle;
            var rowId:* = isLeft ? (leftIndex < this._left.length ? this._left[leftIndex++] : null)
                                 : (rightIndex < this._right.length ? this._right[rightIndex++] : null);
            var marker:Array = rowId != null ? this._markers[String(rowId)] as Array : null;
            var player:TextField = this.namedText(icon, "playerName_" + suffix);
            var vehicle:TextField = this.namedText(icon, "vehicleName_" + suffix);
            this._rosterColors.apply({playerNameFullTF:player, vehicleTF:vehicle},
                                     marker != null ? String(marker[4]) : null,
                                     this._colorNames, this._colorClanTags,
                                     this._colorVehicles, marker != null ? marker[5] : null,
                                     marker != null ? marker[6] : null,
                                     marker != null ? marker[7] : null,
                                     marker != null && marker.currentPlayer);
         }
      }

      private function namedText(from:DisplayObject, name:String) : TextField
      {
         var current:DisplayObject = from;
         for(var i:int = 0; i < 6 && current != null; i++)
         {
            var owner:DisplayObjectContainer = current.parent;
            if(owner == null)
            {
               return null;
            }
            var found:DisplayObject = owner.getChildByName(name);
            if(found is TextField)
            {
               return found as TextField;
            }
            current = owner;
         }
         return null;
      }

      // One team's icons, the ids of their rows in the same order, and
      // whether each row shows (null: all of them). Markers go right of the
      // icons when ally, else left; beside them, or with the middle of the
      // screen given, outside the team's rows. Returns [edge, badges width]
      // of the columns drawn, or null when none is.
      private function placeTeam(icons:Array, ids:Array, shown:Array, ally:Boolean, middle:Number,
                                panelBadgesVisible:Boolean = true) : Array
      {
         // Placing a team is expensive: an edge measures every neighbour of
         // every row, and a screen has thirty of them. Where the icons sit is
         // cheap to read, so a placement stands while that reading holds, and
         // is done again every RESTING_MS anyway, since a neighbour's text can
         // grow without anything having moved.
         var key:Object = icons.length > 0 ? icons[0] : null;
         var reading:Number = this.readingOf(icons, icons.length) + (ally ? 0.5 : 0) +
                              (isNaN(middle) ? 0 : Math.round(middle)) + (panelBadgesVisible ? 0.75 : 0);
         if(this.settled(key, reading))
         {
            return this._placed[key].result as Array;
         }
         var edge:Number = NaN;
         var badges:Number = 0;
         var drawn:Array = [];
         for(var i:int = 0; i < icons.length; i++)
         {
            var icon:DisplayObject = icons[i] as DisplayObject;
            if(icon == null || icon.parent == null)
            {
               continue;
            }
            var id:* = ids[i];
            var marker:Array = id != null ? this._markers[String(id)] as Array : null;
            var visible:Boolean = marker != null && icon.visible && (shown == null || shown[i]);
            var fields:Array = this.fieldsFor(icon, marker != null);
            if(fields == null)
            {
               continue;
            }
            for each(var tf:TextField in fields)
            {
               tf.visible = visible;
            }
            if(!visible)
            {
               continue;
            }
            // The outer edge in stage space, where rows of one team compare.
            var parent:DisplayObjectContainer = icon.parent;
            var bounds:Rectangle = icon.getBounds(parent);
            var global:Number = parent.localToGlobal(new Point(this.edge(parent, icon, bounds, ally, middle), 0)).x;
            edge = isNaN(edge) ? global : (ally ? Math.max(edge, global) : Math.min(edge, global));
            badges = Math.max(badges, Number(marker[1]));
            drawn.push([icon, marker, fields, bounds]);
         }
         for each(var item:Array in drawn)
         {
            this.placeRow(item[0], item[1], item[2], item[3], edge, badges, ally,
                          panelBadgesVisible);
         }
         var result:Array = drawn.length > 0 ? [edge, badges] : null;
         if(key != null)
         {
            this._placed[key].result = result;
         }
         return result;
      }

      // How long a placement stands when nothing has moved, in milliseconds.
      private static const RESTING_MS:int = 250;

      // Where a row of things sits, as one number, from properties that cost
      // nothing to read: no bounds are measured, no text is laid out.
      private function readingOf(nodes:Object, count:int) : Number
      {
         var reading:Number = this._revision * 1000003 + count * 1009;
         for(var i:int = 0; i < count; i++)
         {
            var node:DisplayObject = nodes[i] as DisplayObject;
            if(node == null)
            {
               reading += (i + 1) * 3;
               continue;
            }
            var owner:DisplayObjectContainer = node.parent;
            reading += (i + 1) * (node.x + node.y * 7 + (node.visible ? 3 : 0));
            if(owner == null)
            {
               continue;
            }
            reading += owner.y * 13 + owner.numChildren * 17 + (owner.visible ? 5 : 0);
            // The neighbours too, and whether each shows: the columns start
            // past the farthest one, so one appearing without anything moving
            // -- a spotted indicator, a ping -- must place the row again.
            // Only where they are and whether they show is read, which costs
            // nothing; their bounds are what the placing itself measures.
            for(var j:int = 0; j < owner.numChildren; j++)
            {
               var neighbour:DisplayObject = owner.getChildAt(j);
               if(neighbour.name == NAME)
               {
                  continue;
               }
               reading += (j + 1) * (neighbour.x + (neighbour.visible ? 2 : 0));
            }
         }
         return reading;
      }

      // Whether this screen can be left as it is: nothing has moved since it
      // was placed, and it was placed recently enough.
      private function settled(key:Object, reading:Number) : Boolean
      {
         if(key == null)
         {
            return false;
         }
         var kept:Object = this._placed[key];
         var now:int = getTimer();
         if(kept != null && kept.reading == reading && now - kept.when < RESTING_MS)
         {
            return true;
         }
         this._placed[key] = {"reading":reading, "when":now, "result":kept != null ? kept.result : null};
         return false;
      }

      // icons[0] -> the reading it was placed on, when, and what it gave.
      private var _placed:Dictionary = new Dictionary(true);

      // Changes whenever what is drawn changes, not only where: new markup,
      // another order, or a screen hidden or shown.
      private var _revision:int = 0;

      private var _hiding:String = "";

      private function fieldsFor(icon:DisplayObject, create:Boolean) : Array
      {
         var fields:Array = this._fields[icon] as Array;
         if(fields == null)
         {
            if(!create)
            {
               return null;
            }
            fields = [newField(), newField()];
            this._fields[icon] = fields;
         }
         for each(var tf:TextField in fields)
         {
            if(tf.parent != icon.parent)
            {
               icon.parent.addChild(tf);
            }
         }
         return fields;
      }

      private static function newField() : TextField
      {
         var tf:TextField = new TextField();
         tf.selectable = false;
         tf.mouseEnabled = false;
         tf.multiline = false;
         tf.wordWrap = false;
         tf.height = HEIGHT;
         tf.name = NAME;
         return tf;
      }

      private function placeRow(icon:DisplayObject, marker:Array, fields:Array, bounds:Rectangle,
                                edge:Number, badges:Number, ally:Boolean,
                                badgeVisible:Boolean = true) : void
      {
         var parent:DisplayObjectContainer = icon.parent;
         var local:Number = parent.globalToLocal(new Point(edge, 0)).x;
         var y:Number = Math.round(bounds.y + (bounds.height - HEIGHT) / 2) + IMAGE_RISE;
         var badgeWidth:Number = marker[1];
         var flagsWidth:Number = marker[3];
         // Allies read outwards from the icon, badge then flags; enemies are
         // mirrored, each column hugging the side nearest the icon.
         var badgeX:Number = ally ? local + GAP : local - GAP - badgeWidth;
         var flagsX:Number = ally ? local + GAP + badges + SPACE : local - GAP - badges - SPACE - flagsWidth;
         this.setField(fields[0], marker[0], badgeWidth, badgeX, y);
         this.setField(fields[1], marker[2], flagsWidth, flagsX, y + imageDrop(fields[0], fields[1]));
         if(!badgeVisible)
         {
            // Keep the marker's measured column width so flags do not jump
            // when Alt is pressed, but do not leave a visible blank pill.
            fields[0].visible = false;
         }
      }

      /**
       * How much lower the flags field has to sit for its images to share the
       * badges' line, measured rather than assumed.
       *
       * The two are read as one row but they are two TextFields: they swap
       * sides between allies and enemies, so they cannot share one. Given the
       * same y they do not agree, and nothing in the markup says why -- both
       * hold 12px images written with the same vspace, both fields are the
       * same height. What is left is where Flash puts an image inside a field,
       * which depends on what else the field holds, and the badges field holds
       * a different number of images and sometimes a text fallback.
       *
       * So the offset is read off the result: the first image's own rectangle
       * in each field, and the difference between their tops. An image loads a
       * frame or two after its tag is set (see ContactColumns) and until then
       * there is no rectangle to read, which is why this returns 0 rather than
       * guessing -- `placeTeam` comes back every RESTING_MS and the answer
       * lands once the images have.
       */
      private static function imageDrop(badge:TextField, flags:TextField) : Number
      {
         if(!badge.visible || !flags.visible || badge.length == 0 || flags.length == 0)
         {
            return 0;
         }
         var first:Rectangle = badge.getCharBoundaries(0);
         var second:Rectangle = flags.getCharBoundaries(0);
         if(first == null || second == null)
         {
            return 0;
         }
         return Math.round(first.y - second.y);
      }

      private function setField(tf:TextField, html:String, width:Number, x:Number, y:Number) : void
      {
         if(!html)
         {
            tf.visible = false;
            return;
         }
         if(this._html[tf] != html)
         {
            tf.htmlText = html;
            // htmlText reads back rewritten, so what was set is kept aside.
            this._html[tf] = html;
         }
         tf.width = width + GUTTER * 2 + 2;
         tf.x = Math.round(x - GUTTER);
         tf.y = y;
      }

      // Where a field's text is drawn, in its parent's space, or null when empty.
      private static function textBounds(text:TextField, box:Rectangle) : Rectangle
      {
         if(text.text == null || text.text.length == 0)
         {
            return null;
         }
         var width:Number = Math.min(text.textWidth + 4, box.width);
         var align:String = text.getTextFormat().align;
         var left:Number = box.left;
         if(align == TextFormatAlign.RIGHT)
         {
            left = box.right - width;
         }
         else if(align == TextFormatAlign.CENTER)
         {
            left = box.left + (box.width - width) / 2;
         }
         return new Rectangle(left, box.top, width, box.height);
      }

      // The outer edge of the icon and of every visible neighbour beyond it,
      // on the markers' side and across the icon's middle. With the middle of
      // the screen given, every neighbour on the icon's half counts: the edge
      // of the whole row.
      private function edge(parent:DisplayObjectContainer, icon:DisplayObject, bounds:Rectangle, ally:Boolean, screenMiddle:Number) : Number
      {
         var edge:Number = ally ? bounds.right : bounds.left;
         var middle:Number = bounds.y + bounds.height / 2;
         var half:Number = isNaN(screenMiddle) ? NaN : parent.globalToLocal(new Point(screenMiddle, 0)).x;
         for(var i:int = 0; i < parent.numChildren; i++)
         {
            var child:DisplayObject = parent.getChildAt(i);
            if(child == icon || !child.visible || child.alpha == 0 || child.name == NAME || BACKGROUND.test(child.name))
            {
               continue;
            }
            var other:Rectangle = child.getBounds(parent);
            if(other.width <= 0 || other.width > MAX_NEIGHBOUR_WIDTH || other.top > middle || other.bottom < middle)
            {
               continue;
            }
            var text:TextField = child as TextField;
            if(text != null)
            {
               // A text field is often wider than its text and set over the
               // icon, so only the text itself counts, wherever it starts.
               other = textBounds(text, other);
               if(other == null)
               {
                  continue;
               }
            }
            if(!isNaN(half))
            {
               var side:Number = other.x + other.width / 2;
               if(ally && side > half && other.right > edge)
               {
                  edge = other.right;
               }
               else if(!ally && side < half && other.left < edge)
               {
                  edge = other.left;
               }
            }
            else if(text != null)
            {
               if(ally && other.right > edge)
               {
                  edge = other.right;
               }
               else if(!ally && other.left < edge)
               {
                  edge = other.left;
               }
            }
            else if(ally && other.left >= bounds.right - 2 && other.right > edge)
            {
               edge = other.right;
            }
            else if(!ally && other.right <= bounds.left + 2 && other.left < edge)
            {
               edge = other.left;
            }
         }
         return edge;
      }
   }
}
