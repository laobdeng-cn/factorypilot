import { defineConfig } from '@umijs/max';

import routes from './routes';

export default defineConfig({
  antd: {},
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
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
  esbuildMinifyIIFE: true,
  npmClient: 'pnpm',
  favicons: ['/favicon.svg'],
});
