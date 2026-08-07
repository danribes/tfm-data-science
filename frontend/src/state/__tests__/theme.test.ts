import { beforeEach, describe, expect, it } from "vitest";
import { getTheme, initTheme, setTheme } from "../theme";

describe("theme — data-theme attribute + localStorage persistence", () => {
  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.theme;
  });
  it("initTheme defaults to light when no preference stored (jsdom matchMedia is non-matching)", () => {
    initTheme();
    expect(document.documentElement.dataset.theme).toBe("light");
  });
  it("setTheme stamps the attribute and persists", () => {
    initTheme();
    setTheme("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");
    expect(getTheme()).toBe("dark");
  });
  it("initTheme honors a stored choice over the OS default", () => {
    localStorage.setItem("theme", "dark");
    initTheme();
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
