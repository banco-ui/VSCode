import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  root: 'electron',
  base: './',
  build: {
    outDir: '../dist-electron',
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'electron/src'),
    },
  },
  server: {
    port: 5173,
  },
});
