import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RagReportCard } from "../RagReportCard";

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}><RagReportCard /></QueryClientProvider>,
  );
}

describe("RagReportCard — la biblioteca enseña sus notas", () => {
  it("shows the four measurements with their meanings", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Esta biblioteca se evalúa/)).toBeInTheDocument());
    expect(screen.getByText("97 %")).toBeInTheDocument();       // hit@8
    expect(screen.getByText("4/4")).toBeInTheDocument();        // refusals
    expect(screen.getByText("93 %")).toBeInTheDocument();       // cited share
    expect(screen.getByText("10/12")).toBeInTheDocument();      // fidelity
    expect(screen.getByText(/rechazadas en vez de inventadas/)).toBeInTheDocument();
  });

  it("names the isolation and guardrail states in the header", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/sin fugas/)).toBeInTheDocument());
    expect(screen.getByText(/íntegro/)).toBeInTheDocument();
  });

  it("marks a healthy metric as healthy, not bad", async () => {
    const { container } = ui();
    await waitFor(() => expect(container.querySelector(".rr-item")).toBeTruthy());
    expect(container.querySelectorAll(".rr-item")).toHaveLength(4);
    expect(container.querySelectorAll(".rr-item.bad")).toHaveLength(0);
  });

  it("says how to regenerate the numbers", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/rag.evaluate/)).toBeInTheDocument());
    expect(screen.getByText(/rag.eval_chat/)).toBeInTheDocument();
  });
});
