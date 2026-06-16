import { rand } from "@/game/core/Vec";
import { PALETTE } from "@/game/core/constants";

export class ParticleModel {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  max: number;
  color: string;
  size: number;
  drag: number;
  dead = false;

  constructor(
    x: number,
    y: number,
    vx: number,
    vy: number,
    life: number,
    color: string,
    size: number,
    drag = 0.9,
  ) {
    this.x = x;
    this.y = y;
    this.vx = vx;
    this.vy = vy;
    this.life = life;
    this.max = life;
    this.color = color;
    this.size = size;
    this.drag = drag;
  }

  static muzzle(x: number, y: number): ParticleModel {
    const a = rand(0, Math.PI * 2);
    const s = rand(40, 150);
    return new ParticleModel(
      x,
      y,
      Math.cos(a) * s,
      Math.sin(a) * s,
      rand(0.12, 0.3),
      PALETTE.cyan,
      rand(2, 3.5),
    );
  }

  static death(x: number, y: number): ParticleModel {
    const a = rand(0, Math.PI * 2);
    const s = rand(60, 240);
    return new ParticleModel(
      x,
      y,
      Math.cos(a) * s,
      Math.sin(a) * s,
      rand(0.3, 0.7),
      Math.random() < 0.5 ? PALETTE.red : PALETTE.purple,
      rand(2, 5),
      0.88,
    );
  }

  static impact(x: number, y: number): ParticleModel {
    const a = rand(0, Math.PI * 2);
    const s = rand(30, 120);
    return new ParticleModel(
      x,
      y,
      Math.cos(a) * s,
      Math.sin(a) * s,
      rand(0.1, 0.25),
      PALETTE.amber,
      rand(1.5, 3),
    );
  }
}
