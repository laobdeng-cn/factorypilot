import { PageContainer } from '@ant-design/pro-components';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAccess } from '@umijs/max';
import {
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Switch,
  Table,
  Tabs,
  Tag,
  Tree,
  Typography,
  message,
  type TableColumnsType,
  type TreeDataNode,
} from 'antd';
import { useMemo, useState } from 'react';

import {
  createDepartment,
  createOrganization,
  createPlant,
  listDepartments,
  listOrganizations,
  listPlants,
  updateDepartment,
  updateOrganization,
  updatePlant,
  type DepartmentRead,
  type OrganizationRead,
  type PlantRead,
} from '@/services/iam';

type EntityKind = 'organization' | 'plant' | 'department';
type EditableRecord = OrganizationRead | PlantRead | DepartmentRead;

const kindLabel: Record<EntityKind, string> = {
  organization: '组织',
  plant: '工厂',
  department: '部门',
};

function ActiveTag({ active }: { active: boolean }) {
  return <Tag color={active ? 'success' : 'default'}>{active ? '启用' : '停用'}</Tag>;
}

export default function SystemOrganizationPage() {
  const access = useAccess();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [modal, setModal] = useState<{ kind: EntityKind; record?: EditableRecord } | null>(null);

  const organizations = useQuery({ queryKey: ['iam', 'organizations'], queryFn: () => listOrganizations({ page_size: 100 }) });
  const plants = useQuery({ queryKey: ['iam', 'plants'], queryFn: () => listPlants({ page_size: 100 }) });
  const departments = useQuery({ queryKey: ['iam', 'departments'], queryFn: () => listDepartments({ page_size: 100 }) });

  const orgItems = organizations.data?.items ?? [];
  const plantItems = plants.data?.items ?? [];
  const departmentItems = departments.data?.items ?? [];

  const orgName = useMemo(() => new Map(orgItems.map((item) => [item.id, item.name])), [orgItems]);
  const plantName = useMemo(() => new Map(plantItems.map((item) => [item.id, item.name])), [plantItems]);
  const departmentName = useMemo(() => new Map(departmentItems.map((item) => [item.id, item.name])), [departmentItems]);

  const treeData = useMemo<TreeDataNode[]>(() => {
    const buildDepartments = (organizationId: string, plantId: string | null, parentId: string | null): TreeDataNode[] =>
      departmentItems
        .filter((item) => item.organization_id === organizationId && item.plant_id === plantId && item.parent_id === parentId)
        .sort((a, b) => a.sort_order - b.sort_order)
        .map((item) => ({
          key: `department:${item.id}`,
          title: `${item.name} · ${item.code}`,
          children: buildDepartments(organizationId, plantId, item.id),
        }));

    return orgItems.map((organization) => ({
      key: `organization:${organization.id}`,
      title: `${organization.name} · ${organization.code}`,
      children: [
        ...buildDepartments(organization.id, null, null),
        ...plantItems.filter((plant) => plant.organization_id === organization.id).map((plant) => ({
          key: `plant:${plant.id}`,
          title: `${plant.name} · ${plant.code}`,
          children: buildDepartments(organization.id, plant.id, null),
        })),
      ],
    }));
  }, [departmentItems, orgItems, plantItems]);

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['iam', 'organizations'] }),
      queryClient.invalidateQueries({ queryKey: ['iam', 'plants'] }),
      queryClient.invalidateQueries({ queryKey: ['iam', 'departments'] }),
    ]);
  };

  const saveMutation = useMutation({
    mutationFn: async ({ kind, record, values }: { kind: EntityKind; record?: EditableRecord; values: Record<string, unknown> }) => {
      if (kind === 'organization') return record ? updateOrganization(record.id, values) : createOrganization(values as Parameters<typeof createOrganization>[0]);
      if (kind === 'plant') return record ? updatePlant(record.id, values) : createPlant(values as Parameters<typeof createPlant>[0]);
      return record ? updateDepartment(record.id, values) : createDepartment(values as Parameters<typeof createDepartment>[0]);
    },
    onSuccess: async () => {
      message.success('保存成功');
      setModal(null);
      form.resetFields();
      await invalidate();
    },
    onError: (error: Error) => message.error(error.message),
  });

  const openCreate = (kind: EntityKind) => {
    setModal({ kind });
    form.resetFields();
    form.setFieldsValue({ is_active: true, timezone: 'Asia/Shanghai', country_code: 'CN', sort_order: 0 });
  };

  const openEdit = (kind: EntityKind, record: EditableRecord) => {
    setModal({ kind, record });
    form.resetFields();
    form.setFieldsValue(record);
  };

  const organizationColumns: TableColumnsType<OrganizationRead> = [
    { title: '组织编码', dataIndex: 'code', width: 140 },
    { title: '组织名称', dataIndex: 'name' },
    { title: '简称', dataIndex: 'short_name', render: (value) => value || '-' },
    { title: '状态', dataIndex: 'is_active', width: 90, render: (value) => <ActiveTag active={value} /> },
    { title: '操作', width: 90, render: (_, record) => <Button type="link" disabled={!access.canManageEnterprise} onClick={() => openEdit('organization', record)}>编辑</Button> },
  ];

  const plantColumns: TableColumnsType<PlantRead> = [
    { title: '工厂编码', dataIndex: 'code', width: 120 },
    { title: '工厂名称', dataIndex: 'name' },
    { title: '所属组织', dataIndex: 'organization_id', render: (value) => orgName.get(value) ?? value },
    { title: '城市', dataIndex: 'city', render: (value) => value || '-' },
    { title: '时区', dataIndex: 'timezone', width: 130 },
    { title: '状态', dataIndex: 'is_active', width: 90, render: (value) => <ActiveTag active={value} /> },
    { title: '操作', width: 90, render: (_, record) => <Button type="link" disabled={!access.canManageEnterprise} onClick={() => openEdit('plant', record)}>编辑</Button> },
  ];

  const departmentColumns: TableColumnsType<DepartmentRead> = [
    { title: '部门编码', dataIndex: 'code', width: 120 },
    { title: '部门名称', dataIndex: 'name' },
    { title: '工厂', dataIndex: 'plant_id', render: (value) => (value ? plantName.get(value) ?? value : '组织级') },
    { title: '上级部门', dataIndex: 'parent_id', render: (value) => (value ? departmentName.get(value) ?? value : '-') },
    { title: '类型', dataIndex: 'department_type', render: (value) => value || '-' },
    { title: '排序', dataIndex: 'sort_order', width: 80 },
    { title: '状态', dataIndex: 'is_active', width: 90, render: (value) => <ActiveTag active={value} /> },
    { title: '操作', width: 90, render: (_, record) => <Button type="link" disabled={!access.canManageEnterprise} onClick={() => openEdit('department', record)}>编辑</Button> },
  ];

  const loading = organizations.isLoading || plants.isLoading || departments.isLoading;

  return (
    <PageContainer title="组织架构" content="管理 Organization / Plant / Department 主数据。数据范围由后端 Data Scope 强制约束。" extra={<Tag color="blue">Phase 1.8</Tag>}>
      <Row gutter={16}>
        <Col xs={24} xl={7}>
          <Card title="组织层级" styles={{ body: { minHeight: 520 } }}>
            {treeData.length ? <Tree defaultExpandAll showLine treeData={treeData} /> : <Empty description="当前数据范围内暂无组织数据" />}
          </Card>
        </Col>
        <Col xs={24} xl={17}>
          <Card>
            <Tabs items={[
              {
                key: 'organization', label: `组织 ${orgItems.length}`,
                children: <Space direction="vertical" size={16} style={{ width: '100%' }}><Button type="primary" disabled={!access.canManageEnterprise} onClick={() => openCreate('organization')}>新建组织</Button><Table rowKey="id" loading={loading} columns={organizationColumns} dataSource={orgItems} pagination={false} /></Space>,
              },
              {
                key: 'plant', label: `工厂 ${plantItems.length}`,
                children: <Space direction="vertical" size={16} style={{ width: '100%' }}><Button type="primary" disabled={!access.canManageEnterprise} onClick={() => openCreate('plant')}>新建工厂</Button><Table rowKey="id" loading={loading} columns={plantColumns} dataSource={plantItems} pagination={false} scroll={{ x: 900 }} /></Space>,
              },
              {
                key: 'department', label: `部门 ${departmentItems.length}`,
                children: <Space direction="vertical" size={16} style={{ width: '100%' }}><Button type="primary" disabled={!access.canManageEnterprise} onClick={() => openCreate('department')}>新建部门</Button><Table rowKey="id" loading={loading} columns={departmentColumns} dataSource={departmentItems} pagination={false} scroll={{ x: 980 }} /></Space>,
              },
            ]} />
          </Card>
        </Col>
      </Row>

      <Modal title={`${modal?.record ? '编辑' : '新建'}${modal ? kindLabel[modal.kind] : ''}`} open={Boolean(modal)} confirmLoading={saveMutation.isPending} onCancel={() => setModal(null)} onOk={() => form.submit()} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={(values) => modal && saveMutation.mutate({ kind: modal.kind, record: modal.record, values })}>
          {modal && modal.kind !== 'organization' && !modal.record && (
            <Form.Item name="organization_id" label="所属组织" rules={[{ required: true }]}><Select options={orgItems.map((item) => ({ label: `${item.name} (${item.code})`, value: item.id }))} /></Form.Item>
          )}
          {modal?.kind === 'plant' && <>
            <Form.Item name="timezone" label="时区" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="country_code" label="国家代码" rules={[{ required: true, len: 2 }]}><Input maxLength={2} /></Form.Item>
            <Form.Item name="province" label="省份"><Input /></Form.Item>
            <Form.Item name="city" label="城市"><Input /></Form.Item>
            <Form.Item name="address" label="地址"><Input /></Form.Item>
          </>}
          {modal?.kind === 'department' && <>
            <Form.Item name="plant_id" label="所属工厂"><Select allowClear options={plantItems.map((item) => ({ label: `${item.name} (${item.code})`, value: item.id }))} /></Form.Item>
            <Form.Item name="parent_id" label="上级部门"><Select allowClear options={departmentItems.filter((item) => item.id !== modal.record?.id).map((item) => ({ label: `${item.name} (${item.code})`, value: item.id }))} /></Form.Item>
            <Form.Item name="department_type" label="部门类型"><Input placeholder="production / quality / planning ..." /></Form.Item>
            <Form.Item name="sort_order" label="排序"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          </>}
          <Form.Item name="code" label={`${kindLabel[modal?.kind ?? 'organization']}编码`} rules={[{ required: true, min: 2 }]}><Input /></Form.Item>
          <Form.Item name="name" label={`${kindLabel[modal?.kind ?? 'organization']}名称`} rules={[{ required: true, min: 2 }]}><Input /></Form.Item>
          {modal?.kind === 'organization' && <Form.Item name="short_name" label="组织简称"><Input /></Form.Item>}
          <Form.Item name="is_active" label="启用" valuePropName="checked"><Switch /></Form.Item>
          <Typography.Text type="secondary">当前用户只能操作后端 Data Scope 允许访问的组织资源；前端禁用按钮不替代 API 授权。</Typography.Text>
        </Form>
      </Modal>
    </PageContainer>
  );
}
