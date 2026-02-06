/**
 * Format a date string or Date object into DD/MM/YY.
 * Accepts ISO strings (YYYY-MM-DD) or already formatted inputs.
 */
export function formatDobDisplay(input?: string | Date | null): string {
  const date = input instanceof Date
    ? input
    : parseDobToDate(input || undefined);

  if (!date) return '';

  const dd = String(date.getDate()).padStart(2, '0');
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const yy = String(date.getFullYear()).slice(-2);

  return `${dd}/${mm}/${yy}`;
}

/**
 * Parse user input (DD/MM/YY, DD-MM-YY, or ISO) into a Date.
 * The parser is deliberately day-first to avoid MM/DD acceptance.
 */
export function parseDobToDate(value?: string): Date | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;

  // ISO input (YYYY-MM-DD)
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    const [year, month, day] = trimmed.split('-').map(Number);
    return buildSafeDate(year, month, day);
  }

  const normalized = trimmed.replace(/-/g, '/');
  const parts = normalized.split('/');
  if (parts.length === 3) {
    const [dayStr, monthStr, yearStr] = parts;
    const day = Number(dayStr);
    const month = Number(monthStr);
    const year = normalizeTwoDigitYear(yearStr);
    return buildSafeDate(year, month, day);
  }

  return null;
}

/**
 * Normalize DOB input to ISO string and formatted display string.
 * Returns empty values when parsing fails so callers can guard accordingly.
 */
export function normalizeDobInput(value: string): { iso: string | null; display: string; date: Date | null } {
  const date = parseDobToDate(value);
  if (!date) {
    return { iso: null, display: '', date: null };
  }

  const iso = [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-');

  return { iso, display: formatDobDisplay(date), date };
}

function normalizeTwoDigitYear(rawYear: string): number {
  if (rawYear.length === 4) return Number(rawYear);
  const yy = Number(rawYear);
  if (Number.isNaN(yy)) return NaN;

  // Assume 00-49 => 2000s, 50-99 => 1900s to keep adult ages valid
  return yy >= 50 ? 1900 + yy : 2000 + yy;
}

function buildSafeDate(year: number, month: number, day: number): Date | null {
  if ([year, month, day].some((n) => Number.isNaN(n) || n <= 0)) return null;
  const date = new Date(year, month - 1, day);
  // Guard against overflow (e.g., 31/02)
  if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) {
    return null;
  }
  return date;
}
