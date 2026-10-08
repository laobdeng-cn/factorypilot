import { defineConfig } from '@umijs/max';

import routes from './routes';

const apiProxyTarget = process.env.FACTORYPILOT_API_PROXY_TARGET ?? 'http://127.0.0.1:8000';

export default defineConfig({
  antd: {},
  access: {},
  initialState: {},
  model: {},
  request: {},
  layout: {
    title: 'FactoryPilot',
    locale: false,
  },
  locale: {
    default: 'zh-CN',
    antd: true,
    baseNavigator: false,
  },
  routes,
  history: {
    type: 'browser',
  },
  proxy: {
    '/api/': {
      target: apiProxyTarget,
      changeOrigin: true,
    },
  },
  esbuildMinifyIIFE: true,
  npmClient: 'pnpm',
  favicons: ['/favicon.svg'],
});
