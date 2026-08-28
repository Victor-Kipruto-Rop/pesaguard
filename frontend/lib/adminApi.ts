'use client';

import { apiFetch } from './api';

export interface AdminApiResult<T = unknown> {
  ok: boolean;
  data: T | null;
  status: number;
  error?: string;
}

export async function adminFetch<T = unknown>(path: string, init?: RequestInit): Promise<AdminApiResult<T>> {
  const adminToken = typeof window !== 'undefined' ? window.localStorage.getItem('pesaguard.admin_token') : null;

  const headers: Record<string, string> = {
    ...(typeof init?.headers === 'object' && !(init?.headers instanceof Headers) ? (init.headers as Record<string, string>) : {}),
    'Content-Type': 'application/json',
  };

  if (adminToken) {
    headers['X-Admin-Token'] = adminToken;
  }

  const result = await apiFetch<T>(path, {
    ...init,
    headers,
  });

  if (!result.ok && result.status === 403) {
    return { ok: false, data: null, status: result.status, error: 'Unauthorized' };
  }

  return result;
}
