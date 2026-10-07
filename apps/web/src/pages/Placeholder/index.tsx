import { PageContainer } from '@ant-design/pro-components';
import { AppstoreOutlined } from '@ant-design/icons';
import { Card, Empty, Tag, Typography } from 'antd';

const moduleNames: Record<string, string> = {
  '/orders/sales': '销售订单',
  '/orders/forecast': '交付预测',
  '/orders/at-risk': '风险订单',
  '/operations/planning': '生产计划',
  '/operations/aps': 'APS 排程',
  '/operations/work-orders': '生产工单',
  '/operations/execution': '生产执行',
  '/operations/capacity': '产能分析',
  '/materials/readiness': '物料齐套',
  '/materials/shortage': '缺料分析',
  '/materials/inventory': '库存管理',
  '/materials/lots': '批次库存',
  '/materials/reservations': '库存预留',
  '/supply/purchase-orders': '采购订单',
  '/supply/suppliers': '供应商',
  '/supply/risks': '供应风险',
  '/supply/receipts': '到货管理',
  '/quality/issues': '质量异常',
  '/quality/holds': 'Quality Hold',
  '/quality/inspections': '检验批次',
  '/quality/ncr': 'NCR',
  '/exceptions/center': '异常中心',
  '/exceptions/alerts': '风险预警',
  '/exceptions/timeline': '事件时间线',
  '/ai/decisions': 'Decision Center',
  '/ai/what-if': 'What-if 推演',
  '/ai/workspace': 'Agent Workspace',
  '/ai/agent-trace': 'Agent Trace',
  '/ai/history': '决策历史',
  '/approvals/pending': '待我审批',
  '/approvals/mine': '我的申请',
  '/approvals/history': '审批记录',
  '/master-data/plants': '工厂与产线',
  '/master-data/resources': '设备与工作中心',
  '/master-data/materials': '物料',
  '/master-data/boms': 'BOM',
  '/master-data/routings': 'Routing',
  '/master-data/suppliers': '供应商主数据',
  '/system/organization': '用户与组织',
  '/system/rbac': '角色与权限',
  '/system/integrations': '集成中心',
  '/system/audit': '审计日志',
};

export default function PlaceholderPage() {
  const pathname = window.location.pathname;
  const name = moduleNames[pathname] ?? '业务模块';

  return (
    <PageContainer
      title={name}
      content="模块入口已经按 FactoryPilot 正式信息架构建立，业务能力将在对应 Phase 接入。"
      extra={<Tag color="blue">Phase 0.4 UI Baseline</Tag>}
    >
      <Card>
        <Empty
          image={<AppstoreOutlined style={{ color: '#94a3b8', fontSize: 48 }} />}
          description={
            <div>
              <Typography.Title level={5}>{name}</Typography.Title>
              <Typography.Text type="secondary">
                当前阶段先验证国内制造企业平台的导航、布局与信息层级。
              </Typography.Text>
            </div>
          }
        />
      </Card>
    </PageContainer>
  );
}
