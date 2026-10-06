export default [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    name: '智造总览',
    icon: 'DashboardOutlined',
    path: '/dashboard',
    component: './Dashboard',
  },
  {
    name: '生产运营',
    icon: 'ControlOutlined',
    path: '/operations',
    routes: [
      {
        name: '订单履约',
        path: '/operations/orders',
        component: './Placeholder',
      },
      {
        name: '生产计划',
        path: '/operations/planning',
        component: './Placeholder',
      },
    ],
  },
  {
    name: '供应链',
    icon: 'TruckOutlined',
    path: '/supply-chain',
    routes: [
      {
        name: '物料齐套',
        path: '/supply-chain/material-readiness',
        component: './Placeholder',
      },
      {
        name: '供应商',
        path: '/supply-chain/suppliers',
        component: './Placeholder',
      },
    ],
  },
  {
    name: 'AI 智能决策',
    icon: 'RobotOutlined',
    path: '/ai',
    routes: [
      {
        name: 'Decision Center',
        path: '/ai/decisions',
        component: './Placeholder',
      },
      {
        name: 'Agent Trace',
        path: '/ai/agent-trace',
        component: './Placeholder',
      },
    ],
  },
  {
    name: '系统基础',
    icon: 'SettingOutlined',
    path: '/system',
    routes: [
      {
        name: '服务状态',
        path: '/system/health',
        component: './SystemHealth',
      },
    ],
  },
  {
    path: '*',
    layout: false,
    component: './NotFound',
  },
];
