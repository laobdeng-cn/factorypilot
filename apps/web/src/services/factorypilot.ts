import { request } from '@umijs/max';

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  checks: Record<string, string>;
}

export async function getLiveness(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/v1/health/live', {
    method: 'GET',
  });
}

export async function getReadiness(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/v1/health/ready', {
    method: 'GET',
  });
}
