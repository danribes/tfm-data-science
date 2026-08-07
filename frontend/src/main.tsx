import { createRoot } from "react-dom/client";
import { initTheme } from "./state/theme";
import "./styles/tokens.css";
import "./styles/base.css";
import App from "./App";

initTheme();
createRoot(document.getElementById("root")!).render(<App />);
