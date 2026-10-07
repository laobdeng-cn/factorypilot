import {
  AlertOutlined,
  ArrowDownOutlined,
  ArrowUpOutlined,
  CheckCircleFilled,
  ClockCircleOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  WarningFilled,
} from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { useQuery } from '@tanstack/react-query';
import {
  Badge,
  Button,
  Card,
  Col,
  Progress,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd';
import type { TableColumnsType } from 'antd';
import ReactECharts from 'echarts-for-react';

import { getLiveness } from '@/services/factorypilot';
import { useAppStore } from '@/stores/useAppStore';

interface RiskOrder {
  key: string;
  orderNo: string;
  customer: string;
  product: string;
  dueDate: string;
  eta: string;
  risk: '高' | '中';
}

interface KpiMetric {
  title: string;
  value: number;
  suffix: string;
  precision?: number;
  trend: number;
  tone: 'blue' | 'green' | 'orange' | 'red';
}

const kpis: KpiMetric[] = [
  { title: 'OTD 准时交付率', value: 94.7, suffix: '%', precision: 1, trend: 1.8, tone: 'blue' },
  { title: '计划达成率', value: 92.3, suffix: '%', precision: 1, trend: 0.9, tone: 'green' },
  { title: '风险订单', value: 12, suffix: '单', trend: -3, tone: 'orange' },
  { title: '物料短缺', value: 27, suffix: '项', trend: -5, tone: 'orange' },
  { title: '延期采购', value: 8, suffix: '单', trend: 2, tone: 'red' },
  { title: '待处理异常', value: 8, suffix: '项', trend: -2, tone: 'red' },
];

const lineLoads = [
  { name: 'SMT-L1', value: 87, status: '运行中' },
  { name: 'SMT-L2', value: 74, status: '运行中' },
  { name: 'Assembly-L3', value: 96, status: '高负载' },
  { name: 'Test-L4', value: 68, status: '运行中' },
];

const riskOrders: RiskOrder[] = [
  {
    key: '1',
    orderNo: 'SO202610070032',
    customer: '深圳远航科技',
    product: 'GP100 100W GaN Charger',
    dueDate: '10-22',
    eta: '10-25',
    risk: '高',
  },
  {
    key: '2',
    orderNo: 'SO202610060018',
    customer: '东莞启明电子',
    product: 'IPM-240 工业电源模块',
    dueDate: '10-19',
    eta: '10-21',
    risk: '高',
  },
  {
    key: '3',
    orderNo: 'SO202610050071',
    customer: '广州智联设备',
    product: 'SC-300 智能控制器',
    dueDate: '10-24',
    eta: '10-25',
    risk: '中',
  },
  {
    key: '4',
    orderNo: 'SO202610040026',
    customer: '佛山恒锐自动化',
    product: 'PA120 电源适配器',
    dueDate: '10-20',
    eta: '10-21',
    risk: '中',
  },
];

const riskOrderColumns: TableColumnsType<RiskOrder> = [
  { title: '订单号', dataIndex: 'orderNo', width: 160 },
  { title: '客户', dataIndex: 'customer', width: 130 },
  { title: '产品', dataIndex: 'product', ellipsis: true },
  { title: '承诺交期', dataIndex: 'dueDate', width: 90 },
  { title: '预测 ETA', dataIndex: 'eta', width: 90 },
  {
    title: '风险',
    dataIndex: 'risk',
    width: 76,
    render: (risk) => <Tag color={risk === '高' ? 'error' : 'warning'}>{risk}</Tag>,
  },
];

const deliveryOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: ['计划交付', '实际/预测交付'], top: 0, right: 8 },
  grid: { left: 36, right: 18, top: 42, bottom: 28 },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['10/01', '10/02', '10/03', '10/04', '10/05', '10/06', '10/07'],
    axisLine: { lineStyle: { color: '#dbe3ec' } },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#eef2f7' } },
  },
  series: [
    {
      name: '计划交付',
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: [42, 46, 44, 52, 48, 55, 51],
      lineStyle: { width: 2 },
      areaStyle: { opacity: 0.06 },
    },
    {
      name: '实际/预测交付',
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: [40, 45, 43, 49, 47, 53, 48],
      lineStyle: { width: 2 },
    },
  ],
};

