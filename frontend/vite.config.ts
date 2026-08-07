import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const dirname = import.meta.dirname;

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@fixtures": path.resolve(dirname, "../tests/fixtures"),
      "@": path.resolve(dirname, "src"),
    },
  },
  server: { fs: { allow: [path.resolve(dirname, ".."), dirname] } },
});
