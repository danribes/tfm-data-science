import type { Scenario } from "../engine/spain";
import type { ChainSpec } from "../components/Chain";
import { p01 } from "./p01_bonista";
import { p02 } from "./p02_banca";
import { p03 } from "./p03_comprador";
import { p04 } from "./p04_emprendedor";
import { p05 } from "./p05_funcionario";
import { p06 } from "./p06_politico";
import { p07 } from "./p07_corrupto";
import { p08 } from "./p08_infancia";
import { p09 } from "./p09_jubilado";
import { p10 } from "./p10_joven";
import { p11 } from "./p11_indefinido";
import { p12 } from "./p12_autonomo";

export interface PersonaModule {
  id: string;
  chains: ChainSpec[];
  narr: (R: Scenario, k: number, y: number) => string;
  cite: string;
}

export const SHIPPED_IDS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"];
const MODULES: Record<string, PersonaModule> = {
  "01": p01, "02": p02, "03": p03, "04": p04, "05": p05, "06": p06,
  "07": p07, "08": p08, "09": p09, "10": p10, "11": p11, "12": p12,
};
export const getPersonaModule = (id: string): PersonaModule | undefined => MODULES[id];