const shortageOption = {
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 78, right: 18, top: 12, bottom: 24 },
  xAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#eef2f7' } },
  },
  yAxis: {
    type: 'category',
    data: ['GaN IC', 'MLCC', 'MOSFET', 'USB-C Conn.', 'PCB'],
    axisTick: { show: false },
    axisLine: { show: false },
  },
  series: [
    {
      type: 'bar',
      barWidth: 15,
      data: [1800, 1260, 980, 720, 560],
      itemStyle: { borderRadius: [0, 4, 4, 0] },
    },
  ],
};

const supplyAlerts = [
  { level: 'critical', title: 'GaN IC 关键物料延期', detail: '东莞华芯电子 · ETA 10-18 → 10-25', impact: '影响 6 个订单' },
  { level: 'warning', title: 'MLCC 库存低于安全库存', detail: 'MAT-MLCC-104 · 可用库存 4,600 pcs', impact: '影响 3 个工单' },
  { level: 'warning', title: 'Assembly-L3 产能接近上限', detail: '未来 48h 负载 96%', impact: '存在插单冲突' },
  { level: 'info', title: '供应商交付绩效下降', detail: '惠州鑫源电子 · OTD 82.1%', impact: '连续 3 周下降' },
];

const aiDecisions = [
  {
    id: 'DEC-20261007-031',
    title: '紧急订单 SO202610070032 交付调整',
    summary: '建议启用备选供应商 + 切换 SMT-L3，预计满足 10-22 交付，新增成本 ¥18,420。',
    risk: '低风险',
    status: '待审批',
  },
  {
    id: 'DEC-20261007-028',
    title: 'GaN IC 供应延期影响处置',
    summary: '已识别 6 个受影响订单，推荐拆分采购并优先保障 A 类客户订单。',
    risk: '中风险',
    status: '分析完成',
  },
  {
    id: 'DEC-20261007-024',
    title: 'Assembly-L3 高负载再排程',
    summary: '建议将 WO-10482 转移至 Assembly-L2，可释放 11.5 小时关键产能。',
    risk: '低风险',
    status: '待审批',
  },
];

