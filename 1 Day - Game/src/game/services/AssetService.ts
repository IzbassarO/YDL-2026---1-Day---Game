// Loads sprite frames and resolves animation clips. Browser-only.
// Frames live in /public/frames and are served at /frames/<name>.png.

export type ClipName =
  | "player_idle"
  | "player_run"
  | "player_attack"
  | "player_damage"
  | "mob_walk"
  | "mob_lunge"
  | "mob_death";

const CLIPS: Record<ClipName, string[]> = {
  player_idle: ["player_1_idle_1", "player_1_idle_2", "player_1_idle_3"],
  player_run: ["player_2_run_1", "player_2_run_2", "player_2_run_3"],
  player_attack: ["player_3_attack_1", "player_3_attack_2", "player_3_attack_3"],
  player_damage: ["player_4_damage_1", "player_4_damage_2", "player_4_damage_3"],
  mob_walk: ["mob_1_walk_1", "mob_1_walk_2", "mob_1_walk_3"],
  mob_lunge: ["mob_2_lunge_1", "mob_2_lunge_2", "mob_2_lunge_3"],
  mob_death: ["mob_3_death_1", "mob_3_death_2", "mob_3_death_3"],
};

export class AssetService {
  private images = new Map<string, HTMLImageElement>();
  ready = false;

  /** Kick off loading every frame. Renderer falls back to shapes until ready. */
  loadAll(): void {
    if (typeof window === "undefined") return;
    const names = new Set<string>();
    for (const list of Object.values(CLIPS)) list.forEach((n) => names.add(n));

    let remaining = names.size;
    if (remaining === 0) {
      this.ready = true;
      return;
    }
    for (const name of names) {
      const img = new Image();
      img.src = `/frames/${name}.png`;
      const done = () => {
        remaining--;
        if (remaining <= 0) this.ready = true;
      };
      img.onload = done;
      img.onerror = done; // don't block the game if one frame 404s
      this.images.set(name, img);
    }
  }

  /** Resolve a clip + playback time to a ready frame, or null while loading. */
  frame(clip: ClipName, time: number, fps: number, loop = true): HTMLImageElement | null {
    const list = CLIPS[clip];
    if (!list) return null;
    let i = Math.floor(time * fps);
    i = loop ? i % list.length : Math.min(i, list.length - 1);
    const img = this.images.get(list[i]);
    if (img && img.complete && img.naturalWidth > 0) return img;
    return null;
  }
}
