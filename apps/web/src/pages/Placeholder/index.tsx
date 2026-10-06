import { PageContainer, ProCard } from '@ant-design/pro-components';
import { useLocation } from '@umijs/max';
import { Empty, Typography } from 'antd';

const moduleNames: Record<string, string> = {
  '/operations/orders': '订单履约',
  '/operations/planning': '生产计划',
  '/supply-chain/material-readiness': '物料齐套',
  '/supply-chain/suppliers': '供应商',
  '/ai/decisions': 'Decision Center',
  '/ai/agent-trace': 'Agent Trace',
};

export default function PlaceholderPage() {
  const location = useLocation();
  const name = moduleNames[location.pathname] ?? '业务模块';

  return (
    <PageContainer title={name} content="页面入口已经建立，业务功能将在后续 Phase 实现。">
      <ProCard bordered>
        <Empty
          description={
            <Typography.Text type="secondary">
              {name} 已纳入 FactoryPilot 开发路线，目前处于工程基础阶段。
            </Typography.Text>
          }
        />
      </ProCard>
    </PageContainer>
  );
}
