import { defineConfig } from "vite";
import { reactRouter } from "@react-router/dev/vite";

// https://vitejs.dev/config/
export default defineConfig({
    base: "/A.I.D.E",
    plugins: [reactRouter()],
});
