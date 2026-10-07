export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  checks: Record<string, string>;
}

async function getHealth(path: string): Promise<HealthResponse> {
  const response = await fetch(path, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`FactoryPilot API request failed: ${response.status}`);
  }

  return (await response.json()) as HealthResponse;
}

export function getLiveness(): Promise<HealthResponse> {
  return getHealth('/api/v1/health/live');
}

export function getReadiness(): Promise<HealthResponse> {
  return getHealth('/api/v1/health/ready');
}
