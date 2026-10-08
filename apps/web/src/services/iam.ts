import { ApiError, apiFetch, type UserRead } from './auth';

export type DataScopeType = 'global' | 'organization' | 'plant' | 'department' | 'self';

export interface PageResult<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface OrganizationRead {
  id: string;
  code: string;
  name: string;
  short_name: string | null;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface PlantRead {
  id: string;
  organization_id: string;
  code: string;
  name: string;
  timezone: string;
  country_code: string;
  province: string | null;
  city: string | null;
  address: string | null;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface DepartmentRead {
  id: string;
  organization_id: string;
  plant_id: string | null;
  parent_id: string | null;
  code: string;
  name: string;
  department_type: string | null;
  sort_order: number;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface PermissionRead {
  id: string;
  code: string;
  name: string;
  module: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RoleRead {
  id: string;
  organization_id: string | null;
  code: string;
  name: string;
  description: string | null;
  is_system: boolean;
  is_active: boolean;
  data_scope: DataScopeType;
  permission_codes: string[];
  created_at: string;
  updated_at: string;
}

export interface UserRolesRead {
  user_id: string;
  role_ids: string[];
  role_codes: string[];
}

export interface UserDataScopeRead {
  user_id: string;
  role_scope_type: DataScopeType;
  override_scope_type: DataScopeType | null;
  effective_scope_type: DataScopeType;
  source: string;
}

export interface RoleDataScopeRead {
  role_id: string;
  scope_type: DataScopeType;
}

export interface OrganizationPayload {
  code: string;
  name: string;
  short_name?: string | null;
  is_active?: boolean;
}

export interface PlantPayload {
  organization_id: string;
  code: string;
  name: string;
  timezone?: string;
  country_code?: string;
  province?: string | null;
  city?: string | null;
  address?: string | null;
  is_active?: boolean;
}

export interface DepartmentPayload {
  organization_id: string;
  plant_id?: string | null;
  parent_id?: string | null;
  code: string;
  name: string;
  department_type?: string | null;
  sort_order?: number;
  is_active?: boolean;
}

export interface UserCreatePayload {
  organization_id: string;
  department_id?: string | null;
  primary_plant_id?: string | null;
  username: string;
  employee_no: string;
  display_name: string;
  email?: string | null;
  mobile?: string | null;
  password: string;
  is_active?: boolean;
}

export interface RoleCreatePayload {
  code: string;
  name: string;
  description?: string | null;
  data_scope: DataScopeType;
}

interface ListQuery {
  page?: number;
  page_size?: number;
  is_active?: boolean;
}

interface UserListQuery extends ListQuery {
  organization_id?: string;
  department_id?: string;
  primary_plant_id?: string;
  q?: string;
}

function queryString(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value));
    }
  });
  const encoded = search.toString();
  return encoded ? `?${encoded}` : '';
}

