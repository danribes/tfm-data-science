import type { Scenario } from "../engine/spain";
import { CENTRAL } from "../engine/vintage";

interface FlowNode { id: string; label: string; val: number; color: string }

/** Las partidas de gasto que el vintage identifica, y en qué orden se muestran.
 *
 *  Antes sólo salían pensiones, educación e intereses: 21,9 puntos de PIB de
 *  los 45,4 que se gastan, con los otros 23,5 —más de la mitad del
 *  presupuesto— en un bloque llamado «resto». El motor ya traía las cuatro que
 *  faltaban; simplemente no se pintaban. Con ellas el residuo baja a unos 2,5
 *  puntos.
 *
 *  Sanidad NO está, y no por olvido: el corte de datos congelado no trae
 *  ninguna clasificación funcional del gasto (COFOG). El gasto sanitario está
 *  dentro de los salarios públicos y del consumo intermedio, que sí se
 *  publican, pero no puede separarse sin una fuente que este vintage no
 *  incorpora. Inventar la línea sería peor que no tenerla.
 */
const PARTIDAS: { id: string; label: string; key: keyof Scenario; color: string }[] = [
  { id: "pens", label: "Pensiones", key: "pens", color: "#f97316" },
  { id: "d1", label: "Salarios públicos", key: "d1", color: "#7c3aed" },
  { id: "p2", label: "Consumo intermedio", key: "p2", color: "#0891b2" },
  { id: "edu", label: "Educación", key: "edu", color: "#0284c7" },
  { id: "p51", label: "Inversión pública", key: "p51", color: "#16a34a" },
  { id: "d3", label: "Subvenciones", key: "d3", color: "#ca8a04" },
  { id: "int", label: "Intereses", key: "int", color: "#ef4444" },
];

/** Aggregate identities only; the model does not estimate tax earmarking. */
export function budgetFlows(scn: Scenario, k: number) {
  const spending = scn.gtot[k];
  const balance = scn.saldo[k];
  const revenues = spending + balance;
  const partidas = PARTIDAS.map((p) => ({ ...p, val: scn[p.key]?.[k] }));
  const identificado = partidas.reduce((sum, p) => sum + (p.val ?? 0), 0);
  const other = spending - identificado;
  // Las partidas pueden sumar MÁS que el gasto total, y a partir de 2035 lo
  // hacen: el total está congelado en su valor observado —`gtot` es
  // V0.gtot − sp, no evoluciona— igual que seis de las siete partidas,
  // mientras las pensiones sí crecen con la demografía. Antes no se notaba
  // porque sólo se pintaban tres partidas y su suma nunca llegaba al total.
  //
  // Devolver null aquí haría desaparecer el gráfico justo en los años que más
  // se miran. Se publica el descuadre para que la interfaz pueda decirlo.
  const exceso = Math.max(0, identificado - spending);
  if (![spending, balance, revenues, other].every(Number.isFinite)
    || spending <= 0 || revenues < 0
    || partidas.some((p) => !Number.isFinite(p.val) || (p.val as number) < 0)) return null;
  const sources: FlowNode[] = [
    { id: "rev", label: "Ingresos implícitos", val: revenues, color: "#10b981" },
    { id: "def", label: "Financiación del déficit", val: Math.max(0, -balance), color: "#ef4444" },
  ].filter((n) => n.val > 0);
  const targets: FlowNode[] = [
    ...partidas.map((p) => ({ id: p.id, label: p.label, val: p.val as number, color: p.color })),
    { id: "other", label: "Resto del gasto (residual)", val: Math.max(0, other), color: "#64748b" },
    { id: "surplus", label: "Superávit presupuestario", val: Math.max(0, balance), color: "#10b981" },
  ].filter((n) => n.val > 0);
  const total = sources.reduce((sum, n) => sum + n.val, 0);
  const links = sources.flatMap((s) => targets.map((t) => ({
    s: s.id, t: t.id, val: s.val * t.val / total, color: s.color,
  })));
  return { spending, balance, revenues, sources, targets, links, total, exceso, identificado };
}

/** Exact decomposition: Δb = GDP denominator effect − total fiscal balance. */
export function debtRatioBridge(scn: Scenario, k: number) {
  const previous = k > 0 ? scn.b[k - 1] : CENTRAL[2025].deuda;
  const current = scn.b[k];
  const denominatorEffect = previous / (1 + scn.gnom[k] / 100) - previous;
  const fiscalContribution = -scn.saldo[k];
  const change = current - previous;
  const residual = current - (previous + denominatorEffect + fiscalContribution);
  return { previous, current, denominatorEffect, fiscalContribution, change, residual };
}
