import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import Evidencia from "../Evidencia";

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><Evidencia /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Evidencia — calibrado frente a estimado", () => {
  it("shows each constant with its calibrated and estimated value", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("IPV_LR")).toBeInTheDocument());
    const row = screen.getByText("IPV_LR").closest("tr")!;
    expect(within(row).getByText("3,00")).toBeInTheDocument();   // calibrado
    expect(within(row).getByText("1,23")).toBeInTheDocument();   // estimado
    expect(within(row).getByText("0,93 … 1,53")).toBeInTheDocument();
  });

  it("marks a calibration outside its band as crossed, not as safe", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("IPV_LR")).toBeInTheDocument());
    const row = screen.getByText("IPV_LR").closest("tr")!;
    const verdict = within(row).getByText(/fuera de la banda/);
    expect(verdict.className).toContain("crossed");
  });

  it("draws the band, the estimate and the calibration marker", async () => {
    const { container } = ui();
    await waitFor(() => expect(screen.getByText("IPV_LR")).toBeInTheDocument());
    // Two constants plus IPV_LR's two windows.
    expect(container.querySelectorAll(".band-ci").length).toBe(4);
    expect(container.querySelectorAll(".band-est").length).toBe(4);
    // Nothing in the fixture is compatible, so every marker must render as bad
    // — a green marker here would be a silent lie.
    expect(container.querySelectorAll(".band-cal.bad").length).toBe(4);
    expect(container.querySelectorAll(".band-cal.ok").length).toBe(0);
  });

  it("splits the housing window so the estimate's sample dependence shows", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/2007–2013/)).toBeInTheDocument());
    const bust = screen.getByText(/2007–2013/).closest("tr")!;
    expect(within(bust).getByText("−6,48")).toBeInTheDocument();  // U+2212, per fmt.nf
    const boom = screen.getByText(/2014–2026/).closest("tr")!;
    expect(within(boom).getByText("5,00")).toBeInTheDocument();
    // The calibrated 3,0 sits between the two windows and inside neither. Each
    // sub-row must judge against its own band, not inherit the parent verdict.
    expect(within(bust).getByText(/tampoco cabe/)).toBeInTheDocument();
    expect(within(boom).getByText(/tampoco cabe/)).toBeInTheDocument();
    // A window has no calibrated value of its own — that column stays empty.
    expect(within(bust).getByText("—")).toBeInTheDocument();
  });

  it("does not invent windows for a constant that has none", async () => {
    const { container } = ui();
    await waitFor(() => expect(container.querySelector("tbody tr")).toBeTruthy());
    // Only IPV_LR carries windows in the fixture; IPV_REV must stay a bare row.
    expect(container.querySelectorAll("tbody tr").length).toBe(4);
    expect(container.querySelectorAll("tr.ev-sub").length).toBe(2);
  });

  it("puts the estimated impulse response next to the engine's assumption", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Cuánto dura un choque/)).toBeInTheDocument());
    const s = screen.getByText(/Cuánto dura un choque/).closest("section")!;
    const legend = s.querySelector(".legend")!;
    expect(within(legend as HTMLElement).getByText(/estimado en el panel/)).toBeInTheDocument();
    expect(within(legend as HTMLElement).getByText(/supuesto del motor/)).toBeInTheDocument();
    expect(within(legend as HTMLElement).getByText(/banda 90 %/)).toBeInTheDocument();
    // The reversion rate in the prose comes from the payload, not a literal.
    expect(within(s).getByText(/60 % cada año/)).toBeInTheDocument();
  });

  it("says the shock builds when the data says it builds", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Cuánto dura un choque/)).toBeInTheDocument());
    const s = screen.getByText(/Cuánto dura un choque/).closest("section")!;
    // Fixture rises 0,342 → 0,566 while the engine decays to 0,055. The verdict
    // is computed from those numbers, so a vintage that reverses the sign
    // reverses the sentence instead of leaving a stale claim on the page.
    expect(within(s).getByText(/0,57/)).toBeInTheDocument();
    expect(within(s).getByText(/inercia, no reversión/)).toBeInTheDocument();
    expect(within(s).queryByText(/La respuesta decae/)).not.toBeInTheDocument();
  });

  it("calls the impulse response persistence rather than causality", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Cuánto dura un choque/)).toBeInTheDocument());
    const s = screen.getByText(/Cuánto dura un choque/).closest("section")!;
    expect(within(s).getByText(/no causalidad estructural/)).toBeInTheDocument();
  });

  it("reports the fiscal persistence that bears on the sp lever", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Cuánto cuesta mover el saldo/)).toBeInTheDocument());
    expect(screen.getByText("0,87")).toBeInTheDocument();
    expect(screen.getByText(/0,81 … 0,94/)).toBeInTheDocument();
  });

  it("lists what the vintage cannot judge, with the reason", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Qué no puede juzgar/)).toBeInTheDocument());
    // Scoped to the list: MULT is also named further down, in the bullet that
    // explains why it can't be there.
    const list = screen.getByText(/Qué no puede juzgar/).closest("section")!;
    expect(within(list).getByText("MULT")).toBeInTheDocument();
    expect(within(list).getByText("OKUN")).toBeInTheDocument();
    expect(within(list).getByText(/shock fiscal identificado/)).toBeInTheDocument();
    // Only the blocked constants belong here — the estimable ones have a row.
    expect(within(list).queryByText("IPV_LR")).not.toBeInTheDocument();
    // The "no —" prefix is stripped in the UI; the reason itself must survive.
    expect(screen.queryByText(/^no — /)).not.toBeInTheDocument();
  });

  it("states that a calibration outside the band is a finding, not an error", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/no es un error/)).toBeInTheDocument());
    expect(screen.getByText(/calibraciones, no estimaciones/)).toBeInTheDocument();
  });

  it("warns that the housing window contains the crash", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/pinchazo inmobiliario/)).toBeInTheDocument());
  });

  it("explains itself before the estimates arrive", () => {
    ui();
    // Rendered synchronously, before the query resolves: the page states what
    // it is even when the API is down, so a blank panel is never the message.
    expect(screen.getByText(/Qué hace esta página/)).toBeInTheDocument();
    expect(screen.getByText(/Estimando sobre los paneles/)).toBeInTheDocument();
  });
});
