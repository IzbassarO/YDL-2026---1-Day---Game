// Keyboard manager. Owns no game logic — only reports intent.

export class InputService {
  private keys: Record<string, boolean> = {};
  onPause: (() => void) | null = null;
  onRestart: (() => void) | null = null;
  onSkill: ((index: number) => void) | null = null;

  private kd = (e: KeyboardEvent) => {
    // prevent page scroll on arrows/space
    if (
      ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(
        e.code,
      )
    )
      e.preventDefault();
    this.keys[e.code] = true;
    if (e.code === "KeyP" || e.code === "Escape") this.onPause?.();
    if (e.code === "KeyR") this.onRestart?.();
    // skill-select hotkeys 1/2/3 (top row or numpad)
    if (e.code === "Digit1" || e.code === "Numpad1") this.onSkill?.(0);
    if (e.code === "Digit2" || e.code === "Numpad2") this.onSkill?.(1);
    if (e.code === "Digit3" || e.code === "Numpad3") this.onSkill?.(2);
  };
  private ku = (e: KeyboardEvent) => {
    this.keys[e.code] = false;
  };

  attach(): void {
    window.addEventListener("keydown", this.kd);
    window.addEventListener("keyup", this.ku);
  }
  detach(): void {
    window.removeEventListener("keydown", this.kd);
    window.removeEventListener("keyup", this.ku);
    this.keys = {};
  }

  /** Normalized movement axis (diagonals are not faster). */
  axis(): { x: number; y: number } {
    let x = 0;
    let y = 0;
    if (this.keys.KeyA || this.keys.ArrowLeft) x -= 1;
    if (this.keys.KeyD || this.keys.ArrowRight) x += 1;
    if (this.keys.KeyW || this.keys.ArrowUp) y -= 1;
    if (this.keys.KeyS || this.keys.ArrowDown) y += 1;
    if (x && y) {
      const k = Math.SQRT1_2;
      x *= k;
      y *= k;
    }
    return { x, y };
  }
}