function Trend({ value }: { value: number }) {
  const positive = value >= 0;
  return (
    <span className={positive ? 'fp-trend fp-trend-up' : 'fp-trend fp-trend-down'}>
      {positive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
      {Math.abs(value)}%
    </span>
  );
}

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
      title="生产运营总览"
      content={`${companyName} · ${currentPlant}`}
      extra={[
        <Tag key="plant" color="blue">东莞制造基地</Tag>,
        <Tag key="api" color={health.data ? 'success' : 'error'}>
          API {health.data ? 'ONLINE' : 'OFFLINE'}
        </Tag>,
      ]}
    >
      <div className="fp-dashboard">
        <div className="fp-overview-strip">
          <div>
            <Typography.Text className="fp-overview-kicker">今日运营态势</Typography.Text>
            <Typography.Title level={4} className="fp-overview-title">
              交付总体稳定，供应链存在 3 项重点风险
            </Typography.Title>
            <Typography.Text type="secondary">
              截至 10 月 8 日 03:00，系统监测 128 个在制订单、27 项物料短缺与 8 个开放异常。
            </Typography.Text>
          </div>
          <Space size={10} wrap>
            <Tag icon={<CheckCircleFilled />} color="success">生产运行正常</Tag>
            <Tag icon={<WarningFilled />} color="warning">3 项需关注</Tag>
            <Button type="primary" icon={<RobotOutlined />}>查看 AI 决策</Button>
          </Space>
        </div>

        <Row gutter={[14, 14]}>
          {kpis.map((metric) => (
            <Col key={metric.title} xs={24} sm={12} lg={8} xxl={4}>
              <Card className={`fp-kpi-card fp-kpi-${metric.tone}`}>
                <Statistic
                  precision={metric.precision}
                  suffix={metric.suffix}
                  title={metric.title}
                  value={metric.value}
                />
                <div className="fp-kpi-footer">
                  <Trend value={metric.trend} />
                  <Typography.Text type="secondary">较昨日</Typography.Text>
                </div>
              </Card>
            </Col>
          ))}
        </Row>

        <Row gutter={[14, 14]} className="fp-section-row">
          <Col xs={24} xl={15}>
            <Card title="订单交付趋势" extra={<Typography.Text type="secondary">近 7 日</Typography.Text>}>
              <ReactECharts option={deliveryOption} style={{ height: 278 }} />
            </Card>
          </Col>
          <Col xs={24} xl={9}>
            <Card title="产线负载" extra={<Badge status="processing" text="实时态势" />}>
              <Space direction="vertical" size={18} style={{ width: '100%' }}>
                {lineLoads.map((line) => (
                  <div key={line.name}>
                    <div className="fp-line-head">
                      <Space size={8}>
                        <Typography.Text strong>{line.name}</Typography.Text>
                        <Tag color={line.value >= 95 ? 'error' : 'processing'} bordered={false}>
                          {line.status}
                        </Tag>
                      </Space>
                      <Typography.Text strong>{line.value}%</Typography.Text>
                    </div>
                    <Progress
                      percent={line.value}
                      showInfo={false}
                      status={line.value >= 95 ? 'exception' : 'normal'}
                      strokeWidth={8}
                    />
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
        </Row>

        <Row gutter={[14, 14]} className="fp-section-row">
          <Col xs={24} xl={16}>
            <Card title="重点风险订单" extra={<Button type="link">查看全部 12 单</Button>}>
              <Table<RiskOrder>
                columns={riskOrderColumns}
                dataSource={riskOrders}
                pagination={false}
                size="small"
                scroll={{ x: 760 }}
              />
            </Card>
          </Col>
          <Col xs={24} xl={8}>
            <Card title="物料短缺 Top 5" extra={<Tag color="warning">27 项短缺</Tag>}>
              <ReactECharts option={shortageOption} style={{ height: 248 }} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[14, 14]} className="fp-section-row">
          <Col xs={24} xl={10}>
            <Card title="供应链风险" extra={<Button type="link">异常中心</Button>}>
              <div className="fp-alert-list">
                {supplyAlerts.map((alert) => (
                  <div className="fp-alert-item" key={alert.title}>
                    <div className={`fp-alert-icon fp-alert-${alert.level}`}>
                      {alert.level === 'critical' ? <AlertOutlined /> : <ClockCircleOutlined />}
                    </div>
                    <div className="fp-alert-content">
                      <div className="fp-alert-title">{alert.title}</div>
                      <Typography.Text type="secondary">{alert.detail}</Typography.Text>
                    </div>
                    <Tag color={alert.level === 'critical' ? 'error' : alert.level === 'warning' ? 'warning' : 'blue'}>
                      {alert.impact}
                    </Tag>
                  </div>
                ))}
              </div>
            </Card>
          </Col>
          <Col xs={24} xl={14}>
            <Card
              title={
                <Space>
                  <RobotOutlined style={{ color: '#1677ff' }} />
                  AI 决策中心
                </Space>
              }
              extra={<Button type="primary" ghost>进入 Decision Center</Button>}
            >
              <div className="fp-decision-list">
                {aiDecisions.map((decision) => (
                  <div className="fp-decision-item" key={decision.id}>
                    <div className="fp-decision-main">
                      <Space size={8} wrap>
                        <Typography.Text strong>{decision.title}</Typography.Text>
                        <Tag color={decision.risk === '低风险' ? 'success' : 'warning'}>{decision.risk}</Tag>
                      </Space>
                      <Typography.Paragraph type="secondary" className="fp-decision-summary">
                        {decision.summary}
                      </Typography.Paragraph>
                      <Typography.Text className="fp-decision-id">{decision.id}</Typography.Text>
                    </div>
                    <div className="fp-decision-action">
                      <Tag color={decision.status === '待审批' ? 'processing' : 'blue'}>{decision.status}</Tag>
                      <Button size="small">查看</Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </Col>
        </Row>

        <Card className="fp-system-strip">
          <Space size={24} wrap>
            <Space><SafetyCertificateOutlined className="fp-system-icon" /><Typography.Text strong>平台运行状态</Typography.Text></Space>
            <Badge status={health.data ? 'success' : 'error'} text={`FastAPI ${health.data?.version ?? 'offline'}`} />
            <Badge status="success" text="Mock Factory Data Ready" />
            <Badge status="processing" text="Phase 0.4 UI Baseline" />
          </Space>
        </Card>
      </div>
    </PageContainer>
  );
}
