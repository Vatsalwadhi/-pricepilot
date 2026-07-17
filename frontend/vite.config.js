import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            "/search": "http://127.0.0.1:8000",
            "/history": "http://127.0.0.1:8000",
            "/comparison": "http://127.0.0.1:8000"
        }
    }
});
