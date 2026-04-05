import type { ServerResponse } from 'http';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import type { Server } from 'http-proxy';

function onApiProxyError(_err: Error, _req: unknown, res: unknown) {
  const r = res as ServerResponse;
  if (!r || r.writableEnded || r.headersSent) return;
  r.writeHead(503, { 'Content-Type': 'application/json; charset=utf-8' });
  r.end(
    JSON.stringify({
      detail:
        'Python API kapalı (127.0.0.1:8000). Ayrı terminalde: py -m uvicorn app:app --reload --host 127.0.0.1 --port 8000',
    })
  );
}

function configureApiProxy(proxy: Server) {
  proxy.on('error', onApiProxyError);
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: configureApiProxy,
      },
    },
  },
  preview: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: configureApiProxy,
      },
    },
  },
});