async function readApiError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as {
      error?: { code?: string; message?: string };
      detail?: string;
    };
    return new ApiError(
      response.status,
      payload.error?.message ?? payload.detail ?? `FactoryPilot API request failed: ${response.status}`,
      payload.error?.code,
    );
  } catch {
    return new ApiError(response.status, `FactoryPilot API request failed: ${response.status}`);
  }
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await apiFetch(path, { ...init, headers });
  if (!response.ok) {
    throw await readApiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function jsonBody(payload: unknown): Pick<RequestInit, 'body' | 'headers'> {
  return {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  };
}

export function listOrganizations(query: ListQuery = {}): Promise<PageResult<OrganizationRead>> {
  return requestJson(`/api/v1/organizations${queryString({ page: query.page ?? 1, page_size: query.page_size ?? 100, is_active: query.is_active })}`);
}

export function createOrganization(payload: OrganizationPayload): Promise<OrganizationRead> {
  return requestJson('/api/v1/organizations', { method: 'POST', ...jsonBody(payload) });
}

export function updateOrganization(id: string, payload: Record<string, unknown>): Promise<OrganizationRead> {
  return requestJson(`/api/v1/organizations/${id}`, { method: 'PATCH', ...jsonBody(payload) });
}

export function listPlants(query: ListQuery & { organization_id?: string } = {}): Promise<PageResult<PlantRead>> {
  return requestJson(`/api/v1/plants${queryString({ page: query.page ?? 1, page_size: query.page_size ?? 100, organization_id: query.organization_id, is_active: query.is_active })}`);
}

export function createPlant(payload: PlantPayload): Promise<PlantRead> {
  return requestJson('/api/v1/plants', { method: 'POST', ...jsonBody(payload) });
}

export function updatePlant(id: string, payload: Record<string, unknown>): Promise<PlantRead> {
  return requestJson(`/api/v1/plants/${id}`, { method: 'PATCH', ...jsonBody(payload) });
}

export function listDepartments(
  query: ListQuery & { organization_id?: string; plant_id?: string; parent_id?: string } = {},
): Promise<PageResult<DepartmentRead>> {
  return requestJson(`/api/v1/departments${queryString({ page: query.page ?? 1, page_size: query.page_size ?? 100, organization_id: query.organization_id, plant_id: query.plant_id, parent_id: query.parent_id, is_active: query.is_active })}`);
}

export function createDepartment(payload: DepartmentPayload): Promise<DepartmentRead> {
  return requestJson('/api/v1/departments', { method: 'POST', ...jsonBody(payload) });
}

export function updateDepartment(id: string, payload: Record<string, unknown>): Promise<DepartmentRead> {
  return requestJson(`/api/v1/departments/${id}`, { method: 'PATCH', ...jsonBody(payload) });
}

export function listUsers(query: UserListQuery = {}): Promise<PageResult<UserRead>> {
  return requestJson(`/api/v1/users${queryString({ page: query.page ?? 1, page_size: query.page_size ?? 20, organization_id: query.organization_id, department_id: query.department_id, primary_plant_id: query.primary_plant_id, is_active: query.is_active, q: query.q })}`);
}

export function createUser(payload: UserCreatePayload): Promise<UserRead> {
  return requestJson('/api/v1/users', { method: 'POST', ...jsonBody(payload) });
}

export function updateUser(id: string, payload: Record<string, unknown>): Promise<UserRead> {
  return requestJson(`/api/v1/users/${id}`, { method: 'PATCH', ...jsonBody(payload) });
}

export function resetUserPassword(id: string, newPassword: string): Promise<void> {
  return requestJson(`/api/v1/users/${id}/password`, {
    method: 'POST',
    ...jsonBody({ new_password: newPassword }),
  });
}

export function listPermissions(): Promise<PermissionRead[]> {
  return requestJson('/api/v1/permissions');
}

export function listRoles(): Promise<RoleRead[]> {
  return requestJson('/api/v1/roles');
}

export function createRole(payload: RoleCreatePayload): Promise<RoleRead> {
  return requestJson('/api/v1/roles', { method: 'POST', ...jsonBody(payload) });
}

export function updateRole(id: string, payload: Record<string, unknown>): Promise<RoleRead> {
  return requestJson(`/api/v1/roles/${id}`, { method: 'PATCH', ...jsonBody(payload) });
}

export function setRolePermissions(id: string, permissionCodes: string[]): Promise<RoleRead> {
  return requestJson(`/api/v1/roles/${id}/permissions`, {
    method: 'PUT',
    ...jsonBody({ permission_codes: permissionCodes }),
  });
}

export function getRoleDataScope(id: string): Promise<RoleDataScopeRead> {
  return requestJson(`/api/v1/roles/${id}/data-scope`);
}

export function setRoleDataScope(id: string, scopeType: DataScopeType): Promise<RoleDataScopeRead> {
  return requestJson(`/api/v1/roles/${id}/data-scope`, {
    method: 'PUT',
    ...jsonBody({ scope_type: scopeType }),
  });
}

export function getUserRoles(id: string): Promise<UserRolesRead> {
  return requestJson(`/api/v1/users/${id}/roles`);
}

export function setUserRoles(id: string, roleIds: string[]): Promise<UserRolesRead> {
  return requestJson(`/api/v1/users/${id}/roles`, {
    method: 'PUT',
    ...jsonBody({ role_ids: roleIds }),
  });
}

export function getUserDataScope(id: string): Promise<UserDataScopeRead> {
  return requestJson(`/api/v1/users/${id}/data-scope`);
}

export function setUserDataScope(id: string, scopeType: DataScopeType | null): Promise<UserDataScopeRead> {
  return requestJson(`/api/v1/users/${id}/data-scope`, {
    method: 'PUT',
    ...jsonBody({ scope_type: scopeType }),
  });
}
