import { PageContainer } from '@ant-design/pro-components';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAccess } from '@umijs/max';
import { Button, Checkbox, Divider, Form, Input, Modal, Select, Space, Switch, Table, Tag, Typography, message, type TableColumnsType } from 'antd';
import { useMemo, useState } from 'react';

import {
  createRole,
  listPermissions,
  listRoles,
  setRoleDataScope,
  setRolePermissions,
  updateRole,
  type DataScopeType,
  type PermissionRead,
  type RoleRead,
} from '@/services/iam';

const scopeOptions = ['global', 'organization', 'plant', 'department', 'self'].map((value) => ({ label: value.toUpperCase(), value }));

export default function SystemRolesPage() {
  const access = useAccess();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [editing, setEditing] = useState<RoleRead | null | undefined>(undefined);
  const [permissionRole, setPermissionRole] = useState<RoleRead | null>(null);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);

  const roles = useQuery({ queryKey: ['iam', 'roles'], queryFn: listRoles });
  const permissions = useQuery({ queryKey: ['iam', 'permissions'], queryFn: listPermissions });

  const groupedPermissions = useMemo(() => {
    const groups = new Map<string, PermissionRead[]>();
    (permissions.data ?? []).forEach((permission) => {
      const items = groups.get(permission.module) ?? [];
      items.push(permission);
      groups.set(permission.module, items);
    });
    return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [permissions.data]);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['iam', 'roles'] });
  const saveRole = useMutation({
    mutationFn: (values: Record<string, unknown>) => editing ? updateRole(editing.id, values) : createRole(values as Parameters<typeof createRole>[0]),
    onSuccess: async () => { message.success('角色保存成功'); setEditing(undefined); form.resetFields(); await refresh(); },
    onError: (e: Error) => message.error(e.message),
  });
  const savePermissions = useMutation({
    mutationFn: () => setRolePermissions(permissionRole!.id, selectedPermissions),
    onSuccess: async () => { message.success('角色权限已更新'); setPermissionRole(null); await refresh(); },
    onError: (e: Error) => message.error(e.message),
  });
  const saveScope = useMutation({
    mutationFn: ({ id, scope }: { id: string; scope: DataScopeType }) => setRoleDataScope(id, scope),
    onSuccess: async () => { message.success('角色数据范围已更新'); await refresh(); },
    onError: (e: Error) => message.error(e.message),
  });

  const openEdit = (record?: RoleRead | null) => {
    setEditing(record ?? null);
    form.resetFields();
    if (record) form.setFieldsValue(record);
    else form.setFieldsValue({ data_scope: 'self', is_active: true });
  };

  const columns: TableColumnsType<RoleRead> = [
    { title: '角色编码', dataIndex: 'code', width: 170 },
    { title: '角色名称', dataIndex: 'name', width: 150 },
    { title: '类型', dataIndex: 'is_system', width: 90, render: (v) => <Tag color={v ? 'purple' : 'blue'}>{v ? '系统' : '自定义'}</Tag> },
    { title: '数据范围', dataIndex: 'data_scope', width: 180, render: (value: DataScopeType, record) => access.canManageDataScope && !record.is_system ? <Select size="small" value={value} style={{ width: 150 }} options={scopeOptions} onChange={(scope) => saveScope.mutate({ id: record.id, scope })} /> : <Tag>{value.toUpperCase()}</Tag> },
    { title: '权限数', dataIndex: 'permission_codes', width: 90, render: (v: string[]) => v.length },
    { title: '状态', dataIndex: 'is_active', width: 80, render: (v) => <Tag color={v ? 'success' : 'default'}>{v ? '启用' : '停用'}</Tag> },
    { title: '说明', dataIndex: 'description', ellipsis: true, render: (v) => v || '-' },
    {
      title: '操作', width: 160, fixed: 'right', render: (_, record) => <Space>
        <Button type="link" disabled={!access.canManageRbac || record.is_system} onClick={() => openEdit(record)}>编辑</Button>
        <Button type="link" disabled={!access.canManageRbac} onClick={() => { setPermissionRole(record); setSelectedPermissions(record.permission_codes); }}>权限</Button>
      </Space>,
    },
  ];

  return (
    <PageContainer title="角色与权限" content="维护角色、权限集合和角色默认 Data Scope。系统角色受保护，不允许直接修改基础属性。" extra={<Tag color="blue">Phase 1.8</Tag>}>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" disabled={!access.canManageRbac} onClick={() => openEdit(null)}>新建角色</Button>
        <Typography.Text type="secondary">权限仍由后端 require_permission 强制校验。</Typography.Text>
      </Space>
      <Table rowKey="id" loading={roles.isLoading} columns={columns} dataSource={roles.data ?? []} pagination={false} scroll={{ x: 1100 }} />

      <Modal title={editing ? '编辑角色' : '新建角色'} open={editing !== undefined} onCancel={() => setEditing(undefined)} onOk={() => form.submit()} confirmLoading={saveRole.isPending} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={(values) => saveRole.mutate(values)}>
          {!editing && <Form.Item name="code" label="角色编码" rules={[{ required: true, min: 3 }]}><Input placeholder="planner / quality_manager" /></Form.Item>}
          <Form.Item name="name" label="角色名称" rules={[{ required: true, min: 2 }]}><Input /></Form.Item>
          <Form.Item name="description" label="说明"><Input.TextArea rows={3} /></Form.Item>
          {!editing && <Form.Item name="data_scope" label="默认数据范围" rules={[{ required: true }]}><Select options={scopeOptions} /></Form.Item>}
          {editing && <Form.Item name="is_active" label="启用" valuePropName="checked"><Switch /></Form.Item>}
        </Form>
      </Modal>

      <Modal width={760} title={`权限配置 · ${permissionRole?.name ?? ''}`} open={Boolean(permissionRole)} onCancel={() => setPermissionRole(null)} onOk={() => savePermissions.mutate()} confirmLoading={savePermissions.isPending} okButtonProps={{ disabled: !access.canManageRbac }} destroyOnHidden>
        {groupedPermissions.map(([module, items]) => (
          <div key={module}>
            <Divider orientation="left">{module}</Divider>
            <Checkbox.Group value={selectedPermissions} onChange={(values) => setSelectedPermissions(values as string[])} style={{ width: '100%' }}>
              <Space direction="vertical">
                {items.map((permission) => <Checkbox key={permission.code} value={permission.code}>{permission.name} <Typography.Text type="secondary">{permission.code}</Typography.Text></Checkbox>)}
              </Space>
            </Checkbox.Group>
          </div>
        ))}
      </Modal>
    </PageContainer>
  );
}
