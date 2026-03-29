import { animate } from "framer-motion";
import { useEffect, useRef } from "react";

export function AnimatedCounter({ value, decimals = 0 }) {
  const nodeRef = useRef(null);

  useEffect(() => {
    if (!nodeRef.current || Number.isNaN(Number(value))) return;

    const controls = animate(0, Number(value), {
      duration: 0.8,
      onUpdate(latest) {
        if (nodeRef.current) {
          nodeRef.current.textContent = latest.toFixed(decimals);
        }
      }
    });

    return () => controls.stop();
  }, [decimals, value]);

  return <span ref={nodeRef}>{value}</span>;
}
