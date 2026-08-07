import { useEffect } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { queryClient, useHealth, usePersonas } from "./api/hooks";
import { crossCheckEngine } from "./state/appHealth";
import { useScenarioStore } from "./state/scenarioStore";
import { ApiDownScreen } from "./components/ApiDownScreen";
import { LeverRail } from "./components/LeverRail";
import { ThemeToggle } from "./components/ThemeToggle";
import { Warnings } from "./components/Warnings";
import { SHIPPED_IDS } from "./personas/registry";
import Inicio from "./routes/Inicio";
import Laboratorio from "./routes/Laboratorio";
import Metodologia from "./routes/Metodologia";
import Persona from "./routes/Persona";

function Shell() {
  const health = useHealth();
  const personas = usePersonas();
  const hotIds = useScenarioStore((s) => s.hotIds);
  useEffect(() => {
    if (health.isSuccess) void crossCheckEngine();
  }, [health.isSuccess]);

  if (health.isPending) return <div className="blocking"><div className="card"><h4>Cargando…</h4></div></div>;
  if (health.isError) return <ApiDownScreen error={health.error} />;

  const cards = (personas.data?.personas ?? []).filter((c) => SHIPPED_IDS.includes(c.id));
  return (
    <div className="shell">
      <header className="topbar">
        <strong>España en escenarios</strong>
        <nav>
          <NavLink to="/" end>Inicio</NavLink>
          {cards.map((c) => (
            <NavLink key={c.id} to={`/persona/${c.id}`}>{c.pill}</NavLink>
          ))}
          <NavLink to="/laboratorio">Laboratorio</NavLink>
          <NavLink to="/metodologia">Datos y método</NavLink>
        </nav>
        <span style={{ marginLeft: "auto" }} className="badge-fwd">vintage {health.data.vintage}</span>
        <ThemeToggle />
      </header>
      <div className="body">
        <LeverRail hotIds={hotIds} />
        <main className="main">
          <Warnings />
          <Routes>
            <Route path="/" element={<Inicio />} />
            <Route path="/persona/:id" element={<Persona />} />
            <Route path="/laboratorio" element={<Laboratorio />} />
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
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
