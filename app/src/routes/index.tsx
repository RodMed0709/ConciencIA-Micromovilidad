import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  MessageCircle, BrainCircuit, Route as RouteIcon,
  Lock, BarChart3, Users, Venus, ShieldCheck, Eye, Scale,
  ArrowRight,
} from "lucide-react";
import { ProblemStats } from "@/components/ProblemStats";
import { DemoModal } from "@/components/DemoModal";

export const Route = createFileRoute("/")({
  component: Landing,
});

// (demo content moved to <DemoModal />)

function Landing() {
  const [demoOpen, setDemoOpen] = useState(false);

  return (
    <div className="min-h-screen text-slate-100 selection:bg-teal-500/40">
      {/* NAV */}
      <header className="sticky top-0 z-50 border-b border-slate-400/10 bg-slate-950/60 backdrop-blur-md">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <a href="#" className="font-display text-xl font-extrabold tracking-tight">
            Vía<span className="text-teal-500">Vital</span>.ai
          </a>
          <ul className="hidden gap-8 text-sm text-slate-300 md:flex">
            <li><a href="#problema" className="transition hover:text-teal-400">Problema</a></li>
            <li><a href="#arquitectura" className="transition hover:text-teal-400">Arquitectura</a></li>
            <li><a href="#demo" className="transition hover:text-teal-400">Demo</a></li>
            <li><a href="#cumplimiento" className="transition hover:text-teal-400">Cumplimiento</a></li>
          </ul>
          <a href="#demo" className="rounded-full bg-teal-600 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-teal-600/30 transition hover:scale-105 hover:bg-teal-500">
            Ver Demo
          </a>
        </nav>
      </header>

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 hero-grid opacity-60" />
        <div className="absolute inset-0 hero-glow" />
        <div className="relative mx-auto max-w-7xl px-6 pt-24 pb-32 text-center">
          <div className="mx-auto inline-flex items-center gap-3 rounded-full border border-teal-500/30 bg-slate-800/60 px-4 py-2 text-xs font-medium text-slate-200 backdrop-blur-md animate-[fade-in_0.6s_ease-out_both]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            🏆 Hackathon Concienc.IA 2026 · Tec de Monterrey
          </div>

          <h1 className="mx-auto mt-8 max-w-4xl font-display text-5xl font-extrabold leading-[1.05] tracking-tight md:text-6xl animate-[fade-up_0.8s_ease-out_both]">
            Rutas <span className="text-teal-400">seguras</span>,<br />
            no solo rápidas.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-300 animate-[fade-up_1s_ease-out_both]">
            El primer agente de IA que prioriza tu seguridad personal y vial en trayectos universitarios.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4 animate-[fade-up_1.1s_ease-out_both]">
            <a href="#demo" className="group inline-flex items-center gap-2 rounded-full bg-teal-600 px-7 py-3.5 text-sm font-semibold text-white shadow-xl shadow-teal-600/40 transition-all hover:scale-105 hover:bg-teal-500">
              🛴 Probar Demo
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
            </a>
            <a href="#arquitectura" className="rounded-full border border-slate-400/30 bg-slate-800/40 px-7 py-3.5 text-sm font-semibold text-slate-100 backdrop-blur-md transition hover:border-teal-400/50 hover:bg-slate-800/70">
              Conoce la Arquitectura
            </a>
          </div>
        </div>
      </section>

      {/* PROBLEM */}
      <section id="problema" className="relative px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-3xl text-center">
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-400">El problema</span>
            <h2 className="mt-4 font-display text-3xl font-extrabold md:text-4xl">
              La ciudad ignoró a la micromovilidad
            </h2>
            <p className="mt-4 text-slate-400">
              Cada día, miles de estudiantes en CDMX se mueven en bici o scooter por rutas diseñadas para autos. Las apps de navegación no contemplan su realidad.
            </p>
          </div>

          <div className="mt-14 grid gap-5 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            <ProblemCard emoji="⚡" title="Apps Optimizan Velocidad, No Vida"
              body="Google Maps y Waze te envían por Eje Central o Tlalpan. Para un auto es eficiente. Para un scooter, es un cruce mortal con vehículos a 70 km/h." />
            <ProblemCard emoji="👩" title="Sesgo de Género en el Diseño"
              body="Mujeres y personas no binarias enfrentan riesgos adicionales en rutas no consideradas como 'inseguras' por los algoritmos actuales." />
            <ProblemCard emoji="🏫" title="Zonas Universitarias Desprotegidas"
              body="El 31% de usuarios de micromovilidad en CDMX son estudiantes universitarios. La brecha entre movilidad y seguridad es mayor en estos entornos." />
          </div>

          <ProblemStats />

        </div>
      </section>

      {/* ARCHITECTURE */}
      <section id="arquitectura" className="relative bg-slate-950/40 px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-3xl text-center">
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-400">Arquitectura</span>
            <h2 className="mt-4 font-display text-3xl font-extrabold md:text-4xl">
              ¿Cómo funciona el motor de VíaVital?
            </h2>
            <p className="mt-4 text-slate-400">
              Tres capas que convierten datos abiertos en decisiones de seguridad personal en tiempo real.
            </p>
          </div>

          <div className="mt-16 grid items-stretch gap-6 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
            <ArchColumn step="01" label="Input" icon={<MessageCircle className="h-6 w-6" />}
              title="Interacción Natural"
              body="Conversación directa con el Agente de IA VíaVital.ai dentro de la app. Sin instalaciones externas, sin formularios: cero fricción para el estudiante."
              tags={["Interfaz Nativa VíaVital", "NLU es-MX"]} />
            <Arrow />
            <ArchColumn step="02" label="Cerebro IA" icon={<BrainCircuit className="h-6 w-6" />}
              title="Análisis Predictivo"
              body="Modelo Python que cruza 47K incidentes históricos en CDMX con datos de iluminación, flujo vial y reportes ciudadanos."
              tags={["Python", "Datos Abiertos CDMX", "47K incidentes"]} />
            <Arrow />
            <ArchColumn step="03" label="Output" icon={<RouteIcon className="h-6 w-6" />}
              title="Ruta Segura & Carpooling"
              body="Genera un trayecto óptimo y conecta de forma anónima con otros estudiantes verificados para crear caravanas seguras."
              tags={["Ruta Segura", "Mobility-Pool"]} />
          </div>
        </div>
      </section>

      {/* DEMO */}
      <section id="demo" className="relative px-6 py-24">
        <div className="mx-auto grid max-w-7xl items-center gap-16 lg:grid-cols-2">
          {/* Launcher */}
          <div className="flex flex-col items-center justify-center text-center">
            <div className="relative w-full max-w-md rounded-3xl border border-teal-500/20 bg-slate-800/50 p-10 backdrop-blur-md">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-teal-500/15 text-4xl">
                📱
              </div>
              <p className="mt-6 font-display text-xl font-extrabold text-white">
                Experiencia interactiva completa
              </p>
              <p className="mt-2 text-sm text-slate-400">
                5 pantallas reales: login, chat IA, mapa animado, mobility pool y rating.
              </p>
              <button
                onClick={() => setDemoOpen(true)}
                className="mt-7 inline-flex items-center justify-center rounded-[14px] bg-teal-600 font-display font-bold text-white shadow-xl shadow-teal-900/40 transition hover:scale-[1.02] hover:bg-teal-500"
                style={{ padding: "18px 48px", fontSize: "1.1rem", fontWeight: 700 }}
              >
                📱 Abrir Demo Completo
              </button>
            </div>
          </div>

          {/* Features */}
          <div>
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-400">Demo interactivo</span>
            <h2 className="mt-4 font-display text-3xl font-extrabold md:text-4xl">
              Una conversación. Una ruta más segura.
            </h2>
            <p className="mt-4 text-slate-400">
              Así se siente pedirle ayuda a VíaVital cuando vas saliendo de clase. Sin apps, sin formularios, sin entregar tu identidad.
            </p>
            <ul className="mt-8 space-y-4">
              <Feature icon={<Lock className="h-5 w-5" />} title="🔒 Privacidad por Diseño"
                body="100% compatible con la LFPDPPP. No almacenamos identidad ni género." />
              <Feature icon={<BarChart3 className="h-5 w-5" />} title="📊 Datos Abiertos CDMX"
                body="Integración directa con portales oficiales de incidentes y movilidad." />
              <Feature icon={<Users className="h-5 w-5" />} title="🤝 Mobility-pool Anónimo"
                body="Conexión opcional con estudiantes verificados para trayectos en caravana." />
              <Feature icon={<Venus className="h-5 w-5" />} title="♀ Perspectiva de Género"
                body="Algoritmo entrenado para mitigar sesgos en el cálculo de seguridad." />
            </ul>
          </div>
        </div>
      </section>

      {/* COMPLIANCE */}
      <section id="cumplimiento" className="relative bg-slate-950/40 px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-3xl text-center">
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-400">Rúbrica</span>
            <h2 className="mt-4 font-display text-3xl font-extrabold md:text-4xl">
              Cumplimiento Estricto del Reto
            </h2>
            <p className="mt-4 text-slate-400">
              Cada decisión técnica está mapeada a los criterios de evaluación de Concienc.IA 2026.
            </p>
          </div>

          <div className="mt-14 grid gap-6 md:grid-cols-3">
            <ComplianceCard icon={<ShieldCheck className="h-6 w-6" />} label="Técnico" title="Ingeniería verificable"
              items={["Modelo Python de scoring de rutas", "APIs de Datos Abiertos CDMX", "Supervisión humana en el loop"]} />
            <ComplianceCard icon={<Eye className="h-6 w-6" />} label="Privacidad" title="LFPDPPP compliant"
              items={["Minimización de datos por defecto", "Cifrado extremo a extremo", "Derechos ARCO accesibles en la UI"]} />
            <ComplianceCard icon={<Scale className="h-6 w-6" />} label="Ético & Género" title="Diseño con conciencia"
              items={["Beneficencia como principio rector", "Prevención de violencia sociodigital", "Diseño centrado en la usuaria"]} />
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-slate-400/10 px-6 py-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 text-center md:flex-row md:text-left">
          <div>
            <p className="font-display text-lg font-extrabold">
              Vía<span className="text-teal-500">Vital</span>.ai
            </p>
            <p className="text-sm text-slate-400">Hackeemos la ciudad.</p>
          </div>
          <p className="text-xs text-slate-500">
            © 2026 VíaVital.ai · Hackathon Concienc.IA · Tec de Monterrey
          </p>
        </div>
      </footer>

      <DemoModal open={demoOpen} onClose={() => setDemoOpen(false)} />
    </div>
  );
}

