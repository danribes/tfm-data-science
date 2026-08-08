import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { Explainer } from "../Explainer";
import { ContributionChart } from "../ContributionChart";
import { BASE_LEVERS } from "../../engine/vintage";
import { useScenarioStore } from "../../state/scenarioStore";

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("ContributionChart", () => {
  const contributions = [
    { lever_id: "r", lever_name: "Tipo de interés · Euríbor 12m", delta: 83.1, share: 0.7 },
    { lever_id: "pm", lever_name: "Precio importaciones/energía", delta: -2.0, share: 0.3 },
  ];

  it("renders nothing when no lever has moved", () => {
    const { container } = render(
      <ContributionChart contributions={[]} interaction={0} jointDelta={0} year={2050} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("draws one row per lever plus the interaction residual", () => {
    const { container } = render(
      <ContributionChart
        contributions={contributions}
        interaction={12.2}
        jointDelta={126.0}
        year={2050}
      />,
    );
    // Scoped to the row labels: the lever names also appear in the share
    // summary line below the chart, so a bare text query matches twice.
    const labels = [...container.querySelectorAll(".cr-label")].map((n) => n.textContent);
    expect(labels).toEqual([
      "Tipo de interés · Euríbor 12m",
      "Precio importaciones/energía",
      "Interacción entre palancas",
    ]);
  });

  it("omits the residual row when the interaction is negligible", () => {
    render(
      <ContributionChart
        contributions={contributions}
        interaction={0.01}
        jointDelta={81.1}
        year={2050}
      />,
    );
    expect(screen.queryByText("Interacción entre palancas")).not.toBeInTheDocument();
  });

  it("states that the decomposition is not additive", () => {
    render(
      <ContributionChart
        contributions={contributions}
        interaction={12.2}
        jointDelta={126.0}
        year={2050}
      />,
    );
    expect(screen.getByText(/no es lineal/)).toBeInTheDocument();
    expect(screen.getByText(/no un redondeo/)).toBeInTheDocument();
  });

  it("colours a debt increase as bad and a decrease as good", () => {
    const { container } = render(
      <ContributionChart
        contributions={contributions}
        interaction={0}
        jointDelta={81.1}
        year={2050}
      />,
    );
    expect(container.querySelector(".cr-bar.up")).toBeTruthy();   // +83.1
    expect(container.querySelector(".cr-bar.down")).toBeTruthy(); // −2.0
  });

  it("scales bar widths against the largest magnitude in the set", () => {
    const { container } = render(
      <ContributionChart
        contributions={contributions}
        interaction={0}
        jointDelta={81.1}
        year={2050}
      />,
    );
    const bars = container.querySelectorAll<HTMLElement>(".cr-bar");
    expect(bars[0].style.width).toBe("100%"); // 83.1 is the max
    expect(parseFloat(bars[1].style.width)).toBeCloseTo((2.0 / 83.1) * 100, 1);
  });
});

describe("Explainer", () => {
  beforeEach(() => {
    act(() => {
      useScenarioStore.setState({ levers: { ...BASE_LEVERS }, horizon: 2026 });
    });
  });

  it("shows the plain-language summary from the API", async () => {
    wrap(<Explainer />);
    await waitFor(() =>
      expect(screen.getByText(/línea base del vintage/)).toBeInTheDocument(),
    );
  });

  it("keeps the mechanism collapsed until asked", async () => {
    wrap(<Explainer />);
    const toggle = await screen.findByRole("button", { name: /ver el mecanismo/ });
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText(/identidad de deuda|mecanismo que trazar/)).toBeInTheDocument();
  });

  it("always carries the conditional-projection warning", async () => {
    wrap(<Explainer />);
    await waitFor(() =>
      expect(screen.getByText(/no es una previsión/i)).toBeInTheDocument(),
    );
  });

  it("discloses that the text is deterministic, not model-written", async () => {
    wrap(<Explainer />);
    await waitFor(() =>
      expect(screen.getByText(/plantillas deterministas/)).toBeInTheDocument(),
    );
  });

  it("reacts to a moved lever with its decomposition", async () => {
    act(() => {
      useScenarioStore.setState({ levers: { ...BASE_LEVERS, r: 4.8 }, horizon: 2026 });
    });
    wrap(<Explainer />);
    await waitFor(
      () => expect(screen.getByText(/Has movido 1 palanca/)).toBeInTheDocument(),
      { timeout: 3000 },
    );
    expect(screen.getByText(/Quién mueve la deuda/)).toBeInTheDocument();
  });
});
