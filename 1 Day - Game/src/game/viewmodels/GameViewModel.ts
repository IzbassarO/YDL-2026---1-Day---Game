import { CFG, Difficulty, GameState } from "@/game/core/constants";
import { dist2, rand } from "@/game/core/Vec";
import { EventBus } from "@/game/core/EventBus";
import { SkillDef, rollSkills } from "@/game/core/skills";

import { TileMap } from "@/game/models/TileMap";
import { PlayerModel } from "@/game/models/PlayerModel";
import { MobModel } from "@/game/models/MobModel";
import { BulletModel } from "@/game/models/BulletModel";
import { ParticleModel } from "@/game/models/ParticleModel";
import { CoinModel } from "@/game/models/CoinModel";
import { SkillZoneModel } from "@/game/models/SkillZoneModel";

import { InputService } from "@/game/services/InputService";
import { LevelGenerator } from "@/game/services/LevelGenerator";
import { CollisionService } from "@/game/services/CollisionService";
import { PathfindingService } from "@/game/services/PathfindingService";
import { AutoAimService } from "@/game/services/AutoAimService";
import { WaveService } from "@/game/services/WaveService";
import { CameraService } from "@/game/services/CameraService";
import { AssetService } from "@/game/services/AssetService";
import { AudioService } from "@/game/services/AudioService";
import { Renderer } from "@/game/render/Renderer";

export interface HudSnapshot {
  state: GameState;
  hp: number;
  maxHp: number;
  score: number;
  coins: number;
  time: number;
  wave: number;
  best: number;
  difficulty: Difficulty;
  musicEnabled: boolean;
  skillChoices: SkillDef[];
}

const BEST_KEY = "bp_best_v2";
const MUSIC_KEY = "bp_music";

/**
 * The ViewModel: single owner of game state and the RAF loop. Ticks services to
 * mutate models, draws via the Renderer, and publishes an immutable HUD snapshot
 * that React subscribes to (useSyncExternalStore). Views never touch models.
 */
export class GameViewModel {
  // ---- world ----
  private map!: TileMap;
  private player!: PlayerModel;
  private mobs: MobModel[] = [];
  private bullets: BulletModel[] = [];
  private particles: ParticleModel[] = [];
  private coins: CoinModel[] = [];
  private zones: SkillZoneModel[] = [];

  // ---- services ----
  private input = new InputService();
  private camera = new CameraService();
  private assets = new AssetService();
  private audio = new AudioService();
  private bus = new EventBus();
  private collision!: CollisionService;
  private pathfinder!: PathfindingService;
  private autoaim!: AutoAimService;
  private waves!: WaveService;
  private renderer: Renderer | null = null;

  // ---- runtime ----
  private canvas: HTMLCanvasElement | null = null;
  private raf = 0;
  private lastTs = 0;
  private time = 0; // total seconds (for animation)
  private elapsed = 0; // survival timer
  private score = 0;
  private coinCount = 0;
  private difficulty: Difficulty = "Normal";
  private best = 0;
  private musicEnabled = true;
  private skillChoices: SkillDef[] = [];
  private activeZone: SkillZoneModel | null = null;
  private state: GameState = GameState.MENU;

  // ---- snapshot plumbing (external store) ----
  private listeners = new Set<() => void>();
  private snapshot: HudSnapshot;
  private lastSig = "";

  constructor() {
    if (typeof window !== "undefined") {
      this.best = Number(localStorage.getItem(BEST_KEY) || 0);
      this.musicEnabled = localStorage.getItem(MUSIC_KEY) !== "0";
    }
    this.snapshot = this.buildSnapshot();
    this.input.onPause = () => this.togglePause();
    this.input.onRestart = () => {
      if (this.state === GameState.GAME_OVER) this.startRun();
    };
    this.input.onSkill = (i) => this.pickSkill(i);
  }

  // ============================ lifecycle ============================
  mount(canvas: HTMLCanvasElement): void {
    this.canvas = canvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    this.assets.loadAll();
    this.renderer = new Renderer(ctx, this.assets);
    this.input.attach();
    this.resize();
    window.addEventListener("resize", this.resize);
    this.lastTs = performance.now();
    this.raf = requestAnimationFrame(this.loop);
  }