function ProblemCard({ emoji, title, body }: { emoji: string; title: string; body: string }) {
  return (
    <div className="group rounded-2xl border border-slate-400/20 bg-slate-800/65 backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-teal-400/40 hover:shadow-xl hover:shadow-teal-900/20" style={{ padding: 26 }}>
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-500/10 text-2xl transition group-hover:bg-teal-500/20">
        {emoji}
      </div>
      <h3 className="mt-5 font-display text-xl font-extrabold">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-400">{body}</p>
    </div>
  );
}

function ArchColumn({ step, label, icon, title, body, tags }: {
  step: string; label: string; icon: React.ReactNode; title: string; body: string; tags: string[];
}) {
  return (
    <div className="group flex h-full flex-col rounded-2xl border border-slate-400/20 bg-slate-800/65 p-7 backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-teal-400/40">
      <div className="flex items-center justify-between">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">{icon}</div>
        <div className="text-right">
          <p className="font-display text-3xl font-extrabold text-slate-700">{step}</p>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-teal-400">{label}</p>
        </div>
      </div>
      <h3 className="mt-6 font-display text-xl font-extrabold">{title}</h3>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-400">{body}</p>
      <div className="mt-5 flex flex-wrap gap-2">
        {tags.map((t) => (
          <span key={t} className="rounded-full border border-teal-500/30 bg-teal-500/10 px-3 py-1 text-[11px] font-medium text-teal-300">
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

function Arrow() {
  return (
    <div className="hidden items-center justify-center md:flex">
      <ArrowRight className="h-6 w-6 text-teal-500/60" />
    </div>
  );
}

function Feature({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) {
  return (
    <li className="flex gap-4 rounded-2xl border border-slate-400/15 bg-slate-800/45 p-5 backdrop-blur-md transition hover:-translate-y-0.5 hover:border-teal-400/40">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">{icon}</div>
      <div>
        <p className="font-semibold text-slate-100">{title}</p>
        <p className="mt-1 text-sm text-slate-400">{body}</p>
      </div>
    </li>
  );
}

function ComplianceCard({ icon, label, title, items }: {
  icon: React.ReactNode; label: string; title: string; items: string[];
}) {
  return (
    <div className="group rounded-2xl border border-slate-400/20 bg-slate-800/65 p-7 backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-teal-400/40">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">{icon}</div>
        <span className="rounded-full border border-teal-500/30 bg-teal-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-teal-300">
          {label}
        </span>
      </div>
      <h3 className="mt-5 font-display text-xl font-extrabold">{title}</h3>
      <ul className="mt-4 space-y-2.5">
        {items.map((i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-400" />
            {i}
          </li>
        ))}
      </ul>
    </div>
  );
}
