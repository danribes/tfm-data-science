/** El tema, incluido lo que no se probaba y por eso no funcionaba.
 *
 *  El fallo reportado: cambiar el tema del sistema con la página abierta no
 *  hacía nada. La preferencia del sistema se leía una vez al arrancar y no
 *  se volvía a mirar, y no había ninguna prueba que lo exigiera — la única
 *  comprobaba el botón, que sí funcionaba.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

import { cycleTheme, getPref, getTheme, initTheme, resolve, setPref } from "../theme";

/** Un matchMedia falso con un interruptor, para poder cambiar «el sistema». */
function fakeOS(dark: boolean) {
  const listeners = new Set<() => void>();
  const mql = {
    matches: dark,
    addEventListener: (_: string, fn: () => void) => void listeners.add(fn),
    removeEventListener: (_: string, fn: () => void) => void listeners.delete(fn),
  };
  vi.stubGlobal("matchMedia", () => mql);
  return {
    switchTo(nowDark: boolean) {
      mql.matches = nowDark;
      listeners.forEach((fn) => fn());
    },
    get listenerCount() {
      return listeners.size;
    },
  };
}

beforeEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.theme;
  vi.unstubAllGlobals();
});

describe("preferencia y tema aplicado son cosas distintas", () => {
  it("sin nada guardado, la preferencia es seguir al sistema", () => {
    fakeOS(true);
    expect(getPref()).toBe("system");
    expect(resolve("system")).toBe("dark");
  });

  it("aplica el tema del sistema al arrancar", () => {
    fakeOS(true);
    initTheme();
    expect(getTheme()).toBe("dark");
  });

  it("elegir «sistema» borra la clave en lugar de escribir una", () => {
    fakeOS(false);
    setPref("dark");
    expect(localStorage.getItem("theme")).toBe("dark");
    setPref("system");
    expect(localStorage.getItem("theme")).toBeNull();
  });
});

describe("seguir al sistema en vivo — el fallo reportado", () => {
  it("repinta cuando el sistema cambia con la página abierta", () => {
    const os = fakeOS(false);
    initTheme();
    expect(getTheme()).toBe("light");

    os.switchTo(true);
    expect(getTheme()).toBe("dark");

    os.switchTo(false);
    expect(getTheme()).toBe("light");
  });

  it("una elección explícita manda sobre el sistema", () => {
    const os = fakeOS(false);
    initTheme();
    setPref("dark");

    os.switchTo(false);
    expect(getTheme()).toBe("dark");
    os.switchTo(true);
    expect(getTheme()).toBe("dark");
  });

  it("volver a «sistema» devuelve el control al sistema", () => {
    const os = fakeOS(false);
    initTheme();
    setPref("dark");
    setPref("system");
    expect(getTheme()).toBe("light");
    os.switchTo(true);
    expect(getTheme()).toBe("dark");
  });

  it("no acumula un oyente por cada arranque", () => {
    const os = fakeOS(false);
    initTheme();
    initTheme();
    initTheme();
    expect(os.listenerCount).toBeLessThanOrEqual(1);
  });
});

describe("el ciclo del botón", () => {
  it("avanza sistema → claro → oscuro → sistema", () => {
    fakeOS(false);
    initTheme();
    expect(getPref()).toBe("system");
    expect(cycleTheme()).toBe("light");
    expect(cycleTheme()).toBe("dark");
    expect(cycleTheme()).toBe("system");
  });

  it("un valor guardado por una versión anterior se respeta", () => {
    fakeOS(false);
    localStorage.setItem("theme", "dark");
    initTheme();
    expect(getPref()).toBe("dark");
    expect(getTheme()).toBe("dark");
  });

  it("un valor guardado corrupto no rompe nada", () => {
    fakeOS(true);
    localStorage.setItem("theme", "banana");
    initTheme();
    expect(getPref()).toBe("system");
    expect(getTheme()).toBe("dark");
  });
});
