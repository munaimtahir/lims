export type ReceiptPrintFormat = 'A4' | 'Thermal';

const RECEIPT_FORMAT_KEY = 'lims.receipt.print_format';
const THERMAL_COPIES_KEY = 'lims.receipt.thermal_copies';

export function getStoredReceiptFormat(): ReceiptPrintFormat {
  const stored = localStorage.getItem(RECEIPT_FORMAT_KEY);
  return stored === 'Thermal' ? 'Thermal' : 'A4';
}

export function setStoredReceiptFormat(format: ReceiptPrintFormat): void {
  localStorage.setItem(RECEIPT_FORMAT_KEY, format);
}

export function getStoredThermalCopies(): number {
  const stored = Number(localStorage.getItem(THERMAL_COPIES_KEY));
  if (Number.isNaN(stored) || stored < 1) {
    return 2;
  }
  return stored;
}

export function setStoredThermalCopies(copies: number): void {
  localStorage.setItem(THERMAL_COPIES_KEY, String(Math.max(1, copies)));
}
