const PRINT_FORMAT_KEY = 'lims:receipt:format';
const THERMAL_COPIES_KEY = 'lims:receipt:thermalCopies';

export type ReceiptFormat = 'A4' | 'Thermal';

export function loadLastReceiptFormat(): ReceiptFormat {
  if (typeof window === 'undefined') return 'A4';
  const stored = localStorage.getItem(PRINT_FORMAT_KEY);
  return stored === 'Thermal' ? 'Thermal' : 'A4';
}

export function saveLastReceiptFormat(format: ReceiptFormat) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(PRINT_FORMAT_KEY, format);
}

export function loadThermalCopies(): number {
  if (typeof window === 'undefined') return 2;
  const stored = Number(localStorage.getItem(THERMAL_COPIES_KEY));
  return Number.isFinite(stored) && stored > 0 ? stored : 2;
}

export function saveThermalCopies(copies: number) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(THERMAL_COPIES_KEY, String(Math.max(1, Math.floor(copies))));
}

export { PRINT_FORMAT_KEY, THERMAL_COPIES_KEY };
