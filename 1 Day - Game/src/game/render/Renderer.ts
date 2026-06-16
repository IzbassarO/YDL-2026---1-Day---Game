import { TileMap } from "@/game/models/TileMap";
import { PlayerModel } from "@/game/models/PlayerModel";
import { MobModel } from "@/game/models/MobModel";
import { BulletModel } from "@/game/models/BulletModel";
import { ParticleModel } from "@/game/models/ParticleModel";
import { CoinModel } from "@/game/models/CoinModel";
import { SkillZoneModel } from "@/game/models/SkillZoneModel";
import { CameraService } from "@/game/services/CameraService";
import { AssetService, ClipName } from "@/game/services/AssetService";
import { CFG, PALETTE } from "@/game/core/constants";
import { dist2 } from "@/game/core/Vec";

export interface RenderWorld {
  map: TileMap;
  player: PlayerModel;
  mobs: MobModel[];
  bullets: BulletModel[];
  particles: ParticleModel[];
  coins: CoinModel[];
  zones: SkillZoneModel[];
}

/**
 * All drawing lives here so models stay pure. Pseudo-3D feel via tall walls,
 * elliptical shadows, Y-depth sorting and additive neon glows.
 *
 * NOTE: characters are drawn as polished placeholder shapes. Sprite-sheet
 * swap-in is isolated to drawPlayer / drawMob (see images/ assets later).
 */
export class Renderer {
  // tuned display heights (sprites are 256² with feet near the bottom)
  private static PLAYER_SIZE = 108;
  private static MOB_SIZE = 112;

  constructor(
    private ctx: CanvasRenderingContext2D,
    private assets: AssetService,
  ) {}

  draw(world: RenderWorld, cam: CameraService, vw: number, vh: number, time: number): void {
    const ctx = this.ctx;
    ctx.fillStyle = PALETTE.bg;
    ctx.fillRect(0, 0, vw, vh);

    ctx.save();
    ctx.translate(Math.round(-cam.x + cam.offX), Math.round(-cam.y + cam.offY));

    this.drawMap(world.map, cam, vw, vh);

    // Skill pads sit on the floor, beneath everything else.
    for (const z of world.zones) this.drawZone(z, time);

    // Sprites carry a baked soft shadow; only add code shadows in fallback mode.
    if (!this.assets.ready) {
      this.shadow(world.player.x, world.player.y, world.player.radius);
      for (const m of world.mobs) this.shadow(m.x, m.y, m.radius);
    }

    // Depth sort player + mobs by Y so lower entities overlap higher ones.
    const ents: (PlayerModel | MobModel)[] = [world.player, ...world.mobs];
    ents.sort((a, b) => a.y - b.y);
    for (const e of ents) {
      if (e === world.player) this.drawPlayer(world.player, time);
      else this.drawMob(e as MobModel, world.player, time);
    }

    for (const c of world.coins) this.drawCoin(c, time);
    for (const b of world.bullets) this.drawBullet(b);
    for (const p of world.particles) this.drawParticle(p);

    ctx.restore();

    // Vignette + scanlines for the terminal feel.
    this.drawVignette(vw, vh);
  }

