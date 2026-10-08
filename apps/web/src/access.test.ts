import { describe, expect, it } from 'vitest';

import access from './access';
import type { CurrentUserContext } from './services/auth';

function makeCurrentUser(overrides: Partial<CurrentUserContext> = {}): CurrentUserContext {
  return {
    session_id: 'session-1',
    user_id: 'user-1',
    organization_id: 'org-1',
    department_id: null,
    primary_plant_id: null,
    username: 'viewer.fp',
    display_name: '只读用户',
    role_codes: ['viewer'],
    permission_codes: [
      'enterprise.organization.read',
      'enterprise.plant.read',
      'enterprise.department.read',
      'identity.user.read',
    ],
    data_scope_type: 'organization',
    data_scope_source: 'role',
    user: {
      id: 'user-1',
      organization_id: 'org-1',
      department_id: null,
      primary_plant_id: null,
      username: 'viewer.fp',
      employee_no: 'E0002',
      display_name: '只读用户',
      email: 'viewer@factorypilot.local',
      mobile: null,
      is_active: true,
      failed_login_count: 0,
      locked_until: null,
      last_login_at: null,
      version: 1,
      created_at: '2026-10-08T00:00:00Z',
      updated_at: '2026-10-08T00:00:00Z',
    },
    ...overrides,
  };
}

describe('frontend access policy', () => {
  it('denies protected routes without a current user', () => {
    const policy = access({ currentUser: null });
    expect(policy.authenticated).toBe(false);
    expect(policy.canReadEnterprise).toBe(false);
    expect(policy.canReadDataScope).toBe(false);
    expect(policy.canReadAudit).toBe(false);
  });

  it('allows viewer read capabilities without admin capabilities', () => {
    const policy = access({ currentUser: makeCurrentUser() });
    expect(policy.authenticated).toBe(true);
    expect(policy.canReadEnterprise).toBe(true);
    expect(policy.canReadUsers).toBe(true);
    expect(policy.canReadRbac).toBe(false);
    expect(policy.canReadUserRoles).toBe(false);
    expect(policy.canReadDataScope).toBe(false);
    expect(policy.canReadAudit).toBe(false);
    expect(policy.isSystemAdmin).toBe(false);
  });

  it('exposes system admin IAM capabilities independently', () => {
    const policy = access({
      currentUser: makeCurrentUser({
        role_codes: ['system_admin'],
        permission_codes: [
          'enterprise.organization.manage',
          'identity.user.manage',
          'rbac.role.read',
          'rbac.role.manage',
          'rbac.user_role.read',
          'rbac.user_role.manage',
          'rbac.data_scope.read',
          'rbac.data_scope.manage',
          'audit.log.read',
        ],
      }),
    });

    expect(policy.isSystemAdmin).toBe(true);
    expect(policy.canManageEnterprise).toBe(true);
    expect(policy.canManageUsers).toBe(true);
    expect(policy.canReadRbac).toBe(true);
    expect(policy.canManageRbac).toBe(true);
    expect(policy.canReadUserRoles).toBe(true);
    expect(policy.canManageUserRoles).toBe(true);
    expect(policy.canReadDataScope).toBe(true);
    expect(policy.canManageDataScope).toBe(true);
    expect(policy.canReadAudit).toBe(true);
  });
});
