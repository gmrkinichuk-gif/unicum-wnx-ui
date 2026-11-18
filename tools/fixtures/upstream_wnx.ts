// AGPL-3.0, Antoine Kingue. Unicum.gg 65f19c009bf434bb2c0c9061183b12c743f856fd ratings.ts
export type WNXExpected = {
  damage: number;
  frags: number;
  spots: number;
  assist: number;
};

/** Battle-weighted WNX accumulator. Same split rationale as {@link WN8Acc}: add
 * each tank once, remove any subset in O(1). */
export type WNXAcc = {
  wExpDmg: number;
  wExpSpot: number;
  wExpFrag: number;
  wExpAssist: number;
  wDmg: number;
  wSpot: number;
  wFrag: number;
  wAssist: number;
};

export function wnxAccZero(): WNXAcc {
  return {
    wExpDmg: 0, wExpSpot: 0, wExpFrag: 0, wExpAssist: 0,
    wDmg: 0, wSpot: 0, wFrag: 0, wAssist: 0,
  };
}

/** Add one tank into `acc`; a no-op for a tank with no battles or no expected
 * values, matching `computeWNX`'s `continue` (so removal stays exact). */
export function wnxAccAdd(
  acc: WNXAcc,
  t: TankStats,
  expected: Map<number, WNXExpected>,
): void {
  const exp = expected.get(t.tank_id);
  const b = t.all?.battles ?? 0;
  if (!exp || b <= 0) return;

  acc.wExpDmg += b * exp.damage;
  acc.wExpSpot += b * exp.spots;
  acc.wExpFrag += b * exp.frags;
  acc.wExpAssist += b * exp.assist;

  acc.wDmg += t.all.damage_dealt;
  acc.wSpot += t.all.spotted;
  acc.wFrag += t.all.frags;
  acc.wAssist +=
    (t.all.radio_assisted_damage ?? 0) +
    (t.all.track_assisted_damage ?? 0);
}

export function wnxFinalize(acc: WNXAcc): number | null {
  const {
    wExpDmg, wExpSpot, wExpFrag, wExpAssist, wDmg, wSpot, wFrag, wAssist,
  } = acc;
  if (wExpDmg <= 0) return null;

  const adjustedAssist = wAssist * 0.67;
  const adjustedExpAssist = wExpAssist * 0.67;
  const combinedDamage = wDmg + adjustedAssist;
  const combinedExpDamage = wExpDmg + adjustedExpAssist;

  const rDmg = combinedDamage / combinedExpDamage;
  const rDmgC = Math.max(
    0,
    Math.min(rDmg - 0.22, (rDmg - 0.22) / (1 - 0.22)),
  );

  const rFrags = wFrag / wExpFrag;
  const rSpots = wSpot / wExpSpot;
  const rFragsC = Math.max(
    0,
    Math.min(rDmgC + 0.4, (rFrags - 0.12) / (1 - 0.12)),
  );
  const rSpotsC = Math.max(
    0,
    Math.min(rDmgC + 0.2, (rSpots - 0.38) / (1 - 0.38)),
  );

  const raw = 750 * rDmgC + 200 * rFragsC + 50 * rSpotsC;
  const result = raw * (raw / 1000) ** 0.45 * 1.65;
  return Number.isFinite(result) ? result : null;
}

export function computeWNX(
  tanks: TankStats[],
  expected: Map<number, WNXExpected>,
): number | null {
  const acc = wnxAccZero();
  for (const t of tanks) wnxAccAdd(acc, t, expected);
  return wnxFinalize(acc);
}
