import { TileMap } from "@/game/models/TileMap";

/**
 * Flow-field pathfinding.
 *
 * A single BFS from the player's tile produces a distance field over every
 * reachable floor tile. Each mob then simply walks "downhill" toward the lower
 * distance value — so the whole horde pursues the player AROUND walls and
 * corridors, at any range, with O(mobs) per-frame cost instead of an A* search
 * per mob.
 *
 * The field is only recomputed when the player changes tile (or on demand),
 * which keeps it cheap.
 */
export class PathfindingService {
  private dist: Int32Array;
  private goalC = -1;
  private goalR = -1;
  private queue: Int32Array; // ring buffer of tile indices
  private readonly UNREACHABLE = 0x7fffffff;

  constructor(private map: TileMap) {
    this.dist = new Int32Array(map.cols * map.rows).fill(this.UNREACHABLE);
    this.queue = new Int32Array(map.cols * map.rows);
  }

  /** Recompute the field only if the goal tile changed. */
  update(goalCol: number, goalRow: number): void {
    if (goalCol === this.goalC && goalRow === this.goalR) return;
    if (!this.map.isFloor(goalCol, goalRow)) return; // goal inside wall — keep last field
    this.goalC = goalCol;
    this.goalR = goalRow;
    this.computeField(goalCol, goalRow);
  }

  forceRecompute(): void {
    this.goalC = -1;
    this.goalR = -1;
  }

  private computeField(gc: number, gr: number): void {
    const cols = this.map.cols;
    const dist = this.dist;
    dist.fill(this.UNREACHABLE);

    const q = this.queue;
    let head = 0;
    let tail = 0;
    const start = gr * cols + gc;
    dist[start] = 0;
    q[tail++] = start;

    // 4-neighbour BFS (uniform cost) — corridors stay clean.
    while (head < tail) {
      const cur = q[head++];
      const cc = cur % cols;
      const cr = (cur / cols) | 0;
      const nd = dist[cur] + 1;

      tail = this.tryNeighbor(cc, cr - 1, nd, q, tail); // up
      tail = this.tryNeighbor(cc, cr + 1, nd, q, tail); // down
      tail = this.tryNeighbor(cc - 1, cr, nd, q, tail); // left
      tail = this.tryNeighbor(cc + 1, cr, nd, q, tail); // right
    }
  }

  private tryNeighbor(
    c: number,
    r: number,
    nd: number,
    q: Int32Array,
    tail: number,
  ): number {
    if (c < 0 || r < 0 || c >= this.map.cols || r >= this.map.rows) return tail;
    if (!this.map.isFloor(c, r)) return tail;
    const i = r * this.map.cols + c;
    if (nd < this.dist[i]) {
      this.dist[i] = nd;
      q[tail++] = i;
    }
    return tail;
  }

  private distAt(c: number, r: number): number {
    if (c < 0 || r < 0 || c >= this.map.cols || r >= this.map.rows)
      return this.UNREACHABLE;
    return this.dist[r * this.map.cols + c];
  }

  /** Path distance (in tiles) from a world point to the goal; Infinity if walled off. */
  pathCost(px: number, py: number): number {
    const d = this.distAt(this.map.colOf(px), this.map.rowOf(py));
    return d === this.UNREACHABLE ? Infinity : d;
  }

  /**
   * Desired unit direction for a mob at (px,py): walk toward the neighbouring
   * tile with the lowest distance value. Falls back to straight-line seek when
   * the mob sits on an unreachable tile (e.g. spawned in an odd spot).
   */
  steer(px: number, py: number, goalX: number, goalY: number): { x: number; y: number } {
    const cc = this.map.colOf(px);
    const cr = this.map.rowOf(py);
    const here = this.distAt(cc, cr);

    if (here === this.UNREACHABLE) return this.directTo(px, py, goalX, goalY);
    if (here === 0) return this.directTo(px, py, goalX, goalY); // same tile as player

    // pick best of 8 neighbours, allowing diagonals only when both orthogonals are open
    let best = here;
    let bx = 0;
    let by = 0;
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dc === 0 && dr === 0) continue;
        if (dc !== 0 && dr !== 0) {
          // prevent corner-cutting through walls
          if (!this.map.isFloor(cc + dc, cr) || !this.map.isFloor(cc, cr + dr))
            continue;
        }
        const d = this.distAt(cc + dc, cr + dr);
        if (d < best) {
          best = d;
          bx = dc;
          by = dr;
        }
      }
    }

    if (bx === 0 && by === 0) return this.directTo(px, py, goalX, goalY);

    // Aim at the center of the chosen neighbour tile for smooth motion.
    const T = this.map.T;
    const targetX = (cc + bx + 0.5) * T;
    const targetY = (cr + by + 0.5) * T;
    return this.directTo(px, py, targetX, targetY);
  }

  private directTo(px: number, py: number, tx: number, ty: number) {
    const dx = tx - px;
    const dy = ty - py;
    const l = Math.hypot(dx, dy) || 1;
    return { x: dx / l, y: dy / l };
  }
}
