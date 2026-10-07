import { PageContainer } from '@ant-design/pro-components';
import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Card,
  Col,
  Progress,
  Row,
  Space,
  Statistic,
  Tag,
  Typography,
} from 'antd';

import { getLiveness } from '@/services/factorypilot';
import { useAppStore } from '@/stores/useAppStore';

const metrics = [
  { title: 'OTD 准时交付率', value: 94.7, suffix: '%', precision: 1 },
  { title: '风险订单', value: 12, suffix: '单' },
  { title: '物料短缺', value: 27, suffix: '项' },
  { title: '当前异常', value: 8, suffix: '项' },
];

const lineLoads = [
  { name: 'SMT-L1', value: 87 },
  { name: 'SMT-L2', value: 74 },
  { name: 'Assembly-L3', value: 96 },
];

export default function DashboardPage() {
  const companyName = useAppStore((state) => state.companyName);
  const currentPlant = useAppStore((state) => state.currentPlant);
  const health = useQuery({
    queryKey: ['backend-liveness'],
    queryFn: getLiveness,
    retry: false,
    refetchInterval: 15_000,
  });

  return (
    <PageContainer
      title="智造总览"
      content={`${companyName} · ${currentPlant}`}
      extra={[
        <Tag color="processing" key="environment">
          Phase 0 Mock Data
        </Tag>,
      ]}
    >
      <Alert
        showIcon
        type="info"
        message="FactoryPilot 前端工程基线已建立"
        description="当前 Dashboard 使用 Mock 数据验证 Ant Design Pro 布局与 FastAPI 联调能力；真实制造业务数据将在后续 Phase 接入。"
        style={{ marginBottom: 16 }}
      />

      <Row gutter={[16, 16]}>
        {metrics.map((metric) => (
          <Col key={metric.title} xs={24} sm={12} xl={6}>
            <Card>
              <Statistic
                precision={metric.precision}
                suffix={metric.suffix}
                title={metric.title}
                value={metric.value}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} xl={14}>
          <Card title="产线负载">
            <Space direction="vertical" size={20} style={{ width: '100%' }}>
              {lineLoads.map((line) => (
                <div key={line.name}>
                  <Space style={{ marginBottom: 6 }}>
                    <Typography.Text strong>{line.name}</Typography.Text>
                    <Typography.Text type="secondary">{line.value}%</Typography.Text>
                  </Space>
                  <Progress
                    percent={line.value}
                    showInfo={false}
                    status={line.value >= 95 ? 'exception' : 'normal'}
                  />
                </div>
              ))}
            </Space>
          </Card>
        </Col>

        <Col xs={24} xl={10}>
          <Card title="平台基础状态">
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              <div>
                <Typography.Text type="secondary">FastAPI</Typography.Text>
                <div style={{ marginTop: 6 }}>
                  {health.isFetching ? (
                    <Tag color="processing">检查中</Tag>
                  ) : health.data ? (
                    <Tag color="success">ONLINE · {health.data.version}</Tag>
                  ) : (
                    <Tag color="error">OFFLINE</Tag>
                  )}
                </div>
              </div>
              <div>
                <Typography.Text type="secondary">当前工程阶段</Typography.Text>
                <Typography.Paragraph style={{ marginBottom: 0, marginTop: 6 }}>
                  Phase 0.3 · Ant Design Pro Frontend Foundation
                </Typography.Paragraph>
              </div>
              <div>
                <Typography.Text type="secondary">下一阶段</Typography.Text>
                <Typography.Paragraph style={{ marginBottom: 0, marginTop: 6 }}>
                  FactoryPilot Design Tokens、完整导航与正式 Dashboard 视觉
                </Typography.Paragraph>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </PageContainer>
  );
}