  unmount(): void {
    cancelAnimationFrame(this.raf);
    this.input.detach();
    this.audio.dispose();
    this.bus.clear();
    window.removeEventListener("resize", this.resize);
    this.canvas = null;
    this.renderer = null;
  }

  private resize = (): void => {
    if (!this.canvas) return;
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  };

  // ============================ external store ============================
  subscribe = (cb: () => void): (() => void) => {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  };
  getSnapshot = (): HudSnapshot => this.snapshot;

  private notify(): void {
    for (const l of this.listeners) l();
  }

  private buildSnapshot(): HudSnapshot {
    return {
      state: this.state,
      hp: this.player ? this.player.hp : CFG.player.hp,
      maxHp: CFG.player.hp,
      score: this.score,
      coins: this.coinCount,
      time: this.elapsed,
      wave: this.waves ? this.waves.wave : 0,
      best: this.best,
      difficulty: this.difficulty,
      musicEnabled: this.musicEnabled,
      skillChoices: this.skillChoices,
    };
  }

  /** Rebuild + notify only when something the UI cares about changed. */
  private syncSnapshot(): void {
    const sig = [
      this.state,
      Math.ceil(this.player ? this.player.hp : CFG.player.hp),
      this.score,
      this.coinCount,
      Math.floor(this.elapsed),
      this.waves ? this.waves.wave : 0,
      this.best,
      this.difficulty,
      this.musicEnabled ? "m1" : "m0",
      this.skillChoices.map((s) => s.id).join(","),
    ].join("|");
    if (sig === this.lastSig) return;
    this.lastSig = sig;
    this.snapshot = this.buildSnapshot();
    this.notify();
  }

  // ============================ state transitions ============================
  private setState(s: GameState): void {
    this.state = s;
    this.syncSnapshot();
  }

  toMenu(): void {
    this.setState(GameState.MENU);
  }
  openSettings(): void {
    this.setState(GameState.SETTINGS);
  }
  setDifficulty(d: Difficulty): void {
    this.difficulty = d;
    this.syncSnapshot();
  }

  /** Toggle music. Called from a click, so the AudioContext can start. */
  setMusic(on: boolean): void {
    this.musicEnabled = on;
    if (typeof window !== "undefined")
      localStorage.setItem(MUSIC_KEY, on ? "1" : "0");
    this.audio.setEnabled(on);
    this.syncSnapshot();
  }
  togglePause(): void {
    if (this.state === GameState.PLAYING) this.setState(GameState.PAUSED);
    else if (this.state === GameState.PAUSED) this.setState(GameState.PLAYING);
  }

  /** Open the 3-skill choice. The world freezes (update only runs in PLAYING). */
  private enterSkillSelect(zone: SkillZoneModel): void {
    this.activeZone = zone;
    this.skillChoices = rollSkills(3);
    this.setState(GameState.SKILL_SELECT);
  }

  /** Apply the chosen skill (0..2) and resume play. Keyboard or mouse driven. */
  pickSkill(index: number): void {
    if (this.state !== GameState.SKILL_SELECT) return;
    const skill = this.skillChoices[index];
    if (!skill) return;
    skill.apply(this.player);
    if (this.activeZone) {
      this.activeZone.charge = 0;
      this.activeZone.needed *= 1.35; // each subsequent pick here takes longer
      this.activeZone.picks++;
    }
    this.skillChoices = [];
    this.activeZone = null;
    for (let i = 0; i < 18; i++)
      this.particles.push(ParticleModel.muzzle(this.player.x, this.player.y));
    this.setState(GameState.PLAYING);
  }

