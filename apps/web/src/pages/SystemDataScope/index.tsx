import { PageContainer } from '@ant-design/pro-components';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAccess } from '@umijs/max';
import { Button, Descriptions, Modal, Select, Space, Table, Tabs, Tag, Typography, message, type TableColumnsType } from 'antd';
import { useState } from 'react';

import type { UserRead } from '@/services/auth';
import {
  getUserDataScope,
  listRoles,
  listUsers,
  setRoleDataScope,
  setUserDataScope,
  type DataScopeType,
  type RoleRead,
} from '@/services/iam';

const scopeOptions = [
  { label: 'GLOBAL', value: 'global' },
  { label: 'ORGANIZATION', value: 'organization' },
  { label: 'PLANT', value: 'plant' },
  { label: 'DEPARTMENT', value: 'department' },
  { label: 'SELF', value: 'self' },
] as const;

export default function SystemDataScopePage() {
  const access = useAccess();
  const queryClient = useQueryClient();
  const [selectedUser, setSelectedUser] = useState<UserRead | null>(null);
  const [overrideValue, setOverrideValue] = useState<DataScopeType | 'inherit'>('inherit');

  const roles = useQuery({ queryKey: ['iam', 'roles'], queryFn: listRoles });
  const users = useQuery({ queryKey: ['iam', 'users', 'data-scope'], queryFn: () => listUsers({ page_size: 100 }) });
  const selectedScope = useQuery({
    queryKey: ['iam', 'user-scope', selectedUser?.id],
    queryFn: async () => {
      const result = await getUserDataScope(selectedUser!.id);
      setOverrideValue(result.override_scope_type ?? 'inherit');
      return result;
    },
    enabled: Boolean(selectedUser),
  });

  const roleScopeMutation = useMutation({
    mutationFn: ({ roleId, scope }: { roleId: string; scope: DataScopeType }) => setRoleDataScope(roleId, scope),
    onSuccess: async () => {
      message.success('角色 Data Scope 已更新');
      await queryClient.invalidateQueries({ queryKey: ['iam', 'roles'] });
    },
    onError: (error: Error) => message.error(error.message),
  });

  const userScopeMutation = useMutation({
    mutationFn: () => setUserDataScope(selectedUser!.id, overrideValue === 'inherit' ? null : overrideValue),
    onSuccess: async () => {
      message.success('用户 Data Scope 覆盖已更新');
      await queryClient.invalidateQueries({ queryKey: ['iam', 'user-scope', selectedUser?.id] });
      setSelectedUser(null);
    },
    onError: (error: Error) => message.error(error.message),
  });

  const roleColumns: TableColumnsType<RoleRead> = [
    { title: '角色', dataIndex: 'name', width: 180 },
    { title: '编码', dataIndex: 'code', width: 180 },
    { title: '类型', dataIndex: 'is_system', width: 90, render: (value) => <Tag color={value ? 'purple' : 'blue'}>{value ? '系统' : '自定义'}</Tag> },
    {
      title: '角色默认范围',
      dataIndex: 'data_scope',
      width: 230,
      render: (value: DataScopeType, record) => access.canManageDataScope ? (
        <Select
          value={value}
          options={[...scopeOptions]}
          style={{ width: 180 }}
          onChange={(scope) => roleScopeMutation.mutate({ roleId: record.id, scope })}
        />
      ) : <Tag>{value.toUpperCase()}</Tag>,
    },
    { title: '权限数', dataIndex: 'permission_codes', render: (value: string[]) => value.length },
  ];

  const userColumns: TableColumnsType<UserRead> = [
    { title: '账号', dataIndex: 'username', width: 160 },
    { title: '姓名', dataIndex: 'display_name', width: 140 },
    { title: '工号', dataIndex: 'employee_no', width: 120 },
    { title: '状态', dataIndex: 'is_active', width: 90, render: (value) => <Tag color={value ? 'success' : 'default'}>{value ? '启用' : '停用'}</Tag> },
    {
      title: '操作', width: 130,
      render: (_, record) => <Button type="link" onClick={() => setSelectedUser(record)}>查看 / 设置</Button>,
    },
  ];

  return (
    <PageContainer
      title="数据权限"
      content="查看角色默认范围、用户覆盖范围与最终 Effective Scope。后端仍根据组织 / 工厂 / 部门 / SELF 边界执行查询过滤。"
      extra={<Tag color="blue">Phase 1.8</Tag>}
    >
      <Typography.Paragraph type="secondary">
        Effective Scope = 用户覆盖（若存在）优先，否则使用角色推导范围。覆盖用于收窄或调整个别账号，不应替代角色设计。
      </Typography.Paragraph>
      <Tabs
        items={[
          {
            key: 'role',
            label: '角色默认范围',
            children: <Table rowKey="id" loading={roles.isLoading} columns={roleColumns} dataSource={roles.data ?? []} pagination={false} />,
          },
          {
            key: 'user',
            label: '用户有效范围',
            children: <Table rowKey="id" loading={users.isLoading} columns={userColumns} dataSource={users.data?.items ?? []} pagination={false} />,
          },
        ]}
      />

      <Modal
        title={`Data Scope · ${selectedUser?.display_name ?? ''}`}
        open={Boolean(selectedUser)}
        onCancel={() => setSelectedUser(null)}
        onOk={() => userScopeMutation.mutate()}
        confirmLoading={userScopeMutation.isPending}
        okButtonProps={{ disabled: !access.canManageDataScope }}
        destroyOnHidden
      >
        <Descriptions
          bordered
          column={1}
          style={{ marginBottom: 20 }}
          items={[
            { key: 'role', label: 'Role Scope', children: selectedScope.data?.role_scope_type?.toUpperCase() ?? '-' },
            { key: 'override', label: 'User Override', children: selectedScope.data?.override_scope_type?.toUpperCase() ?? 'INHERIT' },
            { key: 'effective', label: 'Effective Scope', children: <Tag color="blue">{selectedScope.data?.effective_scope_type?.toUpperCase() ?? '-'}</Tag> },
            { key: 'source', label: 'Source', children: selectedScope.data?.source ?? '-' },
          ]}
        />
        <Space direction="vertical" style={{ width: '100%' }}>
          <Typography.Text strong>用户覆盖</Typography.Text>
          <Select
            value={overrideValue}
            style={{ width: '100%' }}
            onChange={(value) => setOverrideValue(value)}
            options={[{ label: '继承角色', value: 'inherit' }, ...scopeOptions]}
          />
        </Space>
      </Modal>
    </PageContainer>
  );
}
