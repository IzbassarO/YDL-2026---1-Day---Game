import { PlayerModel } from "@/game/models/PlayerModel";

export interface SkillDef {
  id: string;
  name: string;
  desc: string;
  glyph: string; // tiny ASCII/emoji marker for the card
  apply: (p: PlayerModel) => void;
}

/**
 * Weapon upgrade pool. Each pad pick applies one of these to the player's
 * weapon modifiers (see PlayerModel). Several stack numerically.
 */
export const SKILLS: SkillDef[] = [
  {
    id: "spread",
    name: "Spread Shot",
    desc: "Fire two extra bolts on diagonals.",
    glyph: "⋋⋌",
    apply: (p) => {
      p.spread = true;
    },
  },
  {
    id: "double",
    name: "Double Tap",
    desc: "+1 parallel bolt per shot.",
    glyph: "‖",
    apply: (p) => {
      p.parallel += 1;
    },
  },
  {
    id: "homing",
    name: "Homing Rounds",
    desc: "Bolts curve to follow the nearest enemy.",
    glyph: "↺",
    apply: (p) => {
      p.homing = true;
    },
  },
  {
    id: "pierce",
    name: "Piercing Slug",
    desc: "Bolts punch through enemies. +damage.",
    glyph: "➤",
    apply: (p) => {
      p.pierce = true;
      p.damageMul *= 1.8;
    },
  },
  {
    id: "rapid",
    name: "Overclock",
    desc: "Fire 25% faster.",
    glyph: "⚡",
    apply: (p) => {
      p.fireRateMul *= 0.75;
    },
  },
  {
    id: "heavy",
    name: "Heavy Caliber",
    desc: "Bigger, harder-hitting bolts.",
    glyph: "◉",
    apply: (p) => {
      p.damageMul *= 1.6;
      p.bulletSizeMul *= 1.4;
    },
  },
];

/** Pick `n` distinct skills at random for a pad. */
export function rollSkills(n = 3): SkillDef[] {
  const pool = [...SKILLS];
  const out: SkillDef[] = [];
  for (let i = 0; i < n && pool.length; i++) {
    const idx = Math.floor(Math.random() * pool.length);
    out.push(pool.splice(idx, 1)[0]);
  }
  return out;
}
