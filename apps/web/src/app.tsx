import { LogoutOutlined, UserOutlined } from '@ant-design/icons';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { history } from '@umijs/max';
import { ConfigProvider, Dropdown } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import type { ReactNode } from 'react';

import {
  clearStoredSession,
  getCurrentUser,
  hasStoredSession,
  logout,
  type CurrentUserContext,
} from './services/auth';
import './global.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 10_000,
      retry: 1,
    },
  },
});

export interface InitialState {
  currentUser: CurrentUserContext | null;
}

export async function getInitialState(): Promise<InitialState> {
  if (!hasStoredSession()) {
    return { currentUser: null };
  }

  try {
    return { currentUser: await getCurrentUser() };
  } catch {
    clearStoredSession();
    return { currentUser: null };
  }
}

export const layout = ({ initialState, setInitialState }: {
  initialState?: InitialState;
  setInitialState: (state: InitialState) => Promise<void> | void;
}) => ({
  title: 'FactoryPilot',
  logo: '/logo.svg',
  layout: 'side' as const,
  navTheme: 'light' as const,
  contentWidth: 'Fluid' as const,
  fixedHeader: true,
  fixSiderbar: true,
  siderWidth: 236,
  menu: {
    locale: false,
  },
  footerRender: false,
  onPageChange: () => {
    if (history.location.pathname === '/login') {
      return;
    }
    if (!initialState?.currentUser) {
      const redirect = `${history.location.pathname}${history.location.search}`;
      history.replace(`/login?redirect=${encodeURIComponent(redirect)}`);
    }
  },
  avatarProps: initialState?.currentUser
    ? {
        icon: <UserOutlined />,
        title: initialState.currentUser.display_name,
        render: (_props: unknown, dom: ReactNode) => (
          <Dropdown
            placement="bottomRight"
            menu={{
              items: [
                {
                  key: 'logout',
                  icon: <LogoutOutlined />,
                  label: '退出登录',
                },
              ],
              onClick: async ({ key }) => {
                if (key !== 'logout') {
                  return;
                }
                await logout();
                queryClient.clear();
                await setInitialState({ currentUser: null });
                history.replace('/login');
              },
            }}
          >
            <span>{dom}</span>
          </Dropdown>
        ),
      }
    : undefined,
});

export function rootContainer(container: ReactNode) {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1677ff',
          colorInfo: '#1677ff',
          colorSuccess: '#16a34a',
          colorWarning: '#f59e0b',
          colorError: '#dc2626',
          colorBgBase: '#ffffff',
          colorBgContainer: '#ffffff',
          colorBgElevated: '#ffffff',
          colorBgLayout: '#f3f6fa',
          colorFillAlter: '#f8fafc',
          colorTextBase: '#1f2937',
          colorText: '#1f2937',
          colorTextHeading: '#0f172a',
          colorTextSecondary: '#64748b',
          colorBorderSecondary: '#e8edf3',
          borderRadius: 6,
          borderRadiusLG: 8,
          fontFamily:
            "Inter, 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
        components: {
          Card: {
            headerHeight: 48,
            colorBgContainer: '#ffffff',
          },
          Table: {
            headerBg: '#f8fafc',
            headerColor: '#334155',
            rowHoverBg: '#f8fbff',
          },
        },
      }}
    >
      <QueryClientProvider client={queryClient}>{container}</QueryClientProvider>
    </ConfigProvider>
  );
}
