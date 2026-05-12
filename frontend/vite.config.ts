import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

const proxyTarget = process.env.VITE_PROXY_API_TARGET;

export default defineConfig({
  envDir: path.resolve(__dirname, '..'),
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    ...(proxyTarget
      ? {
          proxy: {
            '/api': { target: proxyTarget, changeOrigin: true },
          },
        }
      : {}),
  },
});