  // ============================ run lifecycle ============================
  startRun(): void {
    // first run is triggered by a click, so this is a valid moment to begin audio
    if (this.musicEnabled) this.audio.setEnabled(true);
    this.map = LevelGenerator.generate();
    this.collision = new CollisionService(this.map);
    this.pathfinder = new PathfindingService(this.map);
    this.autoaim = new AutoAimService(this.collision);
    this.waves = new WaveService(this.map, this.difficulty);

    const start = this.map.rooms[0];
    const T = this.map.T;
    this.player = new PlayerModel((start.cx + 0.5) * T, (start.cy + 0.5) * T);

    this.mobs = [];
    this.bullets = [];
    this.particles = [];
    this.coins = [];
    this.score = 0;
    this.coinCount = 0;
    this.elapsed = 0;
    this.skillChoices = [];
    this.activeZone = null;
    this.zones = this.createZones();
    this.waves.reset();
    this.pathfinder.forceRecompute();

    if (this.canvas) {
      this.camera.snapTo(
        this.player.x,
        this.player.y,
        this.canvas.width,
        this.canvas.height,
      );
    }

    // first wave immediately
    this.mobs.push(...this.waves.tick(CFG.waves.intervalSec + 1, 0));
    this.setState(GameState.PLAYING);
  }

  private createZones(): SkillZoneModel[] {
    const rooms = this.map.rooms;
    const T = this.map.T;
    const zones: SkillZoneModel[] = [];
    const used = new Set<number>([0]); // never on the start room
    const want = Math.min(CFG.zone.count, Math.max(0, rooms.length - 1));
    let guard = 0;
    while (zones.length < want && guard++ < 50) {
      const idx = 1 + Math.floor(rand(0, rooms.length - 1));
      if (used.has(idx) || idx >= rooms.length) continue;
      used.add(idx);
      const rm = rooms[idx];
      zones.push(new SkillZoneModel((rm.cx + 0.5) * T, (rm.cy + 0.5) * T));
    }
    return zones;
  }

  private gameOver(): void {
    if (this.score > this.best) {
      this.best = this.score;
      if (typeof window !== "undefined")
        localStorage.setItem(BEST_KEY, String(this.best));
    }
    this.bus.emit({ type: "gameOver", score: this.score, time: this.elapsed });
    this.setState(GameState.GAME_OVER);
  }

  // ============================ main loop ============================
  private loop = (ts: number): void => {
    let dt = (ts - this.lastTs) / 1000;
    this.lastTs = ts;
    dt = Math.min(dt, 0.05); // clamp big gaps (tab switch)
    this.time += dt;

    if (this.state === GameState.PLAYING) this.update(dt);

    this.render();
    this.syncSnapshot();
    this.raf = requestAnimationFrame(this.loop);
  };

  private update(dt: number): void {
    this.elapsed += dt;

    this.updatePlayer(dt);
    this.updateWeapon(dt);

    // refresh the pursuit field toward the player's current tile
    this.pathfinder.update(
      this.map.colOf(this.player.x),
      this.map.rowOf(this.player.y),
    );

    this.updateMobs(dt);
    this.updateBullets(dt);
    this.updateParticles(dt);
    this.updateCoins(dt);
    this.updateZones(dt); // may flip state to SKILL_SELECT

    // spawn waves
    const spawned = this.waves.tick(dt, this.mobs.length);
    if (spawned.length) {
      this.mobs.push(...spawned);
      this.bus.emit({ type: "waveStarted", wave: this.waves.wave });
    }

    // cull dead
    this.mobs = this.mobs.filter((m) => !m.dead);
    this.bullets = this.bullets.filter((b) => !b.dead);
    this.particles = this.particles.filter((p) => !p.dead);
    this.coins = this.coins.filter((c) => !c.collected && c.life > 0);

    if (this.canvas) {
      this.camera.follow(
        this.player.x,
        this.player.y,
        this.canvas.width,
        this.canvas.height,
        dt,
      );
    }

    if (this.player.hp <= 0) this.gameOver();
  }

  private updatePlayer(dt: number): void {
    const p = this.player;
    const ax = this.input.axis();
    const accel = CFG.player.accel * dt;
    const desVX = ax.x * p.speed;
    const desVY = ax.y * p.speed;
    p.vx = approach(p.vx, desVX, accel);
    p.vy = approach(p.vy, desVY, accel);

    this.collision.move(p, p.vx * dt, p.vy * dt);

    p.moving = Math.hypot(p.vx, p.vy) > 12;
    if (Math.abs(p.vx) > 6) p.facing = Math.sign(p.vx);
    if (p.flash > 0) p.flash -= dt;
    if (p.attackTimer > 0) p.attackTimer -= dt;
    p.animTime += dt;
  }

