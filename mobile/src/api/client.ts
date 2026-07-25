import { API_BASE_URL } from './config';

/**
 * Error carrying the HTTP status.
 *
 * Callers used to decide what to tell the user by searching the message
 * string for "403", which breaks the moment the wording changes. The status
 * is data, so it belongs on the error rather than inside a sentence.
 */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, statusText: string) {
    super(`API ${status}: ${statusText}`);
    this.name = 'ApiError';
    this.status = status;
  }
}


interface RequestOptions {
  token?: string | null;
  params?: Record<string, string>;
}

export async function apiGet<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  if (options.params) {
    Object.entries(options.params).forEach(([k, v]) => url.searchParams.set(k, v));
  }

  const headers: Record<string, string> = { 'Accept': 'application/json' };
  if (options.token) {
    headers['Authorization'] = `Bearer ${options.token}`;
  }

  const resp = await fetch(url.toString(), { headers });
  if (!resp.ok) {
    throw new ApiError(resp.status, resp.statusText);
  }
  return resp.json();
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const url = new URL(path, API_BASE_URL);

  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };
  if (options.token) {
    headers['Authorization'] = `Bearer ${options.token}`;
  }

  const resp = await fetch(url.toString(), {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    throw new ApiError(resp.status, resp.statusText);
  }
  return resp.json();
}

export async function apiPatch<T>(
  path: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };
  if (options.token) headers['Authorization'] = `Bearer ${options.token}`;
  const resp = await fetch(url.toString(), { method: 'PATCH', headers, body: JSON.stringify(body) });
  if (!resp.ok) throw new ApiError(resp.status, resp.statusText);
  return resp.json();
}

export async function apiDelete(path: string, options: RequestOptions = {}): Promise<void> {
  const url = new URL(path, API_BASE_URL);
  const headers: Record<string, string> = { 'Accept': 'application/json' };
  if (options.token) headers['Authorization'] = `Bearer ${options.token}`;
  const resp = await fetch(url.toString(), { method: 'DELETE', headers });
  if (!resp.ok) throw new ApiError(resp.status, resp.statusText);
}
