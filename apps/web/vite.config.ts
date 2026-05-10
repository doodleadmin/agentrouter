import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Production base path for Mini App static serving.
// Set to /app/ when building for deployment (VITE_BASE_PATH=/app/).
// Defaults to / for local development (npm run dev).
const base = process.env.VITE_BASE_PATH || '/';

export default defineConfig({
  plugins: [react()],
  base,
});
