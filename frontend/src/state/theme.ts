export type Theme = "light" | "dark";

const KEY = "theme";

function osPrefers(): Theme {
  if (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    return "dark";
  }
  return "light";
}

export function getTheme(): Theme {
  return (document.documentElement.dataset.theme as Theme) ?? "light";
}

export function setTheme(t: Theme): void {
  document.documentElement.dataset.theme = t;
  localStorage.setItem(KEY, t);
}

export function initTheme(): void {
  const stored = localStorage.getItem(KEY) as Theme | null;
  document.documentElement.dataset.theme = stored ?? osPrefers();
}

export function toggleTheme(): Theme {
  const next: Theme = getTheme() === "dark" ? "light" : "dark";
  setTheme(next);
  return next;
}
