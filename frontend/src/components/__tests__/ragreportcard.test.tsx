import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { setRagConnection } from "../../api/client";
import { server } from "../../test/msw/server";
import { RagReportCard } from "../RagReportCard";

afterEach(() => { cleanup(); setRagConnection(null); });

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}><RagReportCard /></QueryClientProvider>,
  );
}

describe("RagReportCard — la biblioteca enseña sus notas", () => {
  it("shows the four measurements with their meanings", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Evaluación de desarrollo del proyecto/)).toBeInTheDocument());
    expect(screen.getByText("97 %")).toBeInTheDocument();       // hit@8
    expect(screen.getByText("4/4")).toBeInTheDocument();        // refusals
    expect(screen.getByText("93 %")).toBeInTheDocument();       // cited share
    expect(screen.getByText("10/12")).toBeInTheDocument();      // fidelity
    expect(screen.getByText(/con abstención detectada/)).toBeInTheDocument();
    expect(screen.getByText(/no de un test independiente/)).toBeInTheDocument();
  });

  it("names the isolation and guardrail states in the header", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/sin fugas/)).toBeInTheDocument());
    expect(screen.getByText(/sin fallos en las sondas evaluadas/)).toBeInTheDocument();
  });

  it("shows measurements without a post-hoc pass threshold", async () => {
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

  it("changes evaluation with the library connection and never reuses another corpus's scores", async () => {
    const base = "https://public-library.example.test";
    const note = "La biblioteca pública no tiene una evaluación publicada.";
    server.use(http.get(`${base}/rag/eval`, () => HttpResponse.json({ available: false, note })));
    ui();
    expect(await screen.findByText("97 %")).toBeInTheDocument();
    act(() => setRagConnection(base));
    expect(screen.queryByText("97 %")).not.toBeInTheDocument();
    expect(await screen.findByText(note)).toBeInTheDocument();
    expect(screen.queryByText("93 %")).not.toBeInTheDocument();
    act(() => setRagConnection(null));
    expect(await screen.findByText("97 %")).toBeInTheDocument();
    expect(screen.queryByText(note)).not.toBeInTheDocument();
  });
});
