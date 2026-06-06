import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { ArrowLeft, Minus, Plus, Send, X } from "lucide-react";

mapboxgl.accessToken =
  "pk.eyJ1IjoibGVvbmFyZG8wNDA2IiwiYSI6ImNtbnhqamdraDAzNWUyeW9sNnN0OXdlM3QifQ.7VbegBLq_o6xLiIoMni9nQ";

type Msg = {
  from: "bot" | "user";
  text?: string;
  consent?: boolean;
  progress?: boolean;
  iframe?: string;
};

export function DemoModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (open) setStep(0);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.92)" }}
    >
      <button
        onClick={onClose}
        aria-label="Cerrar demo"
        className="absolute right-6 top-6 text-2xl text-white/60 transition hover:text-white"
      >
        <X className="h-8 w-8" />
      </button>

      <div
        className="relative overflow-hidden bg-slate-950"
        style={{
          width: 360,
          maxWidth: "92vw",
          height: 720,
          maxHeight: "92vh",
          borderRadius: 44,
          border: "10px solid #2A3A4A",
          boxShadow: "0 40px 100px rgba(0,0,0,0.7)",
        }}
      >
        <div className="relative h-full w-full overflow-hidden">
          <Screen visible={step === 0}>
            <LoginScreen onSuccess={() => setStep(1)} />
          </Screen>
          <Screen visible={step === 1}>
            <ChatScreen active={step === 1} onAdvance={() => setStep(2)} />
          </Screen>
          <Screen visible={step === 2}>
            <MapScreen active={step === 2} onAdvance={() => setStep(3)} />
          </Screen>
          <Screen visible={step === 3}>
            <PoolScreen onAdvance={() => setStep(4)} />
          </Screen>
          <Screen visible={step === 4}>
            <RatingScreen active={step === 4} onHome={onClose} />
          </Screen>
        </div>
      </div>
    </div>
  );
}

function Screen({ visible, children }: { visible: boolean; children: React.ReactNode }) {
  return (
    <div
      className="absolute inset-0"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateX(0)" : "translateX(40px)",
        pointerEvents: visible ? "auto" : "none",
        transition: "opacity 0.3s ease, transform 0.3s ease",
      }}
    >
      {children}
    </div>
  );
}

/* ─────────────── SCREEN 0 — LOGIN ─────────────── */
function LoginScreen({ onSuccess }: { onSuccess: () => void }) {
  const [user, setUser] = useState("Alex");
  const [pwd, setPwd] = useState("password");
  const [loading, setLoading] = useState(false);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => onSuccess(), 800);
  };

  return (
    <div className="flex h-full w-full flex-col bg-gradient-to-b from-slate-900 to-slate-950 text-slate-100">
      <div style={{ height: 4, background: "linear-gradient(90deg,#0D9488,#0F766E)" }} />
      <div className="h-5 bg-slate-950/80" />
      <div className="px-6 pt-4 text-center">
        <p className="font-display text-[1.4rem] font-extrabold">
          Vía<span className="text-teal-400">Vital</span>.ai
        </p>
        <p className="mt-1 text-xs text-slate-400">Rutas seguras, no solo rápidas.</p>
      </div>

      <form onSubmit={submit} className="flex flex-1 flex-col px-7 pt-8">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full"
          style={{ background: "linear-gradient(135deg,#0D9488,#2DD4BF)" }}>
          <span style={{ fontSize: "2rem" }}>🛴</span>
        </div>
        <h2 className="mt-4 text-center font-display text-[1.3rem] font-bold">Bienvenido</h2>
        <p className="text-center text-[0.82rem] text-slate-400">Ingresa a tu cuenta</p>

        <label className="mt-6 block text-xs font-medium text-slate-300">Usuario</label>
        <input
          value={user}
          onChange={(e) => setUser(e.target.value)}
          placeholder="Tu nombre"
          className="mt-1.5 w-full rounded-[10px] border px-4 py-3 text-sm text-white outline-none transition focus:border-teal-400"
          style={{ background: "rgba(255,255,255,0.06)", borderColor: "rgba(255,255,255,0.12)" }}
        />

        <label className="mt-4 block text-xs font-medium text-slate-300">Contraseña</label>
        <input
          type="password"
          value={pwd}
          onChange={(e) => setPwd(e.target.value)}
          placeholder="••••••••"
          className="mt-1.5 w-full rounded-[10px] border px-4 py-3 text-sm text-white outline-none transition focus:border-teal-400"
          style={{ background: "rgba(255,255,255,0.06)", borderColor: "rgba(255,255,255,0.12)" }}
        />

        <button
          type="submit"
          disabled={loading}
          className="mt-5 w-full rounded-[10px] py-3.5 font-display text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-70"
          style={{ background: "#0D9488" }}
        >
          {loading ? (
            <span className="inline-flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              Accediendo...
            </span>
          ) : (
            "Acceder →"
          )}
        </button>

        <div className="mt-3 flex justify-center">
          <span className="rounded-full bg-teal-500/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-teal-300">
            ● Demo mode activo
          </span>
        </div>

        <p className="mt-auto pb-6 pt-8 text-center text-xs text-slate-500">
          ¿Nuevo aquí? <span className="text-teal-400 hover:underline">Regístrate gratis</span>
        </p>
      </form>
    </div>
  );
}

