import { STATUS_LABEL, type RedLineStatus } from "../engine/redlines";

export interface SemaphoreItem {
  icon?: string;
  title: string;
  valueText: string;
  status: RedLineStatus;
  note: string;
}

const PILL_CLASS: Record<RedLineStatus, string> = {
  crossed: "st cross",
  near: "st near",
  safe: "st safe",
  sd: "st sd",
};

export function Semaphore({ items }: { items: SemaphoreItem[] }) {
  return (
    <div>
      {items.map((it) => (
        <div className="rl-item" key={it.title}>
          <span className="ic">{it.icon ?? "🚨"}</span>
          <span className="t"><b>{it.title}</b></span>
          <span className={PILL_CLASS[it.status]}>{it.valueText}</span>
          <span className="x">{STATUS_LABEL[it.status]} · {it.note}</span>
        </div>
      ))}
    </div>
  );
}
