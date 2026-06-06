import { useEffect, useRef, useState } from "react";

const ITEMS = [
  { emoji: "🚗", label: "Automóvil", value: 1_600_000, display: "1,600,000" },
  { emoji: "🚶", label: "Peatones", value: 273_000, display: "273,000" },
  { emoji: "🏍️", label: "Moto", value: 127_000, display: "127,000" },
  { emoji: "🚲", label: "Bicicleta", value: 12_500, display: "12,500" },
  { emoji: "🛴", label: "Scooter", value: 245, display: "245" },
  { emoji: "🔀", label: "Otros medios", value: 20_000, display: "20,000" },
];

const TARGET = 2_115_800;
const COUNT_DURATION = 2200;
const CARD_INTERVAL = 1600;

export function ProblemStats() {
  const rootRef = useRef<HTMLDivElement>(null);
  const [count, setCount] = useState(0);
  const [activeIdx, setActiveIdx] = useState(-1);
  const [showRobbery, setShowRobbery] = useState(false);
  const startedRef = useRef(false);

  const runSequence = (idx: number) => {
    setActiveIdx(idx);
    if (idx < ITEMS.length - 1) {
      window.setTimeout(() => runSequence(idx + 1), CARD_INTERVAL);
    } else {
      window.setTimeout(() => setShowRobbery(true), 800);
    }
  };

  useEffect(() => {
    if (!rootRef.current) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting && !startedRef.current) {
            startedRef.current = true;
            const start = performance.now();
            const tick = (now: number) => {
              const p = Math.min((now - start) / COUNT_DURATION, 1);
              const eased = 1 - Math.pow(1 - p, 3);
              setCount(Math.floor(eased * TARGET));
              if (p < 1) requestAnimationFrame(tick);
              else {
                setCount(TARGET);
                window.setTimeout(() => runSequence(0), 200);
              }
            };
            requestAnimationFrame(tick);
          }
        });
      },
      { threshold: 0.25 },
    );
    obs.observe(rootRef.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={rootRef} className="mt-20">
      {/* Grand total */}
      <div className="relative text-center">
        <div
          aria-hidden
          className="pointer-events-none absolute left-1/2 top-1/2 -z-0 h-[420px] w-[620px] -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{ background: "radial-gradient(circle, rgba(13,148,136,0.18), transparent 65%)" }}
        />
        <p className="relative text-xs font-semibold uppercase tracking-[0.22em] text-teal-400">
          Accidentes registrados en México
        </p>
        <p
          className="relative font-display font-extrabold leading-none mt-4"
          style={{ fontSize: "clamp(3.8rem, 11vw, 7rem)", color: "#2DD4BF" }}
        >
          {count.toLocaleString("en-US")}
        </p>
        <p className="relative mt-4 text-slate-400">
          accidentes con distintos medios de transporte cada año
        </p>
      </div>

      {/* Cards */}
      <div className="mt-12 overflow-hidden">
        <div className="flex flex-nowrap justify-center gap-4">
          {ITEMS.map((it, i) => {
            const state =
              i === activeIdx ? "active" : i < activeIdx ? "visited" : "idle";
            const base =
              "flex shrink-0 flex-col items-center rounded-2xl border bg-slate-800/65 p-4 text-center backdrop-blur-md";
            const w = "w-[150px] md:w-[160px]";
            const styleByState =
              state === "active"
                ? "border-teal-400/60"
                : state === "visited"
                  ? "border-teal-400/20"
                  : "border-slate-400/15";
            const transform =
              state === "active"
                ? "scale(1.07)"
                : state === "visited"
                  ? "scale(0.96)"
                  : "scale(0.93)";
            const opacity =
              state === "active" ? 1 : state === "visited" ? 0.62 : 0.38;
            const shadow =
              state === "active"
                ? "0 0 24px rgba(45,212,191,0.22)"
                : "none";
            return (
              <div
                key={it.label}
                className={`${base} ${w} ${styleByState}`}
                style={{
                  transition: "all 0.4s ease",
                  transform,
                  opacity,
                  boxShadow: shadow,
                }}
              >
                <div
                  className="flex items-center justify-center rounded-[14px] bg-teal-500/15 text-2xl"
                  style={{ width: 54, height: 54 }}
                >
                  <span>{it.emoji}</span>
                </div>
                <p
                  className="mt-3 font-display font-extrabold"
                  style={{ color: "#2DD4BF", fontSize: "1.25rem" }}
                >
                  {it.display}
                </p>
                <p className="mt-1 text-xs text-slate-500">{it.label}</p>
              </div>
            );
          })}
        </div>

        {/* Dots */}
        <div className="mt-6 flex justify-center gap-2">
          {ITEMS.map((_, i) => {
            const isActive = i === activeIdx;
            const isVisited = i < activeIdx;
            return (
              <button
                key={i}
                aria-label={`Mostrar tarjeta ${i + 1}`}
                onClick={() => setActiveIdx(i)}
                className="rounded-full"
                style={{
                  width: 7,
                  height: 7,
                  background: isActive
                    ? "#2DD4BF"
                    : isVisited
                      ? "#0F766E"
                      : "#475569",
                  transform: isActive ? "scale(1.4)" : "scale(1)",
                  transition: "all 0.3s ease",
                }}
              />
            );
          })}
        </div>
      </div>

      {/* Robbery callout */}
      <div className="mt-10 flex justify-center">
        <div
          className="flex w-full max-w-[540px] items-center gap-5 rounded-[14px] px-5 py-5 md:flex-row flex-col md:text-left text-center"
          style={{
            background: "rgba(239,68,68,0.07)",
            border: "1px solid rgba(239,68,68,0.22)",
            opacity: showRobbery ? 1 : 0,
            transform: showRobbery ? "translateY(0)" : "translateY(12px)",
            transition: "all 0.6s ease",
            padding: "20px 32px",
          }}
        >
          <div style={{ fontSize: "2rem" }}>👜</div>
          <div>
            <p
              className="font-display font-extrabold"
              style={{ color: "#F87171", fontSize: "1.6rem", lineHeight: 1 }}
            >
              +150,000
            </p>
            <p className="mt-2 text-sm text-slate-400">
              robos a transeúntes registrados — muchos ocurriendo en las mismas rutas "optimizadas"
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
