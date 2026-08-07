import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Semaphore } from "../Semaphore";

const items = [
  { title: "Deuda > 105 %PIB", valueText: "106,3", status: "crossed" as const, note: "narrativa crack23 [comentario]" },
  { title: "Bono 10A > 7 %", valueText: "6,5", status: "near" as const, note: "zona rescate 2012 [hist]" },
  { title: "Paro > 26,9 %", valueText: "10,1", status: "safe" as const, note: "máximo histórico ES (T1-2013) [hist]" },
  { title: "WGI control de la corrupción", valueText: "s/d", status: "sd" as const, note: "API archivada [hueco de datos]" },
];

describe("Semaphore — computed statuses, never authored", () => {
  it("maps status → pill class and Spanish label", () => {
    render(<Semaphore items={items} />);
    expect(screen.getByText("106,3")).toHaveClass("st", "cross");
    expect(screen.getByText("6,5")).toHaveClass("st", "near");
    expect(screen.getByText("10,1")).toHaveClass("st", "safe");
    expect(screen.getByText("s/d")).toHaveClass("st", "sd");
    expect(screen.getByText(/cerca ·/)).toBeInTheDocument(); // note row prefixes label
  });
});
