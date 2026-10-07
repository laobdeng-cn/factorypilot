import { Button, Result } from 'antd';

export default function NotFoundPage() {
  const goHome = () => {
    window.location.assign('/dashboard');
  };

  return (
    <Result
      status="404"
      title="404"
      subTitle="页面不存在或尚未开放。"
      extra={
        <Button type="primary" onClick={goHome}>
          返回智造总览
        </Button>
      }
    />
  );
}
