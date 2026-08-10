import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const dirname = import.meta.dirname;

export default defineConfig({
  // GitHub Pages serves the app under /<repo>/, so the asset base is
  // configurable at build time. Local dev and tests keep "/".
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  resolve: {
    alias: {
      "@fixtures": path.resolve(dirname, "../tests/fixtures"),
      "@": path.resolve(dirname, "src"),
    },
  },
  server: { fs: { allow: [path.resolve(dirname, ".."), dirname] } },
});
