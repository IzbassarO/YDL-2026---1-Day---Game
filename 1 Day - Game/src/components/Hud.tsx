"use client";

import { HudSnapshot } from "@/game/viewmodels/GameViewModel";

function formatTime(t: number): string {
  const s = Math.floor(t);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function Hud({ snap }: { snap: HudSnapshot }) {
  const pct = Math.max(0, (snap.hp / snap.maxHp) * 100);
  const low = pct < 35;
  return (
    <div className="hud">
      <div className="hud-top">
        <div className="hpwrap">
          <div className="hplabel">INTEGRITY</div>
          <div className="hpbar">
            <div
              className={`hpfill${low ? " low" : ""}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
        <div className="hud-center">
          <div className="timer">{formatTime(snap.time)}</div>
          <div className="wave">WAVE {snap.wave}</div>
        </div>
        <div>
          <div className="scorelabel">SCORE</div>
          <div className="score">{snap.score}</div>
          <div className="coins">◎ {snap.coins}</div>
        </div>
      </div>
      <div className="pausetag">P / ESC — PAUSE&nbsp;&nbsp;•&nbsp;&nbsp;STAND ON ✦ PADS FOR SKILLS</div>
    </div>
  );
}
