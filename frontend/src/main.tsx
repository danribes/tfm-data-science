import { createRoot } from "react-dom/client";
import App from "./App";
import { initTheme } from "./state/theme";
import { initFromUrl, startUrlSync } from "./state/scenarioStore";
import "./styles/tokens.css";
import "./styles/base.css";

async function boot() {
  if (import.meta.env.VITE_MOCK_API === "1") {
    const { worker } = await import("./test/msw/browser");
    await worker.start({ onUnhandledRequest: "bypass" });
  }
  initTheme();
  initFromUrl();
  startUrlSync();
  createRoot(document.getElementById("root")!).render(<App />);
}
void boot();
