import { useEffect, useRef, useState } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, NavLink, Outlet, Route, Routes } from "react-router-dom";
import { queryClient, useHealth, usePersonas } from "./api/hooks";
import { API_BASE } from "./api/client";
import { crossCheckEngine } from "./state/appHealth";
import { useScenarioStore } from "./state/scenarioStore";
import { ApiDownScreen } from "./components/ApiDownScreen";
import { Explainer } from "./components/Explainer";
import { LeverRail } from "./components/LeverRail";
import { ThemeToggle } from "./components/ThemeToggle";
import { Warnings } from "./components/Warnings";
import { SHIPPED_IDS } from "./personas/registry";
import Biblioteca from "./routes/Biblioteca";
import Consulta from "./routes/Consulta";
import ComoFunciona from "./routes/ComoFunciona";
import Evidencia from "./routes/Evidencia";
import Prediccion from "./routes/Prediccion";
import Inicio from "./routes/Inicio";
import Laboratorio from "./routes/Laboratorio";
import Metodologia from "./routes/Metodologia";
import Persona from "./routes/Persona";

/** Layout for the scenario routes: the page, then the explanation of it. */
function WithExplainer() {
  return (
    <div className="withexp">
      <Outlet />
      <Explainer />
    </div>
  );
}

function Shell() {
  const health = useHealth();
  const personas = usePersonas();
  const hotIds = useScenarioStore((s) => s.hotIds);
  const [railOpen, setRailOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.matchMedia?.("(max-width: 1024px)").matches ?? false);
  const railToggle = useRef<HTMLButtonElement>(null);
  const closeRail = () => { setRailOpen(false); railToggle.current?.focus(); };
  useEffect(() => {
    const media = window.matchMedia?.("(max-width: 1024px)");
    if (!media) return;
    const update = () => { setIsMobile(media.matches); setRailOpen(false); };
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    if (!railOpen || !isMobile) return;
    const rail = document.getElementById("scenario-levers");
    const focusable = () => Array.from(rail?.querySelectorAll<HTMLElement>("button:not(:disabled), input, select, a[href]") ?? []);
    focusable()[0]?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault(); setRailOpen(false); railToggle.current?.focus();
      } else if (event.key === "Tab") {
        const items = focusable();
        const first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener("keydown", keydown);
    return () => document.removeEventListener("keydown", keydown);
  }, [railOpen, isMobile]);
  useEffect(() => {
    if (health.isSuccess) void crossCheckEngine();
  }, [health.isSuccess]);

  if (health.isPending) {
    return (
      <div className="blocking">
        <div className="card">
          <h4>Despertando el servidor…</h4>
          <p style={{ fontSize: 13.5, color: "var(--ink-2)" }}>
            La API duerme cuando nadie la usa (alojamiento gratuito) y tarda
            hasta un minuto en arrancar. Esta pantalla reintenta sola.
          </p>
          <p style={{ fontSize: 12, color: "var(--muted)" }}>
            Conectando con <code>{API_BASE}</code>
          </p>
        </div>
      </div>
    );
  }
  if (health.isError) return <ApiDownScreen error={health.error} />;

  const cards = (personas.data?.personas ?? []).filter((c) => SHIPPED_IDS.includes(c.id));
  return (
    <div className="shell">
      <header className="topbar">
        <strong>España en escenarios</strong>
        <button type="button" className="rail-toggle" ref={railToggle}
          aria-label="Abrir palancas" aria-controls="scenario-levers" aria-expanded={railOpen}
          onClick={() => setRailOpen(true)}>☰ Palancas</button>
        <nav>
          <NavLink to="/" end>Inicio</NavLink>
          {cards.map((c) => (
            <NavLink key={c.id} to={`/persona/${c.id}`}>{c.pill}</NavLink>
          ))}
          <NavLink to="/laboratorio">Laboratorio</NavLink>
          <NavLink to="/biblioteca">Biblioteca</NavLink>
          <NavLink to="/consulta">Consulta</NavLink>
          <NavLink to="/evidencia">Evidencia</NavLink>
          <NavLink to="/prediccion">Predicción</NavLink>
          <NavLink to="/como-funciona">Cómo funciona</NavLink>
          <NavLink to="/metodologia">Datos y método</NavLink>
        </nav>
        <span style={{ marginLeft: "auto" }} className="badge-fwd">vintage {health.data.vintage}</span>
        <ThemeToggle />
      </header>
      <div className="body">
        {isMobile && railOpen && <button className="rail-backdrop" aria-label="Cerrar panel de palancas" tabIndex={-1} onClick={closeRail} />}
        <LeverRail hotIds={hotIds} mobile={isMobile} open={railOpen} onClose={closeRail} />
        <main className="main">
          <Warnings />
          <Routes>
            {/* Scenario routes carry the live explainer; the two reference
                pages don't — there is no scenario on them to explain, and a
                panel narrating levers the reader can't see would be noise. */}
            <Route element={<WithExplainer />}>
              <Route path="/" element={<Inicio />} />
              <Route path="/persona/:id" element={<Persona />} />
              <Route path="/laboratorio" element={<Laboratorio />} />
            </Route>
            <Route path="/biblioteca" element={<Biblioteca />} />
            <Route path="/consulta" element={<Consulta />} />
            <Route path="/evidencia" element={<Evidencia />} />
            <Route path="/prediccion" element={<Prediccion />} />
            <Route path="/como-funciona" element={<ComoFunciona />} />
            <Route path="/metodologia" element={<Metodologia />} />
          </Routes>
        </main>
      </div>
      <footer className="foot">
        {health.data.computed_not_advice && (
          <span>Proyección condicional, no recomendación de compra, venta o voto.</span>
        )}
        <span>Motor v{health.data.engine_version} · vintage {health.data.vintage}</span>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={import.meta.env.BASE_URL}>
        <Shell />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
