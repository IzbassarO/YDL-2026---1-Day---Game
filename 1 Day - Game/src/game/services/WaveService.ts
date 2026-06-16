import { TileMap } from "@/game/models/TileMap";
import { MobModel } from "@/game/models/MobModel";
import { CFG, Difficulty } from "@/game/core/constants";
import { rand, randi } from "@/game/core/Vec";

/** Spawns escalating waves away from the player's start room. */
export class WaveService {
  wave = 0;
  timer = 0;

  constructor(
    private map: TileMap,
    private difficulty: Difficulty,
  ) {}

  reset(): void {
    this.wave = 0;
    this.timer = 0;
  }

  /** @returns spawned mobs for this tick (empty unless a wave triggers). */
  tick(dt: number, aliveCount: number): MobModel[] {
    this.timer -= dt;
    if (this.timer > 0) return [];
    return this.spawn(aliveCount);
  }

  private spawn(aliveCount: number): MobModel[] {
    this.wave++;
    this.timer = CFG.waves.intervalSec;

    const diff = CFG.difficulty[this.difficulty];
    const want = Math.round(
      (CFG.waves.baseCount + (this.wave - 1) * CFG.waves.perWave) * diff.countMul,
    );
    const room = Math.min(CFG.waves.maxAlive - aliveCount, want);
    if (room <= 0) return [];

    const rooms = this.map.rooms;
    const T = this.map.T;
    const out: MobModel[] = [];
    for (let i = 0; i < room; i++) {
      // never spawn in the player's start room (index 0)
      const rIdx = rooms.length > 1 ? randi(1, rooms.length - 1) : 0;
      const rm = rooms[rIdx];
      const x = (rm.c + rand(0.6, rm.w - 0.6)) * T;
      const y = (rm.r + rand(0.6, rm.h - 0.6)) * T;
      out.push(new MobModel(x, y, this.wave - 1, diff.speedMul));
    }
    return out;
  }
}
