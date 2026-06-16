import { TileMap } from "@/game/models/TileMap";
import { clamp, dist2 } from "@/game/core/Vec";

interface Body {
  x: number;
  y: number;
  radius: number;
}

/** Circle-vs-tile collision with axis-separated resolution (no tunnelling). */
export class CollisionService {
  constructor(private map: TileMap) {}

  move(body: Body, dx: number, dy: number): void {
    const tryX = body.x + dx;
    if (!this.circleHitsWall(tryX, body.y, body.radius)) body.x = tryX;

    const tryY = body.y + dy;
    if (!this.circleHitsWall(body.x, tryY, body.radius)) body.y = tryY;

    const m = this.map;
    body.x = clamp(body.x, body.radius, m.pxW() - body.radius);
    body.y = clamp(body.y, body.radius, m.pxH() - body.radius);
  }

  circleHitsWall(px: number, py: number, rad: number): boolean {
    const T = this.map.T;
    const c0 = Math.floor((px - rad) / T);
    const c1 = Math.floor((px + rad) / T);
    const r0 = Math.floor((py - rad) / T);
    const r1 = Math.floor((py + rad) / T);
    for (let r = r0; r <= r1; r++) {
      for (let c = c0; c <= c1; c++) {
        if (this.map.at(c, r) === 1) {
          const nx = clamp(px, c * T, c * T + T);
          const ny = clamp(py, r * T, r * T + T);
          if (dist2(px, py, nx, ny) < rad * rad) return true;
        }
      }
    }
    return false;
  }

  /**
   * Line-of-sight between two world points. Samples the segment in half-tile
   * steps and reports blocked if any sample lands in a wall.
   * Used by auto-aim so the weapon never fires "through" walls.
   */
  hasLineOfSight(ax: number, ay: number, bx: number, by: number): boolean {
    const T = this.map.T;
    const dx = bx - ax;
    const dy = by - ay;
    const distance = Math.hypot(dx, dy);
    const steps = Math.max(1, Math.ceil(distance / (T * 0.5)));
    const sx = dx / steps;
    const sy = dy / steps;
    let x = ax;
    let y = ay;
    for (let i = 0; i < steps; i++) {
      x += sx;
      y += sy;
      if (this.map.isWallPx(x, y)) return false;
    }
    return true;
  }
}
