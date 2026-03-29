import { AnimatePresence, motion as Motion } from "framer-motion";
import { Outlet, useLocation } from "react-router-dom";

export function RouteTransition() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <Motion.div
        key={location.pathname}
        initial={{ opacity: 0, x: 18, y: 8, filter: "blur(6px)" }}
        animate={{ opacity: 1, x: 0, y: 0, filter: "blur(0px)" }}
        exit={{ opacity: 0, x: -14, y: 5, filter: "blur(5px)" }}
        transition={{ duration: 0.34, ease: [0.22, 1, 0.36, 1] }}
      >
        <Outlet />
      </Motion.div>
    </AnimatePresence>
  );
}
