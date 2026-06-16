import { CFG } from "@/game/core/constants";
import { rand } from "@/game/core/Vec";

let NEXT_ID = 1;

export class MobModel {
  readonly id: number;
  x: number;
  y: number;
  vx = 0;
  vy = 0;
  radius = CFG.mob.radius;
  hp: number;
  maxHp: number;
  speed: number;
  dead = false; // ready to cull
  dying = false; // playing death animation
  deathTime = 0; // seconds into death animation
  flash = 0;
  animTime = rand(0, 10); // desync animation between mobs

  constructor(x: number, y: number, scale: number, speedMul: number) {
    this.id = NEXT_ID++;
    this.x = x;
    this.y = y;
    this.maxHp = CFG.mob.hp * (1 + scale * CFG.waves.hpScale);
    this.hp = this.maxHp;
    this.speed =
      rand(CFG.mob.speedMin, CFG.mob.speedMax) *
      (1 + scale * CFG.waves.speedScale) *
      speedMul;
  }

  /** Targetable by weapon / contact only while fully alive. */
  get active(): boolean {
    return !this.dead && !this.dying;
  }

  /** @returns true if this hit started the death sequence. */
  hurt(amount: number): boolean {
    if (!this.active) return false;
    this.hp -= amount;
    this.flash = 0.12;
    if (this.hp <= 0) {
      this.dying = true; // begin death animation; culled when it finishes
      return true;
    }
    return false;
  }
}
