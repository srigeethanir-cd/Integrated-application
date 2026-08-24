import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(process.env.PORT || '5175'),
    host: '0.0.0.0',
    strictPort: false,
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8010',
        changeOrigin: true,
      },
      '/health': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8010',
        changeOrigin: true,
      }
    }
  }
});
