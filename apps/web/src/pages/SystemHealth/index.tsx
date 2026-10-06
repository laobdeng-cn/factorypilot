import { PageContainer, ProCard } from '@ant-design/pro-components';
import { useQuery } from '@tanstack/react-query';
import { Descriptions, Space, Tag, Typography } from 'antd';

import { getLiveness, getReadiness } from '@/services/factorypilot';

export default function SystemHealthPage() {
  const liveness = useQuery({
    queryKey: ['health', 'live'],
    queryFn: getLiveness,
    retry: false,
  });
  const readiness = useQuery({
    queryKey: ['health', 'ready'],
    queryFn: getReadiness,
    retry: false,
  });

  const apiOnline = Boolean(liveness.data);

  return (
    <PageContainer
      title="服务状态"
      content="用于验证 FactoryPilot Web 与 FastAPI 基础服务的联通状态。"
    >
      <ProCard bordered title="FactoryPilot API">
        <Space direction="vertical" size={20} style={{ width: '100%' }}>
          <Space>
            <Typography.Text strong>服务状态</Typography.Text>
            <Tag color={apiOnline ? 'success' : 'error'}>
              {apiOnline ? 'ONLINE' : 'OFFLINE'}
            </Tag>
          </Space>

          <Descriptions
            bordered
            column={1}
            items={[
              {
                key: 'service',
                label: 'Service',
                children: liveness.data?.service ?? '-',
              },
              {
                key: 'version',
                label: 'Version',
                children: liveness.data?.version ?? '-',
              },
              {
                key: 'environment',
                label: 'Environment',
                children: liveness.data?.environment ?? '-',
              },
              {
                key: 'liveness',
                label: 'Liveness',
                children: liveness.data?.status ?? 'unavailable',
              },
              {
                key: 'readiness',
                label: 'Readiness',
                children: readiness.data?.status ?? 'unavailable',
              },
              {
                key: 'database',
                label: 'Database',
                children: readiness.data?.checks.database ?? 'not_checked',
              },
            ]}
          />
        </Space>
      </ProCard>
    </PageContainer>
  );
}
