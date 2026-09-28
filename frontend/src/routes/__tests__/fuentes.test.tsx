import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import Fuentes from "../Fuentes";
import snapshot from "../../data/fuentes.json";

describe("Estado de las fuentes — un tablero que no finge", () => {
  afterEach(() => vi.restoreAllMocks());

  it("resume la última comprobación con las cifras del snapshot", () => {
    render(<Fuentes />);
    const tiles = screen.getByRole("group", { name: "Resumen de la comprobación" });
    expect(within(tiles).getByText(snapshot.vintage)).toBeInTheDocument();
    expect(within(tiles).getByText(snapshot.checked)).toBeInTheDocument();
    const { sources, ok, attention } = snapshot.counts;
    expect(within(tiles).getByText(`${ok}/${sources}`)).toBeInTheDocument();
    expect(within(tiles).getByText(String(attention))).toBeInTheDocument();
  });

  it("lista cada fuente, y marca las que hay que revisar", () => {
    render(<Fuentes />);
    const table = screen.getByRole("table");
    // Una fila por fuente, derivados incluidos, más la cabecera.
    expect(within(table).getAllByRole("row")).toHaveLength(snapshot.sources.length + 1);
    expect(within(table).getByText("Euríbor a 12 meses")).toBeInTheDocument();
    const flagged = snapshot.sources.filter((s) => s.signal === "size_changed").length;
    expect(within(table).getAllByText("tamaño distinto: revisar")).toHaveLength(flagged);
  });

  it("dice qué no cubre, y enlaza el inventario completo", () => {
    render(<Fuentes />);
    const scope = screen.getByText(
      new RegExp(`sólo comprueba las ${snapshot.counts.sources} fuentes descargables`));
    expect(scope).toHaveTextContent(/senda central de deuda/);
    expect(scope).toHaveTextContent(/proyecciones demográficas/);
    const link = within(scope).getByRole("link", { name: "data/README.md" });
    expect(link.getAttribute("href")).toMatch(/\/data\/README\.md$/);
  });

  it("dice que sin huella el tamaño es una pista, no una prueba", () => {
    render(<Fuentes />);
    expect(screen.getByText(/es una pista, no una prueba/)).toBeInTheDocument();
  });

  it("no deja importar hasta que alguien declara haber revisado", async () => {
    const user = userEvent.setup();
    render(<Fuentes />);
    const button = screen.getByRole("button", { name: /Importar datos nuevos/ });
    expect(button).toBeDisabled();
    await user.click(screen.getByRole("checkbox", { name: /He revisado las fuentes marcadas/ }));
    expect(button).toBeEnabled();
  });

  it("el botón es un prototipo: explica los pasos y no toca la red", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<Fuentes />);
    await user.click(screen.getByRole("checkbox", { name: /He revisado las fuentes marcadas/ }));
    await user.click(screen.getByRole("button", { name: /Importar datos nuevos/ }));

    const panel = screen.getByRole("region", { name: "Qué haría la importación" });
    expect(within(panel).getByText(/este botón no importa nada/)).toBeInTheDocument();
    expect(within(panel).getByText(new RegExp(snapshot.vintage))).toBeInTheDocument();
    expect(within(panel).getAllByRole("listitem")).toHaveLength(5);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
