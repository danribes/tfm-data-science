import { describe, expect, it } from "vitest";
import { limpiarPasaje, marcarFragmento } from "../passageText";

describe("el guion de final de renglón", () => {
  it("se une, porque el libro no lo tiene", () => {
    // El extractor de PDF conserva el guion con el que el libro partía la
    // palabra al final de la línea. La fuente pone «unemployment».
    expect(limpiarPasaje("the unemploy- ment rate")).toBe("the unemployment rate");
    expect(limpiarPasaje("la infla- ción subió")).toBe("la inflación subió");
  });

  it("no toca un guion entre mayúscula o cifra", () => {
    // Rangos y nombres propios no son palabras partidas.
    expect(limpiarPasaje("1960- 2014")).toBe("1960- 2014");
    expect(limpiarPasaje("Phillips- Solow")).toBe("Phillips- Solow");
  });

  it("no toca un compuesto sin espacio", () => {
    expect(limpiarPasaje("coste-beneficio")).toBe("coste-beneficio");
    expect(limpiarPasaje("wage-price spiral")).toBe("wage-price spiral");
  });

  it("normaliza los espacios que el extractor multiplica", () => {
    expect(limpiarPasaje("dos   espacios\n y salto")).toBe("dos espacios y salto");
  });
});

describe("el pasaje que empieza a media palabra", () => {
  it("se marca como fragmento", () => {
    // El corpus se trocea por tamaño, no por frase. Sin marca, «ose a point»
    // se lee como una errata del sistema en vez de como el recorte que es.
    expect(marcarFragmento("ose a point on the Phillips curve")).toBe("…ose a point on the Phillips curve");
  });

  it("no marca un pasaje que empieza bien", () => {
    expect(marcarFragmento("La curva de Phillips relaciona…")).toBe("La curva de Phillips relaciona…");
    expect(marcarFragmento("15.6 Expected inflation")).toBe("15.6 Expected inflation");
  });
});
