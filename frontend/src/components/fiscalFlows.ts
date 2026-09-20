import type { Scenario } from "../engine/spain";
import { CENTRAL } from "../engine/vintage";

interface FlowNode { id: string; label: string; val: number; color: string }

/** Aggregate identities only; the model does not estimate tax earmarking. */
export function budgetFlows(scn: Scenario, k: number) {
  const spending = scn.gtot[k];
  const balance = scn.saldo[k];
  const revenues = spending + balance;
  const other = spending - scn.pens[k] - scn.edu[k] - scn.int[k];
  if (![spending, balance, revenues, other, scn.pens[k], scn.edu[k], scn.int[k]].every(Number.isFinite)
    || spending <= 0 || revenues < 0 || other < -1e-9
    || [scn.pens[k], scn.edu[k], scn.int[k]].some((v) => v < 0)) return null;
  const sources: FlowNode[] = [
    { id: "rev", label: "Ingresos implícitos", val: revenues, color: "#10b981" },
    { id: "def", label: "Financiación del déficit", val: Math.max(0, -balance), color: "#ef4444" },
  ].filter((n) => n.val > 0);
  const targets: FlowNode[] = [
    { id: "pens", label: "Pensiones", val: scn.pens[k], color: "#f97316" },
    { id: "edu", label: "Educación", val: scn.edu[k], color: "#0284c7" },
    { id: "int", label: "Intereses", val: scn.int[k], color: "#ef4444" },
    { id: "other", label: "Resto del gasto (residual)", val: Math.max(0, other), color: "#64748b" },
    { id: "surplus", label: "Superávit presupuestario", val: Math.max(0, balance), color: "#10b981" },
  ].filter((n) => n.val > 0);
  const total = sources.reduce((sum, n) => sum + n.val, 0);
  const links = sources.flatMap((s) => targets.map((t) => ({
    s: s.id, t: t.id, val: s.val * t.val / total, color: s.color,
  })));
  return { spending, balance, revenues, sources, targets, links, total };
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
