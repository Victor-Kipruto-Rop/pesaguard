export function formatKeCurrency(value: number | string | null | undefined, locale: 'en' | 'sw' = 'en') {
  const numericValue = typeof value === 'number' ? value : Number.parseFloat(String(value ?? '0'));

  if (!Number.isFinite(numericValue)) {
    return locale === 'sw' ? 'KES 0.00' : 'KES 0.00';
  }

  return new Intl.NumberFormat(locale === 'sw' ? 'sw-KE' : 'en-KE', {
    style: 'currency',
    currency: 'KES',
    maximumFractionDigits: 2,
  }).format(numericValue);
}

export function formatKeDate(value: string | null | undefined, locale: 'en' | 'sw' = 'en') {
  if (!value) {
    return '—';
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale === 'sw' ? 'sw-KE' : 'en-KE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Africa/Nairobi',
  }).format(parsedDate);
}
