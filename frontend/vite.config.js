import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const localApiTarget = process.env.VITE_DEV_API_TARGET || "http://127.0.0.1:8080";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": localApiTarget,
      "/health": localApiTarget,
    },
  },
});
