const STORAGE_PREFIX = 'lims:feature:';
const SAMPLE_BARCODE_KEY = `${STORAGE_PREFIX}sampleBarcode`;

export function isSampleBarcodeEnabled(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem(SAMPLE_BARCODE_KEY) === 'true';
}

export function setSampleBarcodeEnabled(enabled: boolean) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(SAMPLE_BARCODE_KEY, enabled ? 'true' : 'false');
}

export { SAMPLE_BARCODE_KEY };
