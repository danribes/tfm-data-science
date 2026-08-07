import { render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Metodologia from "../Metodologia";
import { queryClient } from "../../api/hooks";

const ui = () => render(<QueryClientProvider client={queryClient}><Metodologia /></QueryClientProvider>);

describe("Metodología — provenance, parity, honesty", () => {
  beforeEach(() => queryClient.clear());

  it("renders the 31 constants with provenance", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("MULT")).toBeInTheDocument());
    // 31 data rows + header
    expect(screen.getAllByRole("row")).toHaveLength(32);
    expect(screen.getAllByText(/v16 calibration/).length).toBeGreaterThan(10);
  });

  it("lists the 9 red lines with their sources", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/máximo histórico ES \(T1-2013\)/)).toBeInTheDocument());
    expect(screen.getByText(/umbral Maastricht/)).toBeInTheDocument();
  });

  it("states engine parity, the MC ±2pp rule, and the seed-42 caveat", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/mismo fixture de anclas/i)).toBeInTheDocument());
    expect(screen.getByText(/±2 pp/)).toBeInTheDocument();
    expect(screen.getByText(/PCG64/)).toBeInTheDocument();
  });

  it("explains persona reds vs global red lines (the 15% sobre / 40% renta case)", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Sobrecarga > 40 % renta/)).toBeInTheDocument());
    expect(screen.getByText(/15,0/)).toBeInTheDocument();
  });

  it("shows the known-gaps list", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/mora bancaria/i)).toBeInTheDocument());
    expect(screen.getByText(/RETA/)).toBeInTheDocument();
    expect(screen.getByText(/govindicators\.org/)).toBeInTheDocument();
  });
});
