import { useEffect } from "react";

const DISMISS_MS = 30_000;

/** Clears `value` automatically after 30 seconds when it becomes non-null. */
export function useAutoDismiss(
  value: string | null,
  onDismiss: () => void,
  delayMs: number = DISMISS_MS,
) {
  useEffect(() => {
    if (!value) return;
    const timer = window.setTimeout(onDismiss, delayMs);
    return () => window.clearTimeout(timer);
  }, [value, onDismiss, delayMs]);
}