  private drawMap(map: TileMap, cam: CameraService, vw: number, vh: number): void {
    const ctx = this.ctx;
    const T = map.T;
    const c0 = Math.max(0, Math.floor(cam.x / T) - 1);
    const c1 = Math.min(map.cols - 1, Math.floor((cam.x + vw) / T) + 1);
    const r0 = Math.max(0, Math.floor(cam.y / T) - 1);
    const r1 = Math.min(map.rows - 1, Math.floor((cam.y + vh) / T) + 1);

    // floor pass
    for (let r = r0; r <= r1; r++) {
      for (let c = c0; c <= c1; c++) {
        if (map.at(c, r) !== 0) continue;
        const x = c * T;
        const y = r * T;
        ctx.fillStyle = (c + r) & 1 ? PALETTE.floorA : PALETTE.floorB;
        ctx.fillRect(x, y, T, T);
        ctx.strokeStyle = "rgba(66,232,244,0.05)";
        ctx.strokeRect(x + 0.5, y + 0.5, T - 1, T - 1);
      }
    }
    // wall pass (drawn after floor so faces overlap the tile above)
    for (let r = r0; r <= r1; r++) {
      for (let c = c0; c <= c1; c++) {
        if (map.at(c, r) !== 1) continue;
        const x = c * T;
        const y = r * T;
        const openBelow = map.at(c, r + 1) === 0;
        ctx.fillStyle = PALETTE.wallBody;
        ctx.fillRect(x, y, T, T);
        // lit top cap
        ctx.fillStyle = PALETTE.wallFace;
        ctx.fillRect(x, y, T, T * 0.55);
        ctx.fillStyle = "rgba(125,77,255,0.28)";
        ctx.fillRect(x, y, T, 4);
        // neon base line where a wall meets open floor below (depth cue)
        if (openBelow) {
          ctx.fillStyle = "rgba(66,232,244,0.18)";
          ctx.fillRect(x, y + T - 3, T, 3);
        }
      }
    }
  }

