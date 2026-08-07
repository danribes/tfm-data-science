import type { Scenario } from "../engine/spain";
import type { ChainSpec } from "../components/Chain";
import { p01 } from "./p01_bonista";
import { p02 } from "./p02_banca";
import { p03 } from "./p03_comprador";
import { p06 } from "./p06_politico";

export interface PersonaModule {
  id: string;
  chains: ChainSpec[];
  narr: (R: Scenario, k: number, y: number) => string;
  cite: string;
}

export const SHIPPED_IDS = ["01", "02", "03", "06"];
const MODULES: Record<string, PersonaModule> = { "01": p01, "02": p02, "03": p03, "06": p06 };
export const getPersonaModule = (id: string): PersonaModule | undefined => MODULES[id];
