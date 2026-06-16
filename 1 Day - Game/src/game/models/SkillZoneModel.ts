import { CFG } from "@/game/core/constants";
import { rand } from "@/game/core/Vec";

/**
 * A skill pad ("shop / chess square"). The player charges it by standing on it;
 * once full it opens a 3-skill choice and then recharges for the next pick.
 */
export class SkillZoneModel {
  x: number;
  y: number;
  radius = CFG.zone.radius;
  charge = 0;
  needed: number;
  picks = 0; // how many skills already granted here

  constructor(x: number, y: number) {
    this.x = x;
    this.y = y;
    this.needed = rand(CFG.zone.chargeMin, CFG.zone.chargeMax);
  }

  get progress(): number {
    return Math.min(1, this.charge / this.needed);
  }
}