/* ─────────────── SCREEN 1 — CHAT ─────────────── */
function ChatScreen({ active, onAdvance }: { active: boolean; onAdvance: () => void }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [typing, setTyping] = useState(false);
  const [showConsent, setShowConsent] = useState(false);
  const [progress, setProgress] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!active || startedRef.current) return;
    startedRef.current = true;
    const timers: number[] = [];
    timers.push(
      window.setTimeout(() => setTyping(true), 400),
      window.setTimeout(() => {
        setTyping(false);
        setMessages([
          {
            from: "bot",
            text: "🔒 Aviso de privacidad: Tu ubicación se anonimizará y se usará solo para calcular tu ruta segura. No guardamos tu nombre ni género. ¿Aceptas?",
            consent: true,
          },
        ]);
        setShowConsent(true);
      }, 1800),
    );
    return () => timers.forEach((t) => clearTimeout(t));
  }, [active]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, typing]);

  const accept = () => {
    setShowConsent(false);
    setMessages((m) => [
      ...m,
      { from: "user", text: "✅ Sí, acepto. Voy de Narvarte al Tec de Monterrey CCM en bici." },
    ]);
    setTimeout(() => setTyping(true), 600);
    setTimeout(() => {
      setTyping(false);
      setMessages((m) => [
        ...m,
        {
          from: "bot",
          text: "Perfecto, Alex 🙌 Analizando 2,115,800 registros de accidentes, ciclovías activas y zonas de riesgo para tu ruta...",
          progress: true,
        },
      ]);
      // animate progress bar
      const start = performance.now();
      const tick = (now: number) => {
        const p = Math.min((now - start) / 2000, 1);
        setProgress(p * 100);
        if (p < 1) requestAnimationFrame(tick);
        else {
          setTimeout(() => setTyping(true), 300);
          setTimeout(() => {
            setTyping(false);
            setMessages((m) => [
              ...m,
              {
                from: "bot",
                text: "✅ ¡Ruta Segura encontrada! Evitando Tlalpan (zona de alto riesgo vehicular). Tu ruta usa ciclovías verificadas — 34% menos riesgo que la ruta directa.",
              },
              { from: "bot", iframe: "/ruta_segurav2.html" },
            ]);
            setTimeout(() => setTyping(true), 1400);
            setTimeout(() => {
              setTyping(false);
              setMessages((m) => [
                ...m,
                { from: "bot", text: "🛰️ Evaluando mapa de riesgos de la zona..." },
                { from: "bot", iframe: "/mapa_riesgo.html" },
              ]);
              setTimeout(onAdvance, 3200);
            }, 2400);
          }, 1500);
        }
      };
      requestAnimationFrame(tick);
    }, 2600);
  };

  return (
    <div className="flex h-full w-full flex-col bg-gradient-to-b from-slate-900 to-slate-950">
      <div style={{ height: 4, background: "linear-gradient(90deg,#0D9488,#2DD4BF)" }} />
      <div className="h-5" />
      <div className="flex items-center gap-3 border-b border-slate-800/80 px-4 py-3">
        <ArrowLeft className="h-4 w-4 text-slate-400" />
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-teal-600 font-display text-sm font-extrabold text-white">V</div>
        <div>
          <p className="text-sm font-semibold text-white">VíaVital.ai</p>
          <p className="text-[10px] text-green-400">● en línea</p>
        </div>
      </div>

      <div ref={scrollRef} className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
        {messages.map((m, i) => {
          if (m.iframe) {
            const isRisk = m.iframe.includes("riesgo");
            const label = isRisk ? "Mapa de Riesgo de la Zona" : "Ruta Segura Calculada";
            const desc = isRisk
              ? "Visualización interactiva de zonas de alto riesgo"
              : "Abre tu ruta optimizada en pantalla completa";
            const emoji = isRisk ? "🛰️" : "🗺️";
            return (
              <a
                key={i}
                href={m.iframe}
                target="_blank"
                rel="noopener noreferrer"
                className="w-[92%] animate-[fade-up_0.35s_ease-out_both] overflow-hidden rounded-xl border border-teal-500/30 bg-slate-800/70 p-3 transition hover:border-teal-400 hover:bg-slate-800"
                style={{ alignSelf: m.from === "bot" ? "flex-start" : "flex-end", textDecoration: "none" }}
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-teal-500/15 text-xl">
                    {emoji}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-white">{label}</p>
                    <p className="truncate text-[11px] text-slate-400">{desc}</p>
                  </div>
                  <span className="rounded-full bg-teal-500 px-3 py-1 text-[10px] font-bold text-white">
                    Abrir ↗
                  </span>
                </div>
              </a>
            );
          }
          return (
            <div
              key={i}
              className="max-w-[85%] text-sm leading-relaxed animate-[fade-up_0.35s_ease-out_both]"
              style={{
                alignSelf: m.from === "bot" ? "flex-start" : "flex-end",
                background: m.from === "bot" ? "#1E3A5F" : "#0D9488",
                color: m.from === "bot" ? "#CBD5E1" : "#fff",
                borderRadius: m.from === "bot" ? "16px 16px 16px 4px" : "16px 16px 4px 16px",
                padding: "10px 14px",
              }}
            >
              <div>{m.text}</div>
              {m.consent && showConsent && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    onClick={accept}
                    className="rounded-full bg-teal-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-400"
                  >
                    ✅ Sí, acepto
                  </button>
                  <button
                    onClick={accept}
                    className="rounded-full border border-slate-600 bg-slate-800/60 px-3 py-1.5 text-xs font-medium text-slate-300 hover:border-teal-400"
                  >
                    ❌ No por ahora
                  </button>
                </div>
              )}
              {m.progress && (
                <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-teal-400" style={{ width: `${progress}%`, transition: "width 0.1s linear" }} />
                </div>
              )}
            </div>
          );
        })}
        {typing && (
          <div
            className="flex max-w-[85%] gap-1 self-start rounded-2xl px-4 py-3"
            style={{ background: "#1E3A5F", borderRadius: "16px 16px 16px 4px" }}
          >
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-1.5 w-1.5 rounded-full bg-slate-400"
                style={{ animation: `bounce 1.2s ${i * 0.15}s infinite ease-in-out` }}
              />
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-slate-800/80 p-3">
        <div className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800/60 px-3 py-1.5">
          <input
            placeholder="Escribe un mensaje..."
            className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
          />
          <button className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-600 text-white hover:bg-teal-500">
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>

      <style>{`@keyframes bounce { 0%,80%,100% { transform: translateY(0); opacity:.5 } 40% { transform: translateY(-4px); opacity:1 } }`}</style>
    </div>
  );
}

