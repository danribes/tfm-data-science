import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@fixtures": path.resolve(__dirname, "../tests/fixtures"),
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: { fs: { allow: [path.resolve(__dirname, ".."), __dirname] } },
});
