import { useEffect, useState } from "react";
import * as C from "../engine/constants";
import { LEVER_SPECS } from "../engine/levers";
import { nf } from "../lib/fmt";
import { useScenarioStore } from "../state/scenarioStore";
import { RESCUE_YIELD } from "./DebtVsGdpChart";
import { HowToRead } from "./HowToRead";

const R = LEVER_SPECS.find((s) => s.id === "r")!;
const PRIMA = LEVER_SPECS.find((s) => s.id === "prima")!;

/** The engine's own rule for the 10-year yield, as a calculator: Euríbor +
 *  term premium + risk premium / 100 (engine/spain.py, `bono`). Same
 *  formula, so what it shows is what the scenario would use. */
export function bondYield(euribor: number, primaPb: number): number {
  return euribor + C.TERM + primaPb / 100;
}

/** The risk premium, in basis points, that takes the yield to the red line
 *  at a given Euríbor. */
export function primaToRedLine(euribor: number): number {
  return (RESCUE_YIELD - euribor - C.TERM) * 100;
}

export function BondCalculator() {
  const levers = useScenarioStore((s) => s.levers);
  const setLever = useScenarioStore((s) => s.setLever);
  const [r, setR] = useState(levers.r);
  const [prima, setPrima] = useState(levers.prima);
  // Follow the levers when they move elsewhere (the side panel, «Aplicar»).
  useEffect(() => { setR(levers.r); setPrima(levers.prima); }, [levers.r, levers.prima]);

  const bono = bondYield(r, prima);
  const over = bono > RESCUE_YIELD;
  const need = primaToRedLine(r);
  const differs = r !== levers.r || prima !== levers.prima;

  return (
    <div className="card bond-calc">
      <h4>Calculadora del bono a 10 años <small>¿cuánto le costaría a España pedir prestado?</small></h4>
      <HowToRead>
        <p>
          El interés que paga España por pedir prestado a diez años es, en el
          modelo, la suma de tres cosas: el Euríbor, un extra de{" "}
          {nf(C.TERM, 2)} puntos por prestar a más plazo y la prima de riesgo, que
          se mide en puntos básicos (100 pb son 1 punto). Mueve las dos primeras y
          mira dónde cae frente a la línea roja del {nf(RESCUE_YIELD, 0)} %.
        </p>
      </HowToRead>

      <div className="bond-inputs">
        <label>
          <span>Euríbor a 12 meses: <b>{nf(r, 2)} %</b></span>
          <input type="range" aria-label="Euríbor a 12 meses" min={R.min} max={R.max} step={R.step}
            value={r} onChange={(e) => setR(Number(e.target.value))} />
        </label>
        <label>
          <span>Prima de riesgo: <b>{nf(prima, 0)} pb</b></span>
          <input type="range" aria-label="Prima de riesgo" min={PRIMA.min} max={PRIMA.max} step={PRIMA.step}
            value={prima} onChange={(e) => setPrima(Number(e.target.value))} />
        </label>
      </div>

      <p className="bond-result" aria-live="polite">
        {nf(r, 2)} % + {nf(C.TERM, 2)} + {nf(prima, 0)} pb ÷ 100 ={" "}
        <b className={over ? "bad" : ""}>{nf(bono, 2)} %</b>
      </p>

      {over ? (
        <p className="danger-note" role="alert">
          <span aria-hidden="true">⚠</span>{" "}
          {nf(bono, 2)} %: por encima de la línea roja del {nf(RESCUE_YIELD, 0)} %. Es
          la zona en la que Grecia, Portugal e Irlanda pidieron el rescate, y la que
          España tocó en 2012 con un 7,6 %. A ese precio, cada euro de deuda que se
          renueva sale mucho más caro y la bola de nieve se acelera.
        </p>
      ) : (
        <p className="muted" style={{ fontSize: 14, margin: "4px 0 0" }}>
          Le faltan {nf(RESCUE_YIELD - bono, 2)} puntos para el {nf(RESCUE_YIELD, 0)} %.{" "}
          {need <= PRIMA.max
            ? `Con el Euríbor en ${nf(r, 2)} %, la prima tendría que pasar de ${nf(need, 0)} pb para llegar a la línea roja.`
            : `Con el Euríbor en ${nf(r, 2)} %, ni con la prima al máximo del panel (${nf(PRIMA.max, 0)} pb) se llegaría.`}
        </p>
      )}

      {differs && (
        <button type="button" className="ps" style={{ marginTop: 10 }}
          onClick={() => { setLever("r", r); setLever("prima", prima); }}>
          Aplicar a mis palancas
        </button>
      )}
      <p className="muted" style={{ fontSize: 13, margin: "8px 0 0" }}>
        En este modelo el bono no reacciona a la deuda: la prima de riesgo es un
        supuesto que fijas tú. En la realidad, una deuda que no deja de crecer
        suele subirla.
      </p>
    </div>
  );
}
