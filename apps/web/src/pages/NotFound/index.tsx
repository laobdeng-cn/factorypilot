import { history } from '@umijs/max';
import { Button, Result } from 'antd';

export default function NotFoundPage() {
  return (
    <Result
      status="404"
      title="404"
      subTitle="页面不存在或尚未开放。"
      extra={
        <Button type="primary" onClick={() => history.push('/dashboard')}>
          返回智造总览
        </Button>
      }
    />
  );
}
