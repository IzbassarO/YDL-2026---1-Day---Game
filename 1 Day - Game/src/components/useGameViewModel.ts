"use client";

import { useRef, useSyncExternalStore } from "react";
import { GameViewModel, HudSnapshot } from "@/game/viewmodels/GameViewModel";

/** Creates one stable ViewModel instance and subscribes React to its snapshot. */
export function useGameViewModel(): { vm: GameViewModel; snap: HudSnapshot } {
  const ref = useRef<GameViewModel | null>(null);
  if (ref.current === null) ref.current = new GameViewModel();
  const vm = ref.current;

  const snap = useSyncExternalStore(
    vm.subscribe,
    vm.getSnapshot,
    vm.getSnapshot,
  );

  return { vm, snap };
}
