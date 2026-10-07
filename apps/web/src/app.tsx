import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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

export const layout = () => ({
  title: 'FactoryPilot',
  logo: '/logo.svg',
  layout: 'side' as const,
  navTheme: 'light' as const,
  contentWidth: 'Fluid' as const,
  fixedHeader: true,
  fixSiderbar: true,
  siderWidth: 232,
  menu: {
    locale: false,
  },
  actionsRender: () => [
    <Tag color="blue" key="phase">
      Phase 0 · Engineering Foundation
    </Tag>,
  ],
  avatarProps: {
    title: '系统管理员',
    size: 'small' as const,
  },
  footerRender: false,
});

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
