import { CFG } from "@/game/core/constants";
import { damp, rand } from "@/game/core/Vec";

/** Smooth follow camera with decaying screen shake. */
export class CameraService {
  x = 0;
  y = 0;
  shake = 0;
  offX = 0;
  offY = 0;

  snapTo(tx: number, ty: number, vw: number, vh: number): void {
    this.x = tx - vw / 2;
    this.y = ty - vh / 2;
  }

  follow(tx: number, ty: number, vw: number, vh: number, dt: number): void {
    const targetX = tx - vw / 2;
    const targetY = ty - vh / 2;
    const t = damp(CFG.camera.follow, dt);
    this.x += (targetX - this.x) * t;
    this.y += (targetY - this.y) * t;

    if (this.shake > 0.05) {
      this.shake = Math.max(0, this.shake - CFG.camera.shakeDecay * dt);
      this.offX = rand(-this.shake, this.shake);
      this.offY = rand(-this.shake, this.shake);
    } else {
      this.shake = 0;
      this.offX = 0;
      this.offY = 0;
    }
  }

  addShake(amount: number): void {
    this.shake = Math.min(CFG.camera.shakeMax, this.shake + amount);
  }
}
