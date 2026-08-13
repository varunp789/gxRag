export type HealthResponse = {
  status: string;
  service: string;
  timestamp: string;
};

export async function fetchHealth(apiBaseUrl: string): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/v1/health`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  return (await response.json()) as HealthResponse;
}

