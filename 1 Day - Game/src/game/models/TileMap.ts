import { CFG } from "@/game/core/constants";

export interface Room {
  c: number;
  r: number;
  w: number;
  h: number;
  cx: number;
  cy: number;
}

/** Grid map. 0 = floor, 1 = wall. Pure data + cheap lookups. */
export class TileMap {
  readonly cols: number;
  readonly rows: number;
  readonly T = CFG.TILE;
  readonly grid: Uint8Array;
  rooms: Room[] = [];

  constructor(cols: number, rows: number) {
    this.cols = cols;
    this.rows = rows;
    this.grid = new Uint8Array(cols * rows).fill(1);
  }

  idx(c: number, r: number): number {
    return r * this.cols + c;
  }

  at(c: number, r: number): number {
    if (c < 0 || r < 0 || c >= this.cols || r >= this.rows) return 1;
    return this.grid[this.idx(c, r)];
  }

  set(c: number, r: number, v: number): void {
    if (c < 0 || r < 0 || c >= this.cols || r >= this.rows) return;
    this.grid[this.idx(c, r)] = v;
  }

  isFloor(c: number, r: number): boolean {
    return this.at(c, r) === 0;
  }

  isWallPx(px: number, py: number): boolean {
    return this.at(Math.floor(px / this.T), Math.floor(py / this.T)) === 1;
  }

  colOf(px: number): number {
    return Math.floor(px / this.T);
  }
  rowOf(py: number): number {
    return Math.floor(py / this.T);
  }

  pxW(): number {
    return this.cols * this.T;
  }
  pxH(): number {
    return this.rows * this.T;
  }
}
