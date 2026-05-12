import { apiFetch } from './client';

const TOKEN_KEY = 'tc_access_token';
const USER_KEY = 'tc_username';

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  username: string;
};

export async function login(username: string, password: string): Promise<TokenResponse> {
  const body = await apiFetch<TokenResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  localStorage.setItem(TOKEN_KEY, body.access_token);
  localStorage.setItem(USER_KEY, body.username);
  return body;
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUsername(): string | null {
  return localStorage.getItem(USER_KEY);
}
