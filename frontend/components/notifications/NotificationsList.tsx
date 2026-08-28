"use client";

import React, { useEffect, useState } from 'react';
import apiProxy from '../../lib/apiProxy';

type NotificationItem = {
  id: string;
  title: string;
  body?: string;
  severity?: 'info' | 'warning' | 'critical' | 'success';
  receivedAt?: string;
};

export default function NotificationsList({ apiBase, apiPath }: { apiBase?: string; apiPath?: string }) {
  const [items, setItems] = useState<NotificationItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const base = apiBase || (process.env.NEXT_PUBLIC_API_BASE_URL ?? '');
    const path = apiPath ?? '/api/notifications';
    const url = path.startsWith('http') ? path : (base ? base.replace(/\/$/, '') : '') + path;
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        // Use server proxy to call backend endpoint so cookies are included
        const data = await apiProxy(path.startsWith('/') ? path : '/' + path, { method: 'GET' });
        if (!cancelled) setItems(Array.isArray(data) ? data : []);
      } catch (err: any) {
        if (!cancelled) setError(err?.message ?? 'Failed to load');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  if (loading) return <div className="muted">Loading notifications…</div>;
  if (error) return <div className="error">Failed to load notifications: {error}</div>;
  if (!items || items.length === 0) return <div className="muted">No notifications found.</div>;

  return (
    <div className="stackCardList">
      {items.map((it) => (
        <div key={it.id} className={`stackCard ${it.severity === 'critical' ? 'stateDanger' : ''}`}>
          <div className="stackCardBody">
            <div className="stackCardHeader">
              <strong>{it.title}</strong>
              {it.receivedAt ? <small className="muted">{new Date(it.receivedAt).toLocaleString()}</small> : null}
            </div>
            {it.body ? <p>{it.body}</p> : null}
          </div>
        </div>
      ))}
    </div>
  );
}
