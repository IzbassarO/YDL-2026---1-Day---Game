// Central tunables — single source of truth for balance & palette.
// Mirrors buddy_protocol_game_design.md section 8.

export const CFG = {
  TILE: 64,

  player: {
    hp: 100,
    speed: 240, // px/sec max
    accel: 2400, // px/sec^2 — "soft" acceleration
    friction: 12, // velocity damping when no input
    radius: 16,
  },

  weapon: {
    fireRateMs: 320,
    range: 520,
    bulletSpeed: 700,
    bulletDamage: 25,
    bulletRadius: 5,
    trailLength: 10,
  },

  mob: {
    hp: 50,
    speedMin: 70,
    speedMax: 110,
    accel: 900,
    contactDps: 10,
    radius: 18,
    separation: 26, // soft crowd spacing
    scorePerKill: 10,
    deathDuration: 0.45, // seconds the death animation plays before culling
    lungeRange: 46, // distance at which the mob plays its lunge clip
  },

  anim: {
    fps: 9,
    attackHold: 0.18, // seconds the player holds the attack pose after firing
  },

  coin: {
    radius: 9,
    pickupRadius: 26,
    life: 12, // seconds before a dropped coin fades
    value: 1,
    scoreBonus: 5,
    dropChance: 0.85,
  },

  zone: {
    count: 2, // skill pads per level
    radius: 46,
    chargeMin: 5, // seconds of standing to open a skill choice
    chargeMax: 10,
  },

  waves: {
    baseCount: 6,
    perWave: 3,
    intervalSec: 9,
    maxAlive: 90,
    hpScale: 0.12,
    speedScale: 0.05,
  },

  camera: {
    follow: 6, // higher = snappier
    shakeDecay: 42,
    shakeMax: 18,
  },

  difficulty: {
    Easy: { dmgMul: 0.6, countMul: 0.7, speedMul: 0.9 },
    Normal: { dmgMul: 1, countMul: 1, speedMul: 1 },
    Hard: { dmgMul: 1.5, countMul: 1.4, speedMul: 1.15 },
  },
} as const;

export type Difficulty = keyof typeof CFG.difficulty;

export const PALETTE = {
  bg: "#080B16",
  floorA: "#12192B",
  floorB: "#141d31",
  panel: "#172033",
  wallBody: "#0c1020",
  wallFace: "#1d2740",
  cyan: "#42E8F4",
  purple: "#7D4DFF",
  amber: "#FFB84D",
  red: "#FF4D6D",
  green: "#66FF99",
  white: "#EAF6FF",
  shadow: "rgba(0,0,0,0.45)",
} as const;

export enum GameState {
  MENU = "menu",
  SETTINGS = "settings",
  PLAYING = "playing",
  PAUSED = "paused",
  SKILL_SELECT = "skill_select",
  GAME_OVER = "game_over",
}

