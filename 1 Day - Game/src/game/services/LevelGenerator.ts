import { TileMap, Room } from "@/game/models/TileMap";
import { randi } from "@/game/core/Vec";

/**
 * Procedural dungeon: non-overlapping rooms joined by L-shaped corridors.
 * Guarantees connectivity by chaining each room to the previous one.
 */
export class LevelGenerator {
  static generate(): TileMap {
    const cols = randi(36, 44);
    const rows = randi(28, 34);
    const map = new TileMap(cols, rows);

    const target = randi(7, 10);
    const rooms: Room[] = [];
    let tries = 0;

    while (rooms.length < target && tries < 240) {
      tries++;
      const w = randi(5, 9);
      const h = randi(4, 7);
      const c = randi(1, cols - w - 2);
      const r = randi(1, rows - h - 2);
      const room: Room = { c, r, w, h, cx: c + (w >> 1), cy: r + (h >> 1) };

      const overlaps = rooms.some(
        (o) =>
          room.c < o.c + o.w + 1 &&
          room.c + room.w + 1 > o.c &&
          room.r < o.r + o.h + 1 &&
          room.r + room.h + 1 > o.r,
      );
      if (overlaps) continue;

      rooms.push(room);
      for (let y = r; y < r + h; y++)
        for (let x = c; x < c + w; x++) map.set(x, y, 0);
    }

    for (let i = 1; i < rooms.length; i++) {
      const a = rooms[i - 1];
      const b = rooms[i];
      LevelGenerator.carveH(map, a.cx, b.cx, a.cy);
      LevelGenerator.carveV(map, a.cy, b.cy, b.cx);
    }

    map.rooms = rooms;
    return map;
  }

  private static carveH(m: TileMap, x1: number, x2: number, y: number): void {
    for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
      m.set(x, y, 0);
      m.set(x, y + 1, 0);
    }
  }
  private static carveV(m: TileMap, y1: number, y2: number, x: number): void {
    for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
      m.set(x, y, 0);
      m.set(x + 1, y, 0);
    }
  }
}
