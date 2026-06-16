import { CFG } from "@/game/core/constants";
import { rand } from "@/game/core/Vec";

/** Currency pickup dropped by dying mobs. Pops outward, then settles. */
export class CoinModel {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life = CFG.coin.life;
  radius = CFG.coin.radius;
  spin = rand(0, Math.PI * 2);
  collected = false;

  constructor(x: number, y: number) {
    this.x = x;
    this.y = y;
    const a = rand(0, Math.PI * 2);
    const s = rand(20, 90);
    this.vx = Math.cos(a) * s;
    this.vy = Math.sin(a) * s;
  }
}
