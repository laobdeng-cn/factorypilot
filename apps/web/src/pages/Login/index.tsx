import { LockOutlined, SafetyCertificateOutlined, UserOutlined } from '@ant-design/icons';
import { history, useModel } from '@umijs/max';
import { Alert, Button, Card, Form, Input, Space, Tag, Typography } from 'antd';
import { useState } from 'react';

import { ApiError, getCurrentUser, login } from '@/services/auth';

import styles from './index.less';

interface LoginFormValues {
  username: string;
  password: string;
}

export default function LoginPage() {
  const { setInitialState } = useModel('@@initialState');
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFinish = async (values: LoginFormValues) => {
    setSubmitting(true);
    setErrorMessage(null);

    try {
      await login(values.username.trim(), values.password);
      const currentUser = await getCurrentUser();
      await setInitialState({ currentUser });

      const params = new URLSearchParams(history.location.search);
      const redirect = params.get('redirect');
      history.replace(redirect?.startsWith('/') && redirect !== '/login' ? redirect : '/dashboard');
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('登录失败，请检查 API 服务与网络连接。');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className={styles.page}>
      <section className={styles.brandPanel}>
        <div className={styles.brandMark}>FP</div>
        <Typography.Title level={1} className={styles.brandTitle}>
          FactoryPilot
        </Typography.Title>
        <Typography.Paragraph className={styles.brandSubtitle}>
          智造协同决策平台
        </Typography.Paragraph>
        <div className={styles.brandCopy}>
          <Typography.Title level={3}>让制造运营、供应链与 AI 决策使用同一套可信上下文。</Typography.Title>
          <Typography.Paragraph>
            Phase 1 已建立组织、身份、RBAC、数据范围与安全审计底座，本阶段开始接入真实前端身份态。
          </Typography.Paragraph>
        </div>
        <Space wrap>
          <Tag icon={<SafetyCertificateOutlined />}>JWT Session</Tag>
          <Tag>RBAC</Tag>
          <Tag>Data Scope</Tag>
          <Tag>Audit Ready</Tag>
        </Space>
      </section>

      <section className={styles.formPanel}>
        <Card className={styles.loginCard} bordered={false}>
          <div className={styles.cardHeader}>
            <Typography.Title level={2}>登录 FactoryPilot</Typography.Title>
            <Typography.Text type="secondary">使用平台账号进入当前组织工作区。</Typography.Text>
          </div>

          {errorMessage ? (
            <Alert className={styles.alert} type="error" showIcon message={errorMessage} />
          ) : null}

          <Form<LoginFormValues>
            layout="vertical"
            size="large"
            requiredMark={false}
            onFinish={handleFinish}
            initialValues={{ username: 'admin.fp' }}
          >
            <Form.Item
              label="账号"
              name="username"
              rules={[{ required: true, message: '请输入账号' }]}
            >
              <Input autoComplete="username" prefix={<UserOutlined />} placeholder="例如 admin.fp" />
            </Form.Item>
            <Form.Item
              label="密码"
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                autoComplete="current-password"
                prefix={<LockOutlined />}
                placeholder="请输入密码"
              />
            </Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              登录
            </Button>
          </Form>

          <Typography.Paragraph type="secondary" className={styles.securityHint}>
            登录后由服务端会话、权限集合与 Data Scope 共同决定可访问资源。前端菜单隐藏不替代后端授权。
          </Typography.Paragraph>
        </Card>
      </section>
    </main>
  );
}
