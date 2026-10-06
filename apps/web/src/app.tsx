import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { RequestConfig, RunTimeLayoutConfig } from '@umijs/max';
import { Link } from '@umijs/max';
import { ConfigProvider, Tag } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import type { ReactNode } from 'react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 10_000,
      retry: 1,
    },
  },
});

export const layout: RunTimeLayoutConfig = () => ({
  title: 'FactoryPilot',
  logo: '/logo.svg',
  layout: 'side',
  navTheme: 'light',
  contentWidth: 'Fluid',
  fixedHeader: true,
  fixSiderbar: true,
  siderWidth: 232,
  menu: {
    locale: false,
  },
  menuItemRender: (item, dom) =>
    item.path ? (
      <Link to={item.path} prefetch>
        {dom}
      </Link>
    ) : (
      dom
    ),
  actionsRender: () => [
    <Tag color="blue" key="phase">
      Phase 0 · Engineering Foundation
    </Tag>,
  ],
  avatarProps: {
    title: '系统管理员',
    size: 'small',
  },
  footerRender: false,
});

export const request: RequestConfig = {
  timeout: 15_000,
};

export function rootContainer(container: ReactNode) {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#2563eb',
          colorBgLayout: '#f5f7fa',
          colorText: '#1f2937',
          borderRadius: 6,
          fontFamily:
            "Inter, 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
      }}
    >
      <QueryClientProvider client={queryClient}>{container}</QueryClientProvider>
    </ConfigProvider>
  );
}
