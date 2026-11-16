// Execute the actual pure AS3 geometry bodies in JS, without a second formula.
import fs from 'node:fs';
import assert from 'node:assert/strict';
const source = fs.readFileSync(new URL('../as3/src/unicum/RosterGrid.as', import.meta.url), 'utf8');
function method(name) {
  const match = source.match(new RegExp(`public static function ${name}\\(([\\s\\S]*?)\\) : \\w+\\s*\\{([\\s\\S]*?)\\n      \\}`));
  assert.ok(match, `missing pure AS3 method ${name}`);
  const parameters = match[1].replace(/:\w+/g, '');
  const body = match[2].replace(/(var\s+\w+):\w+/g, '$1');
  return new Function(parameters, body);
}
const loading = method('loading');
const stripe = method('stripe');
let cases = 0;
for (const width of [440, 480, 520, 600]) {
  for (const shown of [false, true]) {
    const mirror = 1600;
    const a = loading(0, width, width - 200, width - 100, true, shown);
    const b = loading(mirror - width, mirror, mirror - width + 100, mirror - width + 200, false, shown);
    assert.equal(a.nameWidth, b.nameWidth);
    assert.equal(a.nameX + a.nameWidth + b.nameX, mirror);
    assert.equal(a.badgeX + b.badgeX, mirror);
    assert.equal(a.squadX + b.squadX, mirror);
    assert.ok(a.squadX - 10 >= 0 && a.badgeX + 18 <= a.nameX);
    assert.ok(b.badgeX - 18 >= b.nameX + b.nameWidth && b.squadX + 10 <= mirror);
    assert.ok(a.nameWidth > 0);
    if (shown) {
      assert.ok(a.nameX + a.nameWidth <= a.statsX - 6);
      assert.ok(a.statsX + 126 <= width - 200 - 6);
      assert.equal(a.statsX + b.statsX + 126, mirror);
    }
    assert.equal(stripe(0, width, false) + stripe(mirror-width, mirror, true) + 3, mirror);
    assert.equal(stripe(0, width, true) + stripe(mirror-width, mirror, false) + 3, mirror);
    cases++;
  }
}
console.log(`PASS ${cases} loading layouts: mirrored zones, contained medals/squad, no name/stat overlap; inverse panel stripes`);
