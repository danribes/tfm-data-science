import type { StructuralDiff } from "../api/types";

const ICON: Record<string, string> = {
  converge: "✓",
  diverge: "✗",
  neutral: "≈",
};
const COLOR: Record<string, string> = {
  converge: "var(--ok, #22c55e)",
  diverge:  "var(--err, #ef4444)",
  neutral:  "var(--muted, #6b7280)",
};

export function AnalogDiffRow({ diff }: { diff: StructuralDiff }) {
  const icon  = ICON[diff.direction]  ?? "?";
  const color = COLOR[diff.direction] ?? "inherit";
  return (
    <tr className="analog-diff-row">
      <td style={{ color, fontWeight: 600, width: 24, textAlign: "center" }}
          aria-label={diff.direction}>{icon}</td>
      <td style={{ fontSize: 13 }}>{diff.label}</td>
      <td style={{ fontSize: 13, color: "var(--muted)", textAlign: "right" }}>
        {diff.spain_value}
      </td>
      <td style={{ fontSize: 13, textAlign: "right" }}>{diff.analog_value}</td>
      <td style={{ fontSize: 12, color, textAlign: "right" }}>{diff.direction}</td>
    </tr>
  );
}
