// Minimal typed pub/sub so services and views communicate without hard refs.

export type GameEvent =
  | { type: "mobKilled"; x: number; y: number }
  | { type: "playerHit"; amount: number }
  | { type: "waveStarted"; wave: number }
  | { type: "gameOver"; score: number; time: number }
  | { type: "bulletFired"; x: number; y: number };

type Handler = (e: GameEvent) => void;

export class EventBus {
  private handlers = new Set<Handler>();

  on(h: Handler): () => void {
    this.handlers.add(h);
    return () => this.handlers.delete(h);
  }

  emit(e: GameEvent): void {
    for (const h of this.handlers) h(e);
  }

  clear(): void {
    this.handlers.clear();
  }
}
