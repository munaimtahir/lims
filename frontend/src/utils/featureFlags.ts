const SAMPLE_BARCODE_COLLECTION_KEY = 'lims.samples.enable_barcode_collection';

export function isSampleBarcodeCollectionEnabled(): boolean {
  return localStorage.getItem(SAMPLE_BARCODE_COLLECTION_KEY) === 'true';
}

export function setSampleBarcodeCollectionEnabled(enabled: boolean): void {
  localStorage.setItem(SAMPLE_BARCODE_COLLECTION_KEY, String(enabled));
}