  private updateWeapon(dt: number): void {
    const p = this.player;
    p.fireCooldown -= dt * 1000;
    if (p.fireCooldown > 0) return;

    const target = this.autoaim.pickTarget(p, this.mobs);
    if (!target) return;

    p.fireCooldown = CFG.weapon.fireRateMs * p.fireRateMul;
    p.attackTimer = CFG.anim.attackHold;

    const dx = target.x - p.x;
    const dy = target.y - p.y;
    const len = Math.hypot(dx, dy) || 1;
    const ux = dx / len;
    const uy = dy / len;
    p.facing = dx >= 0 ? 1 : -1;

    const opts = {
      damage: CFG.weapon.bulletDamage * p.damageMul,
      radius: CFG.weapon.bulletRadius * p.bulletSizeMul,
      pierce: p.pierce,
      homing: p.homing,
    };

    // parallel bolts, offset perpendicular to the aim line
    const perpX = -uy;
    const perpY = ux;
    const spacing = 10;
    for (let i = 0; i < p.parallel; i++) {
      const off = (i - (p.parallel - 1) / 2) * spacing;
      this.bullets.push(
        new BulletModel(p.x + perpX * off, p.y + perpY * off, ux, uy, opts),
      );
    }

    // spread: two extra diagonal bolts at ±22°
    if (p.spread) {
      for (const ang of [0.38, -0.38]) {
        const cos = Math.cos(ang);
        const sin = Math.sin(ang);
        this.bullets.push(
          new BulletModel(p.x, p.y, ux * cos - uy * sin, ux * sin + uy * cos, opts),
        );
      }
    }

    for (let i = 0; i < 3; i++)
      this.particles.push(ParticleModel.muzzle(p.x, p.y));
    this.bus.emit({ type: "bulletFired", x: p.x, y: p.y });
  }

  private updateMobs(dt: number): void {
    const p = this.player;
    const sep = CFG.mob.separation;
    const sep2 = sep * sep;

    for (const m of this.mobs) {
      // play out the death animation, then mark for culling
      if (m.dying) {
        m.deathTime += dt;
        if (m.flash > 0) m.flash -= dt;
        if (m.deathTime >= CFG.mob.deathDuration) m.dead = true;
        continue;
      }

      // pursuit direction from the flow field (navigates around walls)
      const dir = this.pathfinder.steer(m.x, m.y, p.x, p.y);
      let dvx = dir.x;
      let dvy = dir.y;

      // soft separation so the horde spreads instead of stacking
      for (const o of this.mobs) {
        if (o === m) continue;
        const d2 = dist2(m.x, m.y, o.x, o.y);
        if (d2 > 0 && d2 < sep2) {
          const d = Math.sqrt(d2);
          const push = (sep - d) / sep;
          dvx += ((m.x - o.x) / d) * push * 0.8;
          dvy += ((m.y - o.y) / d) * push * 0.8;
        }
      }

      const l = Math.hypot(dvx, dvy) || 1;
      const desVX = (dvx / l) * m.speed;
      const desVY = (dvy / l) * m.speed;
      const accel = CFG.mob.accel * dt;
      m.vx = approach(m.vx, desVX, accel);
      m.vy = approach(m.vy, desVY, accel);

      this.collision.move(m, m.vx * dt, m.vy * dt);
      if (m.flash > 0) m.flash -= dt;
      m.animTime += dt;

      // contact damage
      const rr = m.radius + p.radius;
      if (dist2(m.x, m.y, p.x, p.y) < rr * rr) {
        const dmg =
          CFG.mob.contactDps * CFG.difficulty[this.difficulty].dmgMul * dt;
        p.hurt(dmg);
        this.camera.addShake(2.5);
        this.bus.emit({ type: "playerHit", amount: dmg });
      }
    }
  }

