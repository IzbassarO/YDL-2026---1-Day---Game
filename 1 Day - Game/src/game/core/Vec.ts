// Tiny math helpers. Kept as free functions (data-oriented, no Vector objects
// allocated per frame).

export const clamp = (v: number, a: number, b: number): number =>
  v < a ? a : v > b ? b : v;

export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

export const dist2 = (ax: number, ay: number, bx: number, by: number): number => {
  const dx = ax - bx;
  const dy = ay - by;
  return dx * dx + dy * dy;
};

export const len = (x: number, y: number): number => Math.hypot(x, y);

export const rand = (a: number, b: number): number => a + Math.random() * (b - a);

export const randi = (a: number, b: number): number =>
  Math.floor(rand(a, b + 1));

/** Frame-rate independent exponential smoothing factor. */
export const damp = (rate: number, dt: number): number =>
  1 - Math.exp(-rate * dt);