/* ─────────────── SCREEN 2 — MAP ─────────────── */
function MapScreen({ active, onAdvance }: { active: boolean; onAdvance: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!active || !containerRef.current || mapRef.current) return;
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [-99.1670, 19.4200],
      zoom: 12.5,
      attributionControl: false,
    });
    mapRef.current = map;

    const ROUTE: [number, number][] = [
      [-99.168, 19.409],
      [-99.171, 19.400],
      [-99.173, 19.390],
      [-99.175, 19.380],
      [-99.177, 19.371],
    ];

    map.on("load", () => {
      const fullGeo: GeoJSON.Feature<GeoJSON.LineString> = {
        type: "Feature",
        properties: {},
        geometry: { type: "LineString", coordinates: ROUTE },
      };
      map.addSource("route", { type: "geojson", data: fullGeo });
      map.addLayer({
        id: "route-glow",
        type: "line",
        source: "route",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#2DD4BF", "line-width": 12, "line-opacity": 0.25, "line-blur": 6 },
      });
      map.addLayer({
        id: "route-line",
        type: "line",
        source: "route",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#2DD4BF", "line-width": 4, "line-dasharray": [0.1, 2] },
      });

      // animate dasharray to draw the line
      let i = 0;
      const dashSteps: [number, number][] = [
        [0, 4], [0.5, 4], [1, 4], [1.5, 4], [2, 4], [2.5, 4], [3, 4], [3.5, 4], [4, 4], [4, 0],
      ];
      const interval = window.setInterval(() => {
        i = (i + 1) % dashSteps.length;
        if (map.getLayer("route-line")) {
          map.setPaintProperty("route-line", "line-dasharray", dashSteps[i]);
        }
        if (i === dashSteps.length - 1) clearInterval(interval);
      }, 80);

      // markers
      const a = document.createElement("div");
      a.style.cssText = "width:18px;height:18px;border-radius:50%;background:#2DD4BF;border:3px solid #0F172A;box-shadow:0 0 0 4px rgba(45,212,191,0.35)";
      new mapboxgl.Marker(a).setLngLat(ROUTE[0]).setPopup(new mapboxgl.Popup({ offset: 18 }).setText("📍 Narvarte")).addTo(map);
      const b = document.createElement("div");
      b.style.cssText = "width:18px;height:18px;border-radius:50%;background:#fff;border:3px solid #2DD4BF;box-shadow:0 0 0 4px rgba(45,212,191,0.35)";
      new mapboxgl.Marker(b).setLngLat(ROUTE[ROUTE.length - 1]).setPopup(new mapboxgl.Popup({ offset: 18 }).setText("🏫 Tec CCM")).addTo(map);

      // checkpoints
      ROUTE.slice(1, -1).forEach((c) => {
        const el = document.createElement("div");
        el.style.cssText = "width:10px;height:10px;border-radius:50%;background:#2DD4BF;border:2px solid #0F172A";
        new mapboxgl.Marker(el).setLngLat(c).addTo(map);
      });

      // pulsing dot
      const pulse = document.createElement("div");
      pulse.style.cssText = "width:14px;height:14px;border-radius:50%;background:#fff;box-shadow:0 0 12px 4px rgba(45,212,191,0.7);animation:pulseDot 1.4s ease-out infinite";
      const pulseMarker = new mapboxgl.Marker(pulse).setLngLat(ROUTE[0]).addTo(map);
      let t = 0;
      const moveInterval = window.setInterval(() => {
        t = (t + 0.01) % 1;
        const idx = Math.floor(t * (ROUTE.length - 1));
        const next = Math.min(idx + 1, ROUTE.length - 1);
        const f = t * (ROUTE.length - 1) - idx;
        const lng = ROUTE[idx][0] + (ROUTE[next][0] - ROUTE[idx][0]) * f;
        const lat = ROUTE[idx][1] + (ROUTE[next][1] - ROUTE[idx][1]) * f;
        pulseMarker.setLngLat([lng, lat]);
      }, 40);

      map.once("remove", () => {
        clearInterval(interval);
        clearInterval(moveInterval);
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [active]);

  return (
    <div className="relative flex h-full w-full flex-col bg-slate-950">
      <div style={{ height: 4, background: "linear-gradient(90deg,#0D9488,#2DD4BF)" }} />
      <div className="flex items-center justify-between border-b border-slate-800/80 bg-slate-900/80 px-4 py-2.5 pt-7 backdrop-blur">
        <p className="font-display text-sm font-bold text-white">VíaVital.ai</p>
        <p className="text-[10px] text-teal-300">Narvarte → Tec CCM</p>
      </div>
      <div ref={containerRef} className="flex-1" />
      <div className="absolute inset-x-3 bottom-3 rounded-2xl border border-slate-700/60 bg-slate-900/85 p-4 backdrop-blur-md">
        <p className="font-display text-sm font-bold text-white">
          🛴 Ruta Vital · 4.2 km · ~18 min · <span className="text-teal-400">↓34% riesgo</span>
        </p>
        <p className="mt-1 text-[11px] text-teal-300">Evitando: Tlalpan, Eje 5 Sur</p>
        <a
          href="/ruta_segurav2.html"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 block w-full rounded-xl border border-teal-400/60 bg-teal-500/10 py-2.5 text-center text-sm font-semibold text-teal-200 transition hover:bg-teal-500/20"
        >
          🗺️ Abrir mapa real (motor de riesgo) ↗
        </a>
        <button
          onClick={onAdvance}
          className="mt-2 w-full rounded-xl bg-teal-600 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-500"
        >
          Unirme al Mobility Pool →
        </button>
      </div>
      <style>{`@keyframes pulseDot { 0% { transform: scale(1); opacity:1 } 70% { transform: scale(1.8); opacity:0 } 100% { transform: scale(1); opacity:0 } }`}</style>
    </div>
  );
}

/* ─────────────── SCREEN 3 — POOL ─────────────── */
function PoolScreen({ onAdvance }: { onAdvance: () => void }) {
  const [count, setCount] = useState(3);
  const [gender, setGender] = useState<"none" | "women" | "mixed">("none");
  const [loading, setLoading] = useState(false);

  const submit = () => {
    setLoading(true);
    setTimeout(onAdvance, 1500);
  };

  const genderBtn = (val: typeof gender, label: string) => (
    <button
      onClick={() => setGender(val)}
      className="rounded-full border px-3 py-1.5 text-xs font-medium transition"
      style={
        gender === val
          ? { background: "#0D9488", borderColor: "#0D9488", color: "#fff" }
          : { borderColor: "rgba(13,148,136,0.5)", color: "#94A3B8", background: "transparent" }
      }
    >
      {label}
    </button>
  );

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto bg-gradient-to-b from-slate-900 to-slate-950 text-slate-100">
      <div style={{ height: 4, background: "linear-gradient(90deg,#0D9488,#2DD4BF)" }} />
      <div className="h-5" />
      <div className="px-6 pt-4">
        <h2 className="font-display text-xl font-bold">🤝 Mobility Pool</h2>
        <p className="mt-1 text-xs text-slate-400">Viaja en grupo por la misma ruta segura</p>

        {/* Group size */}
        <div className="mt-6">
          <p className="text-xs font-medium text-slate-300">Integrantes mínimos</p>
          <div className="mt-2 flex items-center justify-center gap-4 rounded-xl border border-teal-500/30 bg-slate-800/40 py-3">
            <button
              onClick={() => setCount((c) => Math.max(3, c - 1))}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-teal-500/40 text-teal-300 hover:bg-teal-500/10"
            >
              <Minus className="h-4 w-4" />
            </button>
            <span className="font-display text-2xl font-extrabold text-white" style={{ minWidth: 32, textAlign: "center" }}>{count}</span>
            <button
              onClick={() => setCount((c) => Math.min(8, c + 1))}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-teal-500/40 text-teal-300 hover:bg-teal-500/10"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1.5 text-center text-[10px] text-slate-500">Mínimo 3 personas para activar el Pool</p>
        </div>

        {/* Gender */}
        <div className="mt-5">
          <p className="text-xs font-medium text-slate-300">Preferencia de género (opcional)</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {genderBtn("none", "Sin preferencia")}
            {genderBtn("women", "Solo mujeres")}
            {genderBtn("mixed", "Mixto")}
          </div>
          <p className="mt-2 text-[10px] italic text-slate-500">Esta selección es anónima y respeta la LFPDPPP</p>
        </div>

        {/* Meeting point */}
        <div className="mt-5">
          <p className="text-xs font-medium text-slate-300">Nodo de encuentro</p>
          <div
            className="mt-2 flex items-center justify-center rounded-xl border border-slate-700/60"
            style={{
              height: 120,
              background:
                "radial-gradient(circle at 50% 50%, rgba(13,148,136,0.18), transparent 60%), #0D1B2A",
            }}
          >
            <span style={{ fontSize: "2rem" }}>📍</span>
          </div>
          <p className="mt-2 text-sm font-semibold text-white">📍 Parque México, Col. Condesa</p>
          <p className="text-[11px] text-slate-500">A 1.2 km de tu origen · Punto verificado</p>
        </div>

        <button
          onClick={submit}
          disabled={loading}
          className="my-6 w-full rounded-xl bg-teal-600 py-3 font-display text-sm font-semibold text-white transition hover:bg-teal-500 disabled:opacity-70"
        >
          {loading ? (
            <span className="inline-flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              Buscando compañeros...
            </span>
          ) : (
            "Confirmar y Buscar Pool →"
          )}
        </button>
      </div>
    </div>
  );
}

/* ─────────────── SCREEN 4 — RATING ─────────────── */
function RatingScreen({ active, onHome }: { active: boolean; onHome: () => void }) {
  const [fill, setFill] = useState(0); // 0..5 (with 4.5 step)
  const [count, setCount] = useState(847);
  const [progress, setProgress] = useState(0);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!active || startedRef.current) return;
    startedRef.current = true;
    const timers = [
      setTimeout(() => setFill(1), 600),
      setTimeout(() => setFill(2), 1200),
      setTimeout(() => setFill(3), 1800),
      setTimeout(() => setFill(4), 2400),
      setTimeout(() => setFill(4.5), 2800),
    ];
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - start) / 3000, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setCount(Math.floor(847 + (1203 - 847) * eased));
      setProgress(eased * 90);
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    return () => timers.forEach((t) => clearTimeout(t));
  }, [active]);

  const renderStar = (i: number) => {
    const filled = fill >= i;
    const half = !filled && fill >= i - 0.5;
    return (
      <button
        key={i}
        onClick={() => setFill(i)}
        className="relative"
        style={{ fontSize: "2.2rem", lineHeight: 1, transition: "transform 0.25s ease", transform: filled ? "scale(1)" : "scale(1)" }}
      >
        <span style={{ color: "#334155" }}>★</span>
        {(filled || half) && (
          <span
            className="absolute inset-0"
            style={{
              color: "#FBBF24",
              overflow: "hidden",
              width: half ? "50%" : "100%",
              animation: "pop 0.3s ease",
            }}
          >
            ★
          </span>
        )}
      </button>
    );
  };

  return (
    <div className="flex h-full w-full flex-col bg-gradient-to-b from-slate-900 to-slate-950 text-slate-100">
      <div style={{ height: 4, background: "linear-gradient(90deg,#0D9488,#2DD4BF)" }} />
      <div className="h-5" />
      <div className="flex flex-1 flex-col px-6 pt-6 text-center">
        <h2 className="font-display text-[1.3rem] font-bold">✅ ¡Llegaste seguro!</h2>
        <p className="mt-1 text-xs text-slate-400">Tec de Monterrey CCM · Ruta completada</p>

        <p className="mt-8 text-sm text-white">¿Qué calificación le das a esta ruta?</p>

        <div className="mt-5 flex items-center justify-center gap-2">
          {[1, 2, 3, 4, 5].map(renderStar)}
        </div>

        <p className="mt-4 font-display text-[1.1rem] font-bold text-teal-400">
          {fill.toFixed(1).replace(".0", "")} / 5 estrellas
        </p>

        <p className="mt-6 text-xs text-slate-400">
          Basado en {count.toLocaleString("en-US")} calificaciones
        </p>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
          <div className="h-full rounded-full bg-teal-400" style={{ width: `${progress}%`, transition: "width 0.1s linear" }} />
        </div>

        <div className="mt-auto pb-6">
          <button
            onClick={onHome}
            className="w-full rounded-xl border border-slate-600 bg-transparent py-3 text-sm font-semibold text-slate-200 transition hover:border-teal-400 hover:text-teal-300"
          >
            🏠 Volver al inicio
          </button>
          <p className="mt-3 text-[11px] text-teal-400">VíaVital.ai · Porque llegar es la meta</p>
        </div>
      </div>
      <style>{`@keyframes pop { 0% { transform: scale(0.6); } 50% { transform: scale(1.3); } 100% { transform: scale(1); } }`}</style>
    </div>
  );
}
