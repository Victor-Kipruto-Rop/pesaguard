export function AuditLogView({ entries = [] }) {
  return (
    <section>
      <h2>Audit log</h2>
      <ul>
        {entries.map((entry) => (
          <li key={entry.created_at}>{entry.actor} {entry.action} for {entry.tenant_id}</li>
        ))}
      </ul>
    </section>
  );
}
