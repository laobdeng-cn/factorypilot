import { PageContainer } from '@ant-design/pro-components';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAccess } from '@umijs/max';
import { Button, Form, Input, Modal, Select, Space, Switch, Table, Tag, message, type TableColumnsType } from 'antd';
import { useMemo, useState } from 'react';

import type { UserRead } from '@/services/auth';
import {
  createUser,
  getUserDataScope,
  getUserRoles,
  listDepartments,
  listOrganizations,
  listPlants,
  listRoles,
  listUsers,
  resetUserPassword,
  setUserDataScope,
  setUserRoles,
  updateUser,
  type DataScopeType,
} from '@/services/iam';

export default function SystemUsersPage() {
  const access = useAccess();
  const queryClient = useQueryClient();
  const [q, setQ] = useState('');
  const [editing, setEditing] = useState<UserRead | null | undefined>(undefined);
  const [roleUser, setRoleUser] = useState<UserRead | null>(null);
  const [scopeUser, setScopeUser] = useState<UserRead | null>(null);
  const [passwordUser, setPasswordUser] = useState<UserRead | null>(null);
  const [form] = Form.useForm();
  const [roleForm] = Form.useForm();
  const [scopeForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const users = useQuery({ queryKey: ['iam', 'users', q], queryFn: () => listUsers({ page_size: 100, q: q || undefined }) });
  const organizations = useQuery({ queryKey: ['iam', 'organizations'], queryFn: () => listOrganizations({ page_size: 100 }) });
  const plants = useQuery({ queryKey: ['iam', 'plants'], queryFn: () => listPlants({ page_size: 100 }) });
  const departments = useQuery({ queryKey: ['iam', 'departments'], queryFn: () => listDepartments({ page_size: 100 }) });
  const roles = useQuery({ queryKey: ['iam', 'roles'], queryFn: listRoles, enabled: Boolean(access.canReadRbac || access.canReadUserRoles) });
  const userRoles = useQuery({ queryKey: ['iam', 'user-roles', roleUser?.id], queryFn: () => getUserRoles(roleUser!.id), enabled: Boolean(roleUser && access.canReadUserRoles) });
  const userScope = useQuery({ queryKey: ['iam', 'user-scope', scopeUser?.id], queryFn: () => getUserDataScope(scopeUser!.id), enabled: Boolean(scopeUser && access.canReadDataScope) });

  const orgMap = useMemo(() => new Map((organizations.data?.items ?? []).map((x) => [x.id, x.name])), [organizations.data]);
  const plantMap = useMemo(() => new Map((plants.data?.items ?? []).map((x) => [x.id, x.name])), [plants.data]);
  const deptMap = useMemo(() => new Map((departments.data?.items ?? []).map((x) => [x.id, x.name])), [departments.data]);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['iam', 'users'] });

  const saveUser = useMutation({
    mutationFn: async (values: Record<string, unknown>) => editing ? updateUser(editing.id, values) : createUser(values as Parameters<typeof createUser>[0]),
    onSuccess: async () => { message.success('用户保存成功'); setEditing(undefined); form.resetFields(); await refresh(); },
    onError: (e: Error) => message.error(e.message),
  });
  const saveRoles = useMutation({
    mutationFn: (roleIds: string[]) => setUserRoles(roleUser!.id, roleIds),
    onSuccess: async () => { message.success('角色分配成功'); await queryClient.invalidateQueries({ queryKey: ['iam', 'user-roles', roleUser?.id] }); setRoleUser(null); },
    onError: (e: Error) => message.error(e.message),
  });
  const saveScope = useMutation({
    mutationFn: (scope: DataScopeType | null) => setUserDataScope(scopeUser!.id, scope),
    onSuccess: async () => { message.success('数据范围已更新'); await queryClient.invalidateQueries({ queryKey: ['iam', 'user-scope', scopeUser?.id] }); setScopeUser(null); },
    onError: (e: Error) => message.error(e.message),
  });
  const savePassword = useMutation({
    mutationFn: (value: string) => resetUserPassword(passwordUser!.id, value),
    onSuccess: () => { message.success('密码已重置，现有会话将失效'); setPasswordUser(null); passwordForm.resetFields(); },
    onError: (e: Error) => message.error(e.message),
  });

  const openEdit = (record?: UserRead | null) => {
    setEditing(record ?? null);
    form.resetFields();
    if (record) form.setFieldsValue(record);
    else form.setFieldsValue({ is_active: true });
  };

  const columns: TableColumnsType<UserRead> = [
    { title: '账号', dataIndex: 'username', width: 140 },
    { title: '姓名', dataIndex: 'display_name', width: 120 },
    { title: '工号', dataIndex: 'employee_no', width: 100 },
    { title: '组织', dataIndex: 'organization_id', render: (v) => orgMap.get(v) ?? v },
    { title: '工厂', dataIndex: 'primary_plant_id', render: (v) => v ? plantMap.get(v) ?? v : '-' },
    { title: '部门', dataIndex: 'department_id', render: (v) => v ? deptMap.get(v) ?? v : '-' },
    { title: '状态', dataIndex: 'is_active', width: 80, render: (v) => <Tag color={v ? 'success' : 'default'}>{v ? '启用' : '停用'}</Tag> },
    {
      title: '操作', fixed: 'right', width: 260,
      render: (_, record) => <Space size={4}>
        <Button type="link" disabled={!access.canManageUsers} onClick={() => openEdit(record)}>编辑</Button>
        <Button type="link" disabled={!access.canReadUserRoles} onClick={() => { setRoleUser(record); roleForm.setFieldsValue({ role_ids: undefined }); }}>角色</Button>
        <Button type="link" disabled={!access.canReadDataScope} onClick={() => setScopeUser(record)}>数据范围</Button>
        <Button type="link" disabled={!access.canManageUsers} onClick={() => setPasswordUser(record)}>重置密码</Button>
      </Space>,
    },
  ];

  return (
    <PageContainer title="用户管理" content="管理用户身份、所属组织、角色分配与个人 Data Scope 覆盖。" extra={<Tag color="blue">Phase 1.8</Tag>}>
      <Space style={{ marginBottom: 16 }}>
        <Input.Search allowClear placeholder="搜索账号 / 姓名 / 工号" onSearch={setQ} style={{ width: 320 }} />
        <Button type="primary" disabled={!access.canManageUsers} onClick={() => openEdit(null)}>新建用户</Button>
      </Space>
      <Table rowKey="id" loading={users.isLoading} columns={columns} dataSource={users.data?.items ?? []} scroll={{ x: 1300 }} pagination={false} />

      <Modal title={editing ? '编辑用户' : '新建用户'} open={editing !== undefined} onCancel={() => setEditing(undefined)} onOk={() => form.submit()} confirmLoading={saveUser.isPending} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={(values) => saveUser.mutate(values)}>
          {!editing && <Form.Item name="organization_id" label="组织" rules={[{ required: true }]}><Select options={(organizations.data?.items ?? []).map((x) => ({ label: `${x.name} (${x.code})`, value: x.id }))} /></Form.Item>}
          <Form.Item name="primary_plant_id" label="主要工厂"><Select allowClear options={(plants.data?.items ?? []).map((x) => ({ label: `${x.name} (${x.code})`, value: x.id }))} /></Form.Item>
          <Form.Item name="department_id" label="部门"><Select allowClear options={(departments.data?.items ?? []).map((x) => ({ label: `${x.name} (${x.code})`, value: x.id }))} /></Form.Item>
          <Form.Item name="username" label="账号" rules={[{ required: true, min: 3 }]}><Input /></Form.Item>
          <Form.Item name="employee_no" label="工号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="display_name" label="姓名" rules={[{ required: true, min: 2 }]}><Input /></Form.Item>
          <Form.Item name="email" label="邮箱"><Input /></Form.Item>
          <Form.Item name="mobile" label="手机"><Input /></Form.Item>
          {!editing && <Form.Item name="password" label="初始密码" rules={[{ required: true, min: 12 }]}><Input.Password /></Form.Item>}
          <Form.Item name="is_active" label="启用" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>

      <Modal title={`角色分配 · ${roleUser?.display_name ?? ''}`} open={Boolean(roleUser)} onCancel={() => setRoleUser(null)} onOk={() => roleForm.submit()} confirmLoading={saveRoles.isPending} okButtonProps={{ disabled: !access.canManageUserRoles }} destroyOnHidden>
        <Form form={roleForm} layout="vertical" onFinish={({ role_ids }) => saveRoles.mutate(role_ids ?? [])} initialValues={{ role_ids: userRoles.data?.role_ids ?? [] }}>
          <Form.Item name="role_ids" label="角色">
            <Select mode="multiple" loading={roles.isLoading || userRoles.isLoading} options={(roles.data ?? []).map((r) => ({ label: `${r.name} (${r.code})`, value: r.id }))} />
          </Form.Item>
          {userRoles.data && <Tag color="blue">当前：{userRoles.data.role_codes.join(', ') || '无角色'}</Tag>}
        </Form>
      </Modal>

      <Modal title={`数据范围 · ${scopeUser?.display_name ?? ''}`} open={Boolean(scopeUser)} onCancel={() => setScopeUser(null)} onOk={() => scopeForm.submit()} confirmLoading={saveScope.isPending} okButtonProps={{ disabled: !access.canManageDataScope }} destroyOnHidden>
        <Form form={scopeForm} layout="vertical" onFinish={({ scope_type }) => saveScope.mutate(scope_type === 'inherit' ? null : scope_type)}>
          <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
            <div>角色范围：<Tag>{userScope.data?.role_scope_type ?? '-'}</Tag></div>
            <div>有效范围：<Tag color="blue">{userScope.data?.effective_scope_type ?? '-'}</Tag></div>
            <div>来源：{userScope.data?.source ?? '-'}</div>
          </Space>
          <Form.Item name="scope_type" label="用户覆盖" initialValue={userScope.data?.override_scope_type ?? 'inherit'}>
            <Select options={[
              { label: '继承角色', value: 'inherit' }, { label: 'GLOBAL', value: 'global' }, { label: 'ORGANIZATION', value: 'organization' }, { label: 'PLANT', value: 'plant' }, { label: 'DEPARTMENT', value: 'department' }, { label: 'SELF', value: 'self' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title={`重置密码 · ${passwordUser?.display_name ?? ''}`} open={Boolean(passwordUser)} onCancel={() => setPasswordUser(null)} onOk={() => passwordForm.submit()} confirmLoading={savePassword.isPending} destroyOnHidden>
        <Form form={passwordForm} layout="vertical" onFinish={({ password }) => savePassword.mutate(password)}>
          <Form.Item name="password" label="新密码" rules={[{ required: true, min: 12 }]}><Input.Password /></Form.Item>
        </Form>
      </Modal>
    </PageContainer>
  );
}
