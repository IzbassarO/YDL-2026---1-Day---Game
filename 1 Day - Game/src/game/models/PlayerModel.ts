import { CFG } from "@/game/core/constants";

export class PlayerModel {
  x: number;
  y: number;
  vx = 0;
  vy = 0;
  radius = CFG.player.radius;
  hp: number = CFG.player.hp;
  maxHp: number = CFG.player.hp;
  speed: number = CFG.player.speed;
  fireCooldown = 0; // ms
  flash = 0; // damage flash timer (sec)
  attackTimer = 0; // >0 => play attack clip (sec)
  facing = 1; // -1 left, 1 right
  animTime = 0;
  moving = false;

  // ---- weapon modifiers (mutated by skill pickups) ----
  fireRateMul = 1; // multiplies fire interval (lower = faster)
  damageMul = 1;
  bulletSizeMul = 1;
  parallel = 1; // number of side-by-side bolts
  spread = false; // extra diagonal bolts
  homing = false;
  pierce = false;

  constructor(x: number, y: number) {
    this.x = x;
    this.y = y;
  }

  hurt(amount: number): void {
    this.hp = Math.max(0, this.hp - amount);
    this.flash = 0.25;
  }

  get alive(): boolean {
    return this.hp > 0;
  }
}
