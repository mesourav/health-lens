import { useEffect, useRef } from 'react';

/** Scrolls the returned element to the bottom whenever `trigger` changes. */
export function useAutoScroll<T extends HTMLElement>(trigger: unknown) {
  const ref = useRef<T>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollTo({ top: el.scrollHeight, behavior: reduceMotion ? 'auto' : 'smooth' });
  }, [trigger]);

  return ref;
}