  private updateBullets(dt: number): void {
    for (const b of this.bullets) {
      // homing: gently curve the velocity toward the nearest visible-ish mob
      if (b.homing) {
        const t = this.nearestActiveMob(b.x, b.y);
        if (t) {
          const dx = t.x - b.x;
          const dy = t.y - b.y;
          const l = Math.hypot(dx, dy) || 1;
          const turn = 6 * dt; // rad/sec blend
          b.vx += (dx / l) * b.speed * turn;
          b.vy += (dy / l) * b.speed * turn;
          const sp = Math.hypot(b.vx, b.vy) || 1;
          b.vx = (b.vx / sp) * b.speed;
          b.vy = (b.vy / sp) * b.speed;
        }
      }

      b.x += b.vx * dt;
      b.y += b.vy * dt;
      b.life -= dt;

      // record trail (flat x,y pairs, capped)
      b.trail.unshift(b.x, b.y);
      const cap = CFG.weapon.trailLength * 2;
      if (b.trail.length > cap) b.trail.length = cap;

      if (b.life <= 0 || this.map.isWallPx(b.x, b.y)) {
        b.dead = true;
        this.particles.push(ParticleModel.impact(b.x, b.y));
        continue;
      }

      for (const m of this.mobs) {
        if (!m.active || b.hitIds.has(m.id)) continue;
        const rr = b.radius + m.radius;
        if (dist2(b.x, b.y, m.x, m.y) < rr * rr) {
          const killed = m.hurt(b.damage);
          b.hitIds.add(m.id);
          this.particles.push(ParticleModel.impact(b.x, b.y));
          if (killed) this.onMobKilled(m);
          // piercing bolts pass through; normal bolts stop here
          if (!b.pierce) {
            b.dead = true;
            break;
          }
        }
      }
    }
  }

  private onMobKilled(m: MobModel): void {
    this.score += CFG.mob.scorePerKill;
    this.camera.addShake(3);
    for (let i = 0; i < 14; i++)
      this.particles.push(ParticleModel.death(m.x, m.y));
    if (Math.random() < CFG.coin.dropChance)
      this.coins.push(new CoinModel(m.x, m.y));
    this.bus.emit({ type: "mobKilled", x: m.x, y: m.y });
  }

  private nearestActiveMob(x: number, y: number): MobModel | null {
    let best: MobModel | null = null;
    let bd = Infinity;
    for (const m of this.mobs) {
      if (!m.active) continue;
      const d = dist2(x, y, m.x, m.y);
      if (d < bd) {
        bd = d;
        best = m;
      }
    }
    return best;
  }

  private updateCoins(dt: number): void {
    const p = this.player;
    const pick = CFG.coin.pickupRadius;
    for (const c of this.coins) {
      c.x += c.vx * dt;
      c.y += c.vy * dt;
      c.vx *= 0.9;
      c.vy *= 0.9;
      c.life -= dt;
      c.spin += dt * 6;
      if (dist2(c.x, c.y, p.x, p.y) < pick * pick) {
        c.collected = true;
        this.coinCount += CFG.coin.value;
        this.score += CFG.coin.scoreBonus;
      }
    }
  }

  private updateZones(dt: number): void {
    const p = this.player;
    for (const z of this.zones) {
      if (dist2(p.x, p.y, z.x, z.y) < z.radius * z.radius) {
        z.charge += dt;
        if (z.charge >= z.needed) {
          this.enterSkillSelect(z);
          return; // freeze; remaining zones handled next frame
        }
      }
    }
  }

  private updateParticles(dt: number): void {
    for (const p of this.particles) {
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.vx *= p.drag;
      p.vy *= p.drag;
      p.life -= dt;
      if (p.life <= 0) p.dead = true;
    }
  }

  private render(): void {
    if (!this.renderer || !this.canvas) return;
    const vw = this.canvas.width;
    const vh = this.canvas.height;
    if (!this.map) {
      // idle background before first run
      const ctx = this.canvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = "#080B16";
        ctx.fillRect(0, 0, vw, vh);
      }
      return;
    }
    this.renderer.draw(
      {
        map: this.map,
        player: this.player,
        mobs: this.mobs,
        bullets: this.bullets,
        particles: this.particles,
        coins: this.coins,
        zones: this.zones,
      },
      this.camera,
      vw,
      vh,
      this.time,
    );
  }
}

/** Move `cur` toward `target` by at most `maxDelta`. */
function approach(cur: number, target: number, maxDelta: number): number {
  const d = target - cur;
  if (d > maxDelta) return cur + maxDelta;
  if (d < -maxDelta) return cur - maxDelta;
  return target;
}
