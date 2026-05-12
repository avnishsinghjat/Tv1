/** Empty = same origin, or `/api` via Vite `VITE_PROXY_API_TARGET` in dev. */
const rawBase = import.meta.env.VITE_API_URL;
const baseUrl = (rawBase === undefined || rawBase === '' ? '' : String(rawBase)).replace(/\/$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function getBaseUrl(): string {
  return baseUrl;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(`${baseUrl}${path}`, { ...init, headers });
  const text = await res.text();
  let parsed: unknown = text;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!res.ok) {
    const msg =
      typeof parsed === 'object' && parsed && 'detail' in parsed
        ? String((parsed as { detail: unknown }).detail)
        : res.statusText;
    throw new ApiError(msg || 'Request failed', res.status, parsed);
  }

  return parsed as T;
}
