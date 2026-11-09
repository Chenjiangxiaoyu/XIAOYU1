import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  // The app is published at the repository Pages URL:
  // https://chenjiangxiaoyu.github.io/XIAOYU1/
  base: '/XIAOYU1/',
  plugins: [react()],
  server: { host: '0.0.0.0' },
});
