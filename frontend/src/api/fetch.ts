import { apiFetch, getBaseUrl } from './client';

export type FetchRun = {
  id: string;
  status: string;
  source_label: string | null;
  objects_count: number;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
};

export type TCObjectRow = {
  id: string;
  fetch_run_id: string;
  uid: string;
  object_type: string;
  name: string | null;
  revision: string | null;
  payload: Record<string, unknown>;
  created_at: string;
};

export async function createFetchRun(
  token: string,
  sourceLabel: string | null,
  useCache: boolean,
): Promise<FetchRun> {
  return apiFetch<FetchRun>(
    '/api/fetch/runs',
    {
      method: 'POST',
      body: JSON.stringify({ source_label: sourceLabel || null, use_cache: useCache }),
    },
    token,
  );
}

export async function listFetchRuns(token: string, limit = 50): Promise<FetchRun[]> {
  const q = new URLSearchParams({ limit: String(limit) });
  return apiFetch<FetchRun[]>(`/api/fetch/runs?${q}`, {}, token);
}

export async function listObjects(
  token: string,
  fetchRunId: string | null,
  limit = 100,
): Promise<TCObjectRow[]> {
  const q = new URLSearchParams({ limit: String(limit) });
  if (fetchRunId) {
    q.set('fetch_run_id', fetchRunId);
  }
  return apiFetch<TCObjectRow[]>(`/api/objects?${q}`, {}, token);
}

export { getBaseUrl };
