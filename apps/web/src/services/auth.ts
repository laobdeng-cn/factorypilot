export interface UserRead {
  id: string;
  organization_id: string;
  department_id: string | null;
  primary_plant_id: string | null;
  username: string;
  employee_no: string;
  display_name: string;
  email: string | null;
  mobile: string | null;
  is_active: boolean;
  failed_login_count: number;
  locked_until: string | null;
  last_login_at: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface TokenPairResponse {
  token_type: 'bearer';
  access_token: string;
  expires_in: number;
  refresh_token: string;
  refresh_expires_in: number;
  user: UserRead;
}

export interface LoginResponse extends TokenPairResponse {
  authenticated: boolean;
}

export interface CurrentUserContext {
  session_id: string;
  user_id: string;
  organization_id: string;
  department_id: string | null;
  primary_plant_id: string | null;
  username: string;
  display_name: string;
  role_codes: string[];
  permission_codes: string[];
  data_scope_type: 'global' | 'organization' | 'plant' | 'department' | 'self';
  data_scope_source: string;
  user: UserRead;
}

interface StoredSession {
  accessToken: string;
  refreshToken: string;
  accessExpiresAt: number;
  refreshExpiresAt: number;
}

interface ApiErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
  };
  detail?: string;
}

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

const SESSION_KEY = 'factorypilot.auth.session.v1';
const REFRESH_SKEW_MS = 30_000;
let refreshPromise: Promise<StoredSession | null> | null = null;

function storageAvailable(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

export function getStoredSession(): StoredSession | null {
  if (!storageAvailable()) {
    return null;
  }

  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    const session = JSON.parse(raw) as StoredSession;
    if (!session.accessToken || !session.refreshToken || !session.refreshExpiresAt) {
      throw new Error('Invalid session payload');
    }
    return session;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function hasStoredSession(): boolean {
  const session = getStoredSession();
  return Boolean(session && session.refreshExpiresAt > Date.now());
}

function persistTokenPair(payload: TokenPairResponse): StoredSession {
  const now = Date.now();
  const session: StoredSession = {
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    accessExpiresAt: now + payload.expires_in * 1000,
    refreshExpiresAt: now + payload.refresh_expires_in * 1000,
  };

  if (storageAvailable()) {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  }

  return session;
}

export function clearStoredSession(): void {
  if (storageAvailable()) {
    window.localStorage.removeItem(SESSION_KEY);
  }
}

async function readError(response: Response): Promise<ApiError> {
  let body: ApiErrorEnvelope | null = null;
  try {
    body = (await response.json()) as ApiErrorEnvelope;
  } catch {
    body = null;
  }

  return new ApiError(
    response.status,
    body?.error?.message ?? body?.detail ?? `FactoryPilot API request failed: ${response.status}`,
    body?.error?.code,
  );
}

async function postJson<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw await readError(response);
  }

  return (await response.json()) as T;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await postJson<LoginResponse>('/api/v1/auth/login', { username, password });
  persistTokenPair(response);
  return response;
}

async function rotateRefreshToken(): Promise<StoredSession | null> {
  const session = getStoredSession();
  if (!session || session.refreshExpiresAt <= Date.now()) {
    clearStoredSession();
    return null;
  }

  try {
    const response = await postJson<TokenPairResponse>('/api/v1/auth/refresh', {
      refresh_token: session.refreshToken,
    });
    return persistTokenPair(response);
  } catch {
    clearStoredSession();
    return null;
  }
}

async function refreshSession(): Promise<StoredSession | null> {
  if (!refreshPromise) {
    refreshPromise = rotateRefreshToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function getUsableAccessToken(): Promise<string | null> {
  const session = getStoredSession();
  if (!session) {
    return null;
  }

  if (session.refreshExpiresAt <= Date.now()) {
    clearStoredSession();
    return null;
  }

  if (session.accessExpiresAt - REFRESH_SKEW_MS <= Date.now()) {
    return (await refreshSession())?.accessToken ?? null;
  }

  return session.accessToken;
}

export async function apiFetch(
  input: string,
  init: RequestInit = {},
  allowRefresh = true,
): Promise<Response> {
  const accessToken = await getUsableAccessToken();
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(input, { ...init, headers });
  if (response.status !== 401 || !allowRefresh) {
    return response;
  }

  const refreshed = await refreshSession();
  if (!refreshed) {
    return response;
  }

  const retryHeaders = new Headers(init.headers);
  retryHeaders.set('Accept', 'application/json');
  retryHeaders.set('Authorization', `Bearer ${refreshed.accessToken}`);
  return fetch(input, { ...init, headers: retryHeaders });
}

export async function getCurrentUser(): Promise<CurrentUserContext> {
  const response = await apiFetch('/api/v1/auth/me');
  if (!response.ok) {
    throw await readError(response);
  }
  return (await response.json()) as CurrentUserContext;
}

export async function logout(): Promise<void> {
  try {
    const response = await apiFetch('/api/v1/auth/logout', { method: 'POST' });
    if (!response.ok && response.status !== 401) {
      throw await readError(response);
    }
  } finally {
    clearStoredSession();
  }
}
