'use client';

import { useEffect, useState } from 'react';

export default function RoleAwarePanel() {
  const [role, setRole] = useState<'admin' | 'ops'>('ops');

  useEffect(() => {
    const saved = window.localStorage.getItem('pesaguard.role') || 'ops';
    setRole(saved as 'admin' | 'ops');
  }, []);

  const setAdmin = () => {
    window.localStorage.setItem('pesaguard.role', 'admin');
    setRole('admin');
  };

  const setOps = () => {
    window.localStorage.setItem('pesaguard.role', 'ops');
    setRole('ops');
  };

  return (
    <section className="card">
      <div className="sectionTitle">Role-based workspace</div>
      <div className="row"><span>Current role</span><strong>{role}</strong></div>
      <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
        <button onClick={setAdmin}>Switch to Admin</button>
        <button onClick={setOps}>Switch to Ops</button>
      </div>
      {role === 'admin' ? (
        <div style={{ marginTop: 12 }} className="muted">
          Admin controls: tenant overrides, alert routing, threshold tuning, and audit retention.
        </div>
      ) : (
        <div style={{ marginTop: 12 }} className="muted">
          Ops view: exception queue, incident notes, and daily reconciliation summaries.
        </div>
      )}
    </section>
  );
}
