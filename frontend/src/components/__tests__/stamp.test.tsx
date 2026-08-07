import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Stamp } from "../Stamp";

describe("Stamp — 📅 observed vs 🔮 conditional", () => {
  it("fresh (levers at base + horizon hoy) → 📅 dato observado", () => {
    render(<Stamp fresh year={2026} />);
    const el = screen.getByText(/📅 dato observado · vintage/);
    expect(el).toHaveClass("badge-fwd");
    expect(el).not.toHaveClass("lab");
  });

  it("any lever moved or horizon > hoy → 🔮 condicional · year", () => {
    render(<Stamp fresh={false} year={2035} />);
    const el = screen.getByText("🔮 condicional · 2035");
    expect(el).toHaveClass("badge-fwd", "lab");
  });
});