  private shadow(x: number, y: number, r: number): void {
    const ctx = this.ctx;
    ctx.fillStyle = PALETTE.shadow;
    ctx.beginPath();
    ctx.ellipse(x, y + r * 0.72, r * 1.05, r * 0.5, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  /** Draw a sprite frame anchored at the entity's feet, optional H-flip. */
  private blit(
    img: HTMLImageElement,
    x: number,
    y: number,
    size: number,
    flip: boolean,
  ): void {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(x, y);
    if (flip) ctx.scale(-1, 1);
    // feet sit ~just below the entity center (frame feet ≈ 0.82 of height)
    ctx.drawImage(img, -size / 2, -size * 0.78, size, size);
    ctx.restore();
  }

  private drawPlayer(p: PlayerModel, time: number): void {
    let clip: ClipName = "player_idle";
    let loop = true;
    if (p.flash > 0.12) clip = "player_damage";
    else if (p.attackTimer > 0) {
      clip = "player_attack";
      loop = false;
    } else if (p.moving) clip = "player_run";

    const img = this.assets.frame(clip, p.animTime, CFG.anim.fps, loop);
    if (img) {
      this.blit(img, p.x, p.y, Renderer.PLAYER_SIZE, p.facing > 0);
      return;
    }
    this.fallbackBlob(p.x, p.y, p.radius, p.flash > 0, PALETTE.cyan, time);
  }

  private drawMob(m: MobModel, player: PlayerModel, time: number): void {
    let clip: ClipName = "mob_walk";
    let animTime = m.animTime;
    let loop = true;
    if (m.dying) {
      clip = "mob_death";
      animTime = m.deathTime;
      loop = false;
    } else if (
      dist2(m.x, m.y, player.x, player.y) <
      (m.radius + player.radius + CFG.mob.lungeRange) ** 2
    ) {
      clip = "mob_lunge";
    }

    const img = this.assets.frame(clip, animTime, CFG.anim.fps, loop);
    if (img) {
      const flip = m.vx > 6;
      const fade = m.dying ? Math.max(0, 1 - m.deathTime / CFG.mob.deathDuration) : 1;
      this.ctx.globalAlpha = fade;
      this.blit(img, m.x, m.y, Renderer.MOB_SIZE, flip);
      this.ctx.globalAlpha = 1;
    } else {
      this.fallbackBlob(m.x, m.y, m.radius, m.flash > 0, PALETTE.red, time);
    }

    // health pip (always, on top of the sprite)
    if (!m.dying && m.hp < m.maxHp) {
      const ctx = this.ctx;
      const w = m.radius * 2;
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(m.x - m.radius, m.y - m.radius - 30, w, 4);
      ctx.fillStyle = PALETTE.green;
      ctx.fillRect(m.x - m.radius, m.y - m.radius - 30, w * (m.hp / m.maxHp), 4);
    }
  }

  /** Neon-blob fallback used until sprite frames finish loading. */
  private fallbackBlob(
    x: number,
    y: number,
    r: number,
    hit: boolean,
    accent: string,
    time: number,
  ): void {
    const ctx = this.ctx;
    const wobble = Math.sin(time * 9 + x) * 1.5;
    ctx.save();
    ctx.translate(x, y - 4);
    ctx.fillStyle = hit ? "#ffffff" : "#1b2540";
    ctx.beginPath();
    ctx.arc(0, wobble * 0.3, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = accent;
    ctx.stroke();
    ctx.restore();
  }

  private drawBullet(b: BulletModel): void {
    const ctx = this.ctx;
    // fading trail
    if (b.trail.length >= 4) {
      ctx.lineCap = "round";
      for (let i = 0; i < b.trail.length - 2; i += 2) {
        const t = i / b.trail.length;
        ctx.strokeStyle = `rgba(255,184,77,${0.08 + t * 0.25})`;
        ctx.lineWidth = 1 + t * b.radius;
        ctx.beginPath();
        ctx.moveTo(b.trail[i], b.trail[i + 1]);
        ctx.lineTo(b.trail[i + 2], b.trail[i + 3]);
        ctx.stroke();
      }
    }
    // glowing head
    ctx.save();
    ctx.fillStyle = "#fff6e0";
    ctx.shadowColor = PALETTE.amber;
    ctx.shadowBlur = 16;
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  private drawParticle(p: ParticleModel): void {
    const ctx = this.ctx;
    const a = Math.max(0, p.life / p.max);
    ctx.globalAlpha = a;
    ctx.fillStyle = p.color;
    ctx.fillRect(p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
    ctx.globalAlpha = 1;
  }

  private drawZone(z: SkillZoneModel, time: number): void {
    const ctx = this.ctx;
    const pulse = 0.5 + 0.5 * Math.sin(time * 3);
    ctx.save();
    ctx.translate(z.x, z.y);

    // glowing hex pad
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 3) * i - Math.PI / 6;
      const px = Math.cos(a) * z.radius;
      const py = Math.sin(a) * z.radius * 0.55; // squashed for 3/4 view
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = `rgba(125,77,255,${0.1 + pulse * 0.12})`;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = PALETTE.purple;
    ctx.shadowColor = PALETTE.purple;
    ctx.shadowBlur = 16;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // charge ring
    if (z.charge > 0) {
      ctx.beginPath();
      ctx.arc(0, 0, z.radius * 0.62, -Math.PI / 2, -Math.PI / 2 + z.progress * Math.PI * 2);
      ctx.strokeStyle = PALETTE.cyan;
      ctx.lineWidth = 4;
      ctx.shadowColor = PALETTE.cyan;
      ctx.shadowBlur = 12;
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // central icon
    ctx.fillStyle = PALETTE.cyan;
    ctx.font = "bold 20px system-ui";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("✦", 0, 0);
    ctx.restore();
  }

  private drawCoin(c: CoinModel, time: number): void {
    const ctx = this.ctx;
    const blink = c.life < 3 ? (Math.sin(time * 16) > 0 ? 0.4 : 1) : 1;
    const w = Math.abs(Math.cos(c.spin)) * c.radius + 2; // spin shimmer
    ctx.save();
    ctx.globalAlpha = blink;
    ctx.translate(c.x, c.y);
    ctx.fillStyle = PALETTE.amber;
    ctx.shadowColor = PALETTE.amber;
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.ellipse(0, 0, w, c.radius, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.fillStyle = "rgba(255,255,255,0.7)";
    ctx.fillRect(-w * 0.3, -c.radius * 0.4, Math.max(1, w * 0.25), c.radius * 0.8);
    ctx.restore();
  }

  private drawVignette(vw: number, vh: number): void {
    const ctx = this.ctx;
    const g = ctx.createRadialGradient(
      vw / 2,
      vh / 2,
      Math.min(vw, vh) * 0.35,
      vw / 2,
      vh / 2,
      Math.max(vw, vh) * 0.75,
    );
    g.addColorStop(0, "rgba(0,0,0,0)");
    g.addColorStop(1, "rgba(0,0,0,0.5)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, vw, vh);
  }
}
