import { MobModel } from "@/game/models/MobModel";
import { PlayerModel } from "@/game/models/PlayerModel";
import { CollisionService } from "@/game/services/CollisionService";
import { CFG } from "@/game/core/constants";
import { dist2 } from "@/game/core/Vec";

/**
 * Target selection for the auto-aim weapon.
 *
 * Fixes the "shoots through walls" bug: a mob that is closer by straight-line
 * distance but separated by a wall has NO line of sight, so it is ignored in
 * favour of the nearest mob the weapon can actually hit — i.e. the ones
 * approaching the player in the open / down the corridor.
 */
export class AutoAimService {
  constructor(private collision: CollisionService) {}

  pickTarget(player: PlayerModel, mobs: MobModel[]): MobModel | null {
    const range2 = CFG.weapon.range * CFG.weapon.range;
    let best: MobModel | null = null;
    let bestD = Infinity;

    for (const m of mobs) {
      if (!m.active) continue;
      const d = dist2(player.x, player.y, m.x, m.y);
      if (d > range2) continue;
      if (d >= bestD) continue;
      // Only consider mobs we can see — no firing through walls.
      if (!this.collision.hasLineOfSight(player.x, player.y, m.x, m.y)) continue;
      best = m;
      bestD = d;
    }
    return best;
  }
}
