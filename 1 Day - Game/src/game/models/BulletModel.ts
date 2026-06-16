import { CFG } from "@/game/core/constants";

export interface BulletOpts {
  damage: number;
  radius: number;
  pierce: boolean;
  homing: boolean;
}

export class BulletModel {
  x: number;
  y: number;
  vx: number;
  vy: number;
  speed = CFG.weapon.bulletSpeed;
  radius: number;
  damage: number;
  pierce: boolean;
  homing: boolean;
  life: number;
  dead = false;
  // ids of mobs already hit (so a piercing bolt won't re-hit the same mob)
  hitIds = new Set<number>();
  // recent positions for the glowing tracer trail
  trail: number[] = [];

  constructor(x: number, y: number, dirX: number, dirY: number, opts: BulletOpts) {
    this.x = x;
    this.y = y;
    this.vx = dirX * this.speed;
    this.vy = dirY * this.speed;
    this.radius = opts.radius;
    this.damage = opts.damage;
    this.pierce = opts.pierce;
    this.homing = opts.homing;
    this.life = CFG.weapon.range / this.speed + 0.05;
  }
}
