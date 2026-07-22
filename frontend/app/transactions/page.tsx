'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import EmptyState from '../../components/EmptyState';
import PageHeader from '../../components/PageHeader';
import TransactionSidePanel, { PanelRow } from '../../components/TransactionSidePanel';
import { apiFetch } from '../../lib/api';
import { useLocale } from '../../lib/i18n';
import { formatKeCurrency, formatKeDate } from '../../lib/formatting';

interface RawTransaction {
  trans_id: string;
  trans_amount: number;
  msisdn: string;
  business_short_code: string;
  trans_time: string;
  created_at: string | null;
}

interface Discrepancy {
  id: string;
  trans_id: string;
  anomaly_type: string;
  status: string;
  severity: string;
  resolved: boolean;
  detected_at: string;
  notes?: string;
  timeline?: Array<{ ts: string; event: string; message: string }>;
}

type TxStatus = 'matched' | 'pending' | 'unmatched' | 'disputed';

interface Row {
  trans_id: string;
  amount: number;
  created_at: string | null;
  status: TxStatus;
  discrepancy_id?: string;
  anomaly_type?: string;
  detected_at?: string;
  timeline?: Array<{ ts: string; event: string; message: string }>;
}

type DatePreset = 'all' | 'today' | '7d' | '30d' | 'custom';
type StatusFilter = 'all' | TxStatus;

const UNMATCHED_TYPES = new Set(['missing_payment', 'amount_mismatch', 'duplicate']);
const PAGE_SIZE = 25;
const POLL_MS = 20000;

function deriveStatus(disc: Discrepancy | undefined): TxStatus {
  if (!disc) return 'matched';
  if (disc.notes && disc.notes.includes('DISPUTE:')) return 'disputed';
  if (!disc.resolved && UNMATCHED_TYPES.has(disc.anomaly_type)) return 'unmatched';
  if (!disc.resolved) return 'pending';
  return 'matched';
}

function mergeRows(transactions: RawTransaction[], discrepancies: Discrepancy[]): Row[] {
  const byTransId = new Map<string, Discrepancy>();
  for (const d of discrepancies) {
    const existing = byTransId.get(d.trans_id);
    if (!existing || new Date(d.detected_at) > new Date(existing.detected_at)) {
      byTransId.set(d.trans_id, d);
    }
  }
  return transactions.map((t) => {
    const disc = byTransId.get(t.trans_id);
    return {
      trans_id: t.trans_id,
      amount: t.trans_amount,
      created_at: t.created_at,
      status: deriveStatus(disc),
      discrepancy_id: disc?.id,
      anomaly_type: disc?.anomaly_type,
      detected_at: disc?.detected_at,
      timeline: disc?.timeline,
    };
  });
}

function toCsv(rows: Row[]): string {
  const header = ['Timestamp', 'Amount', 'Transaction ID', 'Status', 'Source'];
  const lines = rows.map((r) => [
    r.created_at || '',
    String(r.amount),
    r.trans_id,
    r.status,
    'M-Pesa Daraja',
  ].map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','));
  return [header.join(','), ...lines].join('\n');
}

