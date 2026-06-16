"use client";

import { useEffect, useRef, useState } from "react";
import { GameState } from "@/game/core/constants";
import { useGameViewModel } from "@/components/useGameViewModel";
import Hud from "@/components/Hud";
import SkillSelect from "@/components/SkillSelect";
import { Menu, Settings, Paused, GameOver } from "@/components/Screens";

export default function GameShell() {
  const { vm, snap } = useGameViewModel();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (canvasRef.current) vm.mount(canvasRef.current);
    return () => vm.unmount();
  }, [vm]);

  return (
    <div className="shell">
      <canvas ref={canvasRef} className="game" />

      {/* Overlays gate on `mounted` to avoid SSR/localStorage hydration drift. */}
      {mounted && (
        <>
          {(snap.state === GameState.PLAYING ||
            snap.state === GameState.PAUSED ||
            snap.state === GameState.SKILL_SELECT) && <Hud snap={snap} />}

          {snap.state === GameState.MENU && <Menu vm={vm} snap={snap} />}
          {snap.state === GameState.SETTINGS && <Settings vm={vm} snap={snap} />}
          {snap.state === GameState.PAUSED && <Paused vm={vm} />}
          {snap.state === GameState.SKILL_SELECT && (
            <SkillSelect vm={vm} snap={snap} />
          )}
          {snap.state === GameState.GAME_OVER && <GameOver vm={vm} snap={snap} />}
        </>
      )}
    </div>
  );
}
