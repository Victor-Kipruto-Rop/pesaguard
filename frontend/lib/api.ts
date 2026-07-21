const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5001';

export async function apiFetch<T = unknown>(
  path: string,
  init?: RequestInit,
): Promise<{ ok: boolean; data: T | null; status: number }> {
  try {
    const response = await fetch(`${API_BASE}${path}`, init);
    const data = response.ok ? ((await response.json()) as T) : null;
    return { ok: response.ok, data, status: response.status };
  } catch {
    return { ok: false, data: null, status: 0 };
  }
}

export { API_BASE };