function downloadCsv(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function CopyIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="12" height="12" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

function truncateId(id: string) {
  return id.length > 14 ? `${id.slice(0, 6)}â€¦${id.slice(-6)}` : id;
}

export default function TransactionsPage() {
  const { t, locale } = useLocale();

  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [datePreset, setDatePreset] = useState<DatePreset>('all');
  const [customFrom, setCustomFrom] = useState('');
  const [customTo, setCustomTo] = useState('');
  const [amountOpen, setAmountOpen] = useState(false);
  const [amountMin, setAmountMin] = useState('');
  const [amountMax, setAmountMax] = useState('');
  const [density, setDensity] = useState<'dense' | 'comfortable'>('dense');
  const [sortKey, setSortKey] = useState<'timestamp' | 'amount'>('timestamp');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [panelTransId, setPanelTransId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [newIds, setNewIds] = useState<Set<string>>(new Set());
  const knownIds = useRef<Set<string>>(new Set());

  const load = async (isPoll = false) => {
    if (!isPoll) setLoading(true);
    const [txRes, discRes] = await Promise.all([
      apiFetch<{ items: RawTransaction[] }>('/v1/customers/default/transactions'),
      apiFetch<{ items: Discrepancy[] }>('/discrepancies?per_page=200&resolved='),
    ]);
    const merged = mergeRows(txRes.data?.items || [], discRes.data?.items || []);

    if (isPoll && knownIds.current.size > 0) {
      const arrivals = merged.filter((r) => !knownIds.current.has(r.trans_id));
      if (arrivals.length > 0) {
        const arrivalIds = new Set(arrivals.map((r) => r.trans_id));
        setNewIds(arrivalIds);
        setTimeout(() => setNewIds(new Set()), 1600);
      }
    }
    merged.forEach((r) => knownIds.current.add(r.trans_id));

    setRows(merged);
    if (!isPoll) setLoading(false);
  };

  useEffect(() => {
    void load();
    const interval = setInterval(() => void load(true), POLL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const dateRange = useMemo(() => {
    const now = new Date();
    if (datePreset === 'today') {
      const start = new Date(now);
      start.setHours(0, 0, 0, 0);
      return { from: start, to: now };
    }
    if (datePreset === '7d') {
      return { from: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000), to: now };
    }
    if (datePreset === '30d') {
      return { from: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000), to: now };
    }
    if (datePreset === 'custom') {
      return {
        from: customFrom ? new Date(customFrom) : null,
        to: customTo ? new Date(customTo) : null,
      };
    }
    return { from: null, to: null };
  }, [datePreset, customFrom, customTo]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const min = amountMin ? Number.parseFloat(amountMin) : null;
    const max = amountMax ? Number.parseFloat(amountMax) : null;

    let result = rows.filter((r) => {
      if (statusFilter !== 'all' && r.status !== statusFilter) return false;
      if (needle && !r.trans_id.toLowerCase().includes(needle) && !String(r.amount).includes(needle)) return false;
      if (dateRange.from || dateRange.to) {
        const created = r.created_at ? new Date(r.created_at) : null;
        if (!created) return false;
        if (dateRange.from && created < dateRange.from) return false;
        if (dateRange.to && created > dateRange.to) return false;
      }
      if (min !== null && r.amount < min) return false;
      if (max !== null && r.amount > max) return false;
      return true;
    });

    result = [...result].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      if (sortKey === 'amount') return (a.amount - b.amount) * dir;
      const at = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bt = b.created_at ? new Date(b.created_at).getTime() : 0;
      return (at - bt) * dir;
    });

    return result;
  }, [rows, q, statusFilter, dateRange, amountMin, amountMax, sortKey, sortDir]);

  const visibleRows = filtered.slice(0, visibleCount);
  const panelRow = rows.find((r) => r.trans_id === panelTransId) || null;

  const hasActiveFilters = q.trim() !== '' || statusFilter !== 'all' || datePreset !== 'all' || amountMin !== '' || amountMax !== '';

  const clearFilters = () => {
    setQ('');
    setStatusFilter('all');
    setDatePreset('all');
    setCustomFrom('');
    setCustomTo('');
    setAmountMin('');
    setAmountMax('');
  };

  const toggleSort = (key: 'timestamp' | 'amount') => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const toggleSelectAll = () => {
    if (selected.size === visibleRows.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(visibleRows.map((r) => r.trans_id)));
    }
  };

  const toggleSelectRow = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const copyRowId = async (id: string) => {
    try {
      await navigator.clipboard.writeText(id);
      setCopiedId(id);
      setTimeout(() => setCopiedId((current) => (current === id ? null : current)), 1500);
    } catch {
      // clipboard access can fail silently
    }
  };

  const bulkMarkReviewed = async () => {
    const ids = rows
      .filter((r) => selected.has(r.trans_id) && r.discrepancy_id && r.status !== 'matched')
      .map((r) => r.discrepancy_id as string);
    if (ids.length === 0) {
      setSelected(new Set());
      return;
    }
    await apiFetch('/discrepancies/bulk-resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids, note: 'Bulk resolved from transactions view' }),
    });
    setSelected(new Set());
    await load();
  };

  const exportRows = (rowsToExport: Row[], filename: string) => {
    downloadCsv(toCsv(rowsToExport), filename);
  };

  const markReviewed = async (transId: string) => {
    const row = rows.find((r) => r.trans_id === transId);
    if (!row?.discrepancy_id) return;
    await apiFetch(`/discrepancies/${row.discrepancy_id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: 'Reviewed from transactions view' }),
    });
    await load();
  };

  const flagDisputed = async (transId: string, reason: string) => {
    const row = rows.find((r) => r.trans_id === transId);
    if (!row?.discrepancy_id) return;
    await apiFetch(`/discrepancies/${row.discrepancy_id}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: `DISPUTE: ${reason}` }),
    });
    await load();
  };

  return (
    <main className="shell txPage">
      <PageHeader eyebrow={t('transactions.eyebrow')} title={t('transactions.title')} summary={t('transactions.summary')} />

      <section className="card">
        <div className="txFilterBar">
          <div className="txFilterRow">
            <div className="txSearchWrap">
              <svg className="txSearchIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="11" cy="11" r="7" />
                <path d="m21 21-4.3-4.3" />
              </svg>
              <input value={q} onChange={(e) => { setQ(e.target.value); setVisibleCount(PAGE_SIZE); }} placeholder={t('transactions.search')} />
            </div>
            <div className="txDensityToggle">
              <button
                type="button"
                className={`txDensityBtn ${density === 'dense' ? 'active' : ''}`}
                onClick={() => setDensity('dense')}
              >
                {t('transactions.densityDense')}
              </button>
              <button
                type="button"
                className={`txDensityBtn ${density === 'comfortable' ? 'active' : ''}`}
                onClick={() => setDensity('comfortable')}
              >
                {t('transactions.densityComfortable')}
              </button>
            </div>
          </div>

          <div className="txFilterRow">
            <div className="txStatusPills">
              {(['all', 'matched', 'pending', 'unmatched', 'disputed'] as StatusFilter[]).map((status) => (
                <button
                  key={status}
                  type="button"
                  data-status={status}
                  className={`txStatusPill ${statusFilter === status ? 'active' : ''}`}
                  onClick={() => { setStatusFilter(status); setVisibleCount(PAGE_SIZE); }}
                >
                  {t(`transactions.status${status.charAt(0).toUpperCase()}${status.slice(1)}`)}
                </button>
              ))}
            </div>

            <div className="txDateGroup">
              {(['all', 'today', '7d', '30d', 'custom'] as DatePreset[]).map((preset) => (
                <button
                  key={preset}
                  type="button"
                  className={`txDatePreset ${datePreset === preset ? 'active' : ''}`}
                  onClick={() => { setDatePreset(preset); setVisibleCount(PAGE_SIZE); }}
                >
                  {preset === 'all'
                    ? t('transactions.statusAll')
                    : preset === '7d'
                      ? t('transactions.date7d')
                      : preset === '30d'
                        ? t('transactions.date30d')
                        : t(`transactions.date${preset.charAt(0).toUpperCase() + preset.slice(1)}`)}
                </button>
              ))}
              {datePreset === 'custom' ? (
                <div className="txCustomRange">
                  <input type="date" value={customFrom} onChange={(e) => setCustomFrom(e.target.value)} aria-label={t('transactions.dateFrom')} />
                  <input type="date" value={customTo} onChange={(e) => setCustomTo(e.target.value)} aria-label={t('transactions.dateTo')} />
                </div>
              ) : null}
            </div>
          </div>

          <div className="txFilterRow">
            <button type="button" className={`txAmountToggle ${amountOpen ? 'active' : ''}`} onClick={() => setAmountOpen((v) => !v)}>
              {t('transactions.amountRangeToggle')} {amountOpen ? 'â–²' : 'â–¼'}
            </button>
            {amountOpen ? (
              <div className="txAmountRange">
                <input type="number" placeholder={t('transactions.amountMin')} value={amountMin} onChange={(e) => { setAmountMin(e.target.value); setVisibleCount(PAGE_SIZE); }} />
                <span className="muted">â€“</span>
                <input type="number" placeholder={t('transactions.amountMax')} value={amountMax} onChange={(e) => { setAmountMax(e.target.value); setVisibleCount(PAGE_SIZE); }} />
              </div>
            ) : null}
            <button
              type="button"
              className="secondaryBtn"
              style={{ marginLeft: 'auto' }}
              onClick={() => exportRows(filtered, 'pesaguard-transactions.csv')}
            >
              {t('transactions.export')}
            </button>
          </div>
        </div>

        <div className="txResultMeta">
          <span>{t('transactions.resultsCount').replace('{count}', String(filtered.length))}</span>
          {hasActiveFilters ? (
            <button className="txClearFilters" onClick={clearFilters} type="button">{t('transactions.clearFilters')}</button>
          ) : null}
        </div>

        {loading ? (
          <div className="txTableWrap">
            <table className={`txTable ${density}`}>
              <tbody>
                {Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="txSkeletonRow">
                    <td colSpan={5}><div className="txSkeletonBar" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : filtered.length === 0 ? (
          rows.length === 0 ? (
            <EmptyState
              title={t('transactions.emptyTitle')}
              message={t('transactions.emptyMessage')}
              action={<a className="primaryBtn" href="/onboarding">{t('transactions.emptyAction')}</a>}
            />
          ) : (
            <EmptyState
              title={t('transactions.emptyFilteredTitle')}
              message=""
              action={<button className="primaryBtn" onClick={clearFilters}>{t('transactions.clearFilters')}</button>}
            />
          )
        ) : (
          <div className="txTableWrap">
            <table className={`txTable ${density}`}>
              <thead>
                <tr>
                  <th className="txCheckboxCell">
                    <input
                      type="checkbox"
                      className="txSelectAll"
                      checked={selected.size > 0 && selected.size === visibleRows.length}
                      onChange={toggleSelectAll}
                      aria-label="Select all"
                    />
                  </th>
                  <th className="sortable" onClick={() => toggleSort('timestamp')}>
                    {t('transactions.columnTimestamp')}
                    {sortKey === 'timestamp' ? <span className="sortArrow">{sortDir === 'asc' ? 'â†‘' : 'â†“'}</span> : null}
                  </th>
                  <th className="sortable" onClick={() => toggleSort('amount')}>
                    {t('transactions.columnAmount')}
                    {sortKey === 'amount' ? <span className="sortArrow">{sortDir === 'asc' ? 'â†‘' : 'â†“'}</span> : null}
                  </th>
                  <th>{t('transactions.columnId')}</th>
                  <th>{t('transactions.columnStatus')}</th>
                  <th>{t('transactions.columnSource')}</th>
                </tr>
              </thead>
              <tbody>
                {visibleRows.map((row) => (
                  <tr
                    key={row.trans_id}
                    className={`txRow ${selected.has(row.trans_id) ? 'selected' : ''} ${newIds.has(row.trans_id) ? 'newArrival' : ''}`}
                    onClick={() => setPanelTransId(row.trans_id)}
                  >
                    <td className="txCheckboxCell" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selected.has(row.trans_id)}
                        onChange={() => toggleSelectRow(row.trans_id)}
                        aria-label={`Select ${row.trans_id}`}
                      />
                    </td>
                    <td>{row.created_at ? formatKeDate(row.created_at, locale as 'en' | 'sw') : 'â€”'}</td>
                    <td className="txAmountCell">{formatKeCurrency(row.amount, locale as 'en' | 'sw')}</td>
                    <td className="txIdCell" onClick={(e) => e.stopPropagation()}>
                      <button className={`txIdCopyBtn ${copiedId === row.trans_id ? 'copied' : ''}`} onClick={() => copyRowId(row.trans_id)} type="button">
                        {truncateId(row.trans_id)}
                        {copiedId === row.trans_id ? <CheckIcon /> : <CopyIcon />}
                      </button>
                    </td>
                    <td>
                      <span className={`statusPill ${row.status}`}>
                        {t(`transactions.status${row.status.charAt(0).toUpperCase()}${row.status.slice(1)}`)}
                      </span>
                    </td>
                    <td className="txSourceCell">{t('transactions.source')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {visibleCount < filtered.length ? (
              <div className="paginationRow">
                <button className="secondaryBtn" onClick={() => setVisibleCount((c) => c + PAGE_SIZE)}>
                  {t('dashboard.operations.pagination.next')}
                </button>
              </div>
            ) : null}
          </div>
        )}
      </section>

      {selected.size > 0 ? (
        <div className="txBulkBar">
          <span className="txBulkCount">{t('transactions.selectedCount').replace('{count}', String(selected.size))}</span>
          <div className="txBulkActions">
            <button onClick={() => void bulkMarkReviewed()}>{t('transactions.markReviewed')}</button>
            <button
              className="secondaryBtn"
              onClick={() => exportRows(rows.filter((r) => selected.has(r.trans_id)), 'pesaguard-transactions-selected.csv')}
            >
              {t('transactions.exportSelected')}
            </button>
          </div>
          <button className="txBulkClear" onClick={() => setSelected(new Set())} type="button">{t('transactions.clearSelection')}</button>
        </div>
      ) : null}

      {panelRow ? (
        <TransactionSidePanel
          row={panelRow as PanelRow}
          onClose={() => setPanelTransId(null)}
          onResolved={markReviewed}
          onDisputed={flagDisputed}
        />
      ) : null}
    </main>
  );
      }
