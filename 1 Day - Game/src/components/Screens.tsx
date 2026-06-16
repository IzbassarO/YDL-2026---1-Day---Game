"use client";

import { CFG, Difficulty } from "@/game/core/constants";
import { GameViewModel, HudSnapshot } from "@/game/viewmodels/GameViewModel";

export function Menu({ vm, snap }: { vm: GameViewModel; snap: HudSnapshot }) {
  return (
    <div className="overlay menu">
      <div className="title">BUDDY PROTOCOL</div>
      <div className="subtitle">NEON QUARANTINE</div>

      {/* Buddy greets the player on the main screen. */}
      <div className="menu-buddy">
        <div className="buddy-drone">
          <div className="buddy-ring" />
          <div className="buddy-body" />
          <div className="buddy-eye" />
        </div>
        <div className="cloud" style={{ minWidth: 300, maxWidth: 380 }}>
          <div className="name">◈ BUDDY</div>
          <div className="text" style={{ minHeight: 0 }}>
            Welcome to N-7. I auto-aim at the nearest enemy I can see — you just
            move and survive. Grab coins and stand on a ✦ pad to unlock skills.
          </div>
        </div>
      </div>

      {/* HUD layout + controls explainer */}
      <div className="menu-info">
        <div className="info-card">
          <div className="info-title">HUD LAYOUT</div>
          <div className="hudmap">
            <span className="tl">❤ Integrity</span>
            <span className="tc">⌛ Timer / Wave</span>
            <span className="tr">★ Score / ◎ Coins</span>
            <span className="mid">your operative</span>
          </div>
        </div>
        <div className="info-card">
          <div className="info-title">CONTROLS</div>
          <ul className="keys">
            <li><b>WASD</b> / <b>Arrows</b> — move</li>
            <li><b>Auto</b> — weapon fires itself</li>
            <li><b>1 / 2 / 3</b> — pick a skill</li>
            <li><b>P</b> / <b>Esc</b> — pause &nbsp; <b>R</b> — restart</li>
          </ul>
        </div>
      </div>

      <div className="row" style={{ marginTop: 6 }}>
        <button className="btn" onClick={() => vm.startRun()}>
          Start
        </button>
        <button className="btn secondary" onClick={() => vm.openSettings()}>
          Settings
        </button>
      </div>
      <div className="hint">
        {snap.best > 0
          ? `Best score: ${snap.best}  •  Difficulty: ${snap.difficulty}`
          : "Move • Survive • Let Buddy do the aiming"}
      </div>
    </div>
  );
}

export function Settings({ vm, snap }: { vm: GameViewModel; snap: HudSnapshot }) {
  const diffs = Object.keys(CFG.difficulty) as Difficulty[];
  return (
    <div className="overlay">
      <div className="title" style={{ fontSize: 44 }}>
        SETTINGS
      </div>
      <div className="col">
        <div className="hint" style={{ marginBottom: 4 }}>
          Difficulty
        </div>
        <div className="seg">
          {diffs.map((d) => (
            <button
              key={d}
              className={snap.difficulty === d ? "active" : ""}
              onClick={() => vm.setDifficulty(d)}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      <div className="col">
        <div className="hint" style={{ marginBottom: 4 }}>
          Music
        </div>
        <div className="seg">
          <button
            className={snap.musicEnabled ? "active" : ""}
            onClick={() => vm.setMusic(true)}
          >
            On
          </button>
          <button
            className={!snap.musicEnabled ? "active" : ""}
            onClick={() => vm.setMusic(false)}
          >
            Off
          </button>
        </div>
      </div>

      <button className="btn" onClick={() => vm.toMenu()}>
        Back
      </button>
    </div>
  );
}

export function Paused({ vm }: { vm: GameViewModel }) {
  return (
    <div className="overlay">
      <div className="title" style={{ fontSize: 48 }}>
        PAUSED
      </div>
      <button className="btn" onClick={() => vm.togglePause()}>
        Resume
      </button>
      <button className="btn secondary" onClick={() => vm.toMenu()}>
        Quit to Menu
      </button>
      <div className="hint">Press P or Esc to resume</div>
    </div>
  );
}

export function GameOver({ vm, snap }: { vm: GameViewModel; snap: HudSnapshot }) {
  return (
    <div className="overlay">
      <div
        className="title"
        style={{
          fontSize: 52,
          color: "var(--red)",
          textShadow: "0 0 18px rgba(255,77,109,.7)",
        }}
      >
        GAME OVER
      </div>
      <div className="stat">
        Score: <b>{snap.score}</b>
      </div>
      <div className="stat">
        Best: <b>{snap.best}</b>
      </div>
      <div className="stat">
        Survived: <b>{Math.floor(snap.time)}s</b>
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        <button className="btn" onClick={() => vm.startRun()}>
          Restart
        </button>
        <button className="btn secondary" onClick={() => vm.toMenu()}>
          Main Menu
        </button>
      </div>
      <div className="hint">Press R to restart</div>
    </div>
  );
}
