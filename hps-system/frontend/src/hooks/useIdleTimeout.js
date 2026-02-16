import { useEffect, useRef } from 'react';

const ACTIVITY_EVENTS = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'];

/**
 * Cierra sesión tras X minutos de inactividad (idle timeout).
 * @param {boolean} enabled - Si true, el timer está activo
 * @param {number} minutes - Minutos de inactividad antes de llamar a onIdle
 * @param {() => void} onIdle - Callback cuando se cumple el tiempo (ej. logout y redirect)
 */
export function useIdleTimeout(enabled, minutes, onIdle) {
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!enabled || !onIdle || minutes <= 0) return;

    const resetTimer = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        onIdle();
      }, minutes * 60 * 1000);
    };

    resetTimer();
    ACTIVITY_EVENTS.forEach((e) => window.addEventListener(e, resetTimer));
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      ACTIVITY_EVENTS.forEach((e) => window.removeEventListener(e, resetTimer));
    };
  }, [enabled, minutes, onIdle]);
}
