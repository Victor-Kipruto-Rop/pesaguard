export function ExportButton({ tenantId, onExport }) {
  return (
    <button
      type="button"
      onClick={() => onExport?.(tenantId)}
      style={{ padding: "0.5rem 1rem" }}
    >
      Export CSV
    </button>
  );
}
