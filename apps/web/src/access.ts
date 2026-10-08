import type { CurrentUserContext } from './services/auth';

interface InitialState {
  currentUser: CurrentUserContext | null;
}

export default function access(initialState: InitialState | undefined) {
  const currentUser = initialState?.currentUser ?? null;
  const permissions = new Set(currentUser?.permission_codes ?? []);
  const roles = new Set(currentUser?.role_codes ?? []);

  const hasAnyPermission = (...codes: string[]) => codes.some((code) => permissions.has(code));

  return {
    authenticated: Boolean(currentUser),
    isSystemAdmin: roles.has('system_admin'),
    canReadEnterprise: hasAnyPermission(
      'enterprise.organization.read',
      'enterprise.plant.read',
      'enterprise.department.read',
    ),
    canManageEnterprise: hasAnyPermission(
      'enterprise.organization.manage',
      'enterprise.plant.manage',
      'enterprise.department.manage',
    ),
    canReadUsers: permissions.has('identity.user.read'),
    canManageUsers: permissions.has('identity.user.manage'),
    canReadRbac: hasAnyPermission('rbac.role.read', 'rbac.permission.read'),
    canManageRbac: hasAnyPermission('rbac.role.manage', 'rbac.user_role.manage', 'rbac.data_scope.manage'),
    canReadAudit: hasAnyPermission(
      'audit.log.read',
      'audit.security_event.read',
      'audit.authorization.read',
    ),
  };
}
