import { describe, expect, it } from "vitest";
import * as C from "../constants";
import { BASE_LEVERS, CENTRAL, ENGINE_VERSION, OLDDEP, V0, VINTAGE } from "../vintage";
import anchors from "@fixtures/engine_anchors.json";

describe("generated constants match the Python engine and the committed vintage", () => {
  it("named v16 constants (engine/constants.py values)", () => {
    expect(C.MULT).toBe(1.4);
    expect(C.RHO).toBe(0.62);
    expect(C.E_R).toBe(0.45);
    expect(C.E_EXT).toBe(0.25);
    expect(C.E_PM).toBe(0.012);
    expect(C.OKUN).toBe(0.48);
    expect(C.KAPPA).toBe(0.22);
    expect(C.GAMMA).toBe(0.045);
    expect(C.THETA).toBe(0.55);
    expect(C.PHI).toBe(0.3);
    expect(C.A_Z).toBe(1.1);
    expect(C.A_TAU).toBe(0.3);
    expect(C.A_LAM).toBe(0.45);
    expect(C.REFI).toBe(0.14);
    expect(C.TERM).toBe(0.17);
    expect(C.DIFF).toBe(1.4757);
    expect(C.IPV_LR).toBe(3.0);
    expect(C.IPV_REV).toBe(0.6);
    expect(C.E_IPV_R).toBe(2.6);
    expect(C.E_IPV_G).toBe(1.1);
    expect(C.RJUV).toBe(2.317);
    expect(C.PM_DECAY).toBe(0.45);
    expect(C.CAL_SALARIO_MES).toBe(1749.79);
  });
  it("31 provenance rows for Metodología", () => {
    expect(C.CONSTANTS_META).toHaveLength(31);
    expect(C.CONSTANTS_META[0]).toMatchObject({ name: "MULT", value: 1.4, unit: "x" });
    expect(C.CONSTANTS_META.map((r) => r.name)).toContain("MC_SIG_R");
  });
  it("vintage-anchored values", () => {
    expect(VINTAGE).toBe(anchors.vintage); // "2026-07-31"
    expect(ENGINE_VERSION).toBe("1.0.0");
    expect(V0.u).toBe(10.1);
    expect(V0.pi).toBe(3.0);
    expect(V0.g).toBe(2.7);
    expect(V0.bono).toBe(3.42);
    expect(V0.precio).toBe(171444);
    expect(V0.cuota).toBe(745);
    expect(V0.salmes).toBe(1749.79);
    expect(V0.salario).toBe(24497);
    expect(V0.ipv).toBe(12.8);
    expect(V0.pens).toBe(13.23);
    expect(V0.vida).toBe(84.0);
    expect(BASE_LEVERS).toEqual({
      r: 2.8, prima: 45, sp: 0.0, lam: 0.9, pm: 0.0,
      tau: 0.0, z: 0.0, ext: 1.8, dem: 0.0, idx: 0.0,
    });
    expect(CENTRAL[2025]).toEqual({ deuda: 105.6, pb: -1.13, r_efectivo: 2.57, g_nominal: 3.3, presion_demog: 0.23 });
    expect(CENTRAL[2026].r_efectivo).toBe(2.68);
    expect(CENTRAL[2050].pb).toBe(-7.47);
    expect(OLDDEP[2026]).toBe(32.6);
  });
});
