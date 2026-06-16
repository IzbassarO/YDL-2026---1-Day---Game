"use client";

import { GameViewModel, HudSnapshot } from "@/game/viewmodels/GameViewModel";

/**
 * Skill-pad choice. The world is frozen while this is up. Pick with the mouse
 * or the 1 / 2 / 3 keys (handled in InputService -> vm.pickSkill).
 */
export default function SkillSelect({
  vm,
  snap,
}: {
  vm: GameViewModel;
  snap: HudSnapshot;
}) {
  return (
    <div className="overlay skill-overlay">
      <div className="buddy-drone" style={{ marginBottom: 6 }}>
        <div className="buddy-ring" />
        <div className="buddy-body" />
        <div className="buddy-eye" />
      </div>
      <div className="title" style={{ fontSize: 40 }}>
        CHOOSE A PROTOCOL
      </div>
      <div className="hint" style={{ marginTop: -6 }}>
        Buddy found an upgrade cache. Pick one — press 1 / 2 / 3 or click.
      </div>

      <div className="skill-row">
        {snap.skillChoices.map((s, i) => (
          <button
            key={s.id}
            className="skill-card"
            onClick={() => vm.pickSkill(i)}
          >
            <div className="skill-key">{i + 1}</div>
            <div className="skill-glyph">{s.glyph}</div>
            <div className="skill-name">{s.name}</div>
            <div className="skill-desc">{s.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
