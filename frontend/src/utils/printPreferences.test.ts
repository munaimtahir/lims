import { describe, expect, it, beforeEach } from 'vitest';
import { loadLastReceiptFormat, saveLastReceiptFormat, loadThermalCopies, saveThermalCopies } from './printPreferences';

describe('printPreferences', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('defaults to A4 when nothing stored', () => {
    expect(loadLastReceiptFormat()).toBe('A4');
  });

  it('persists last receipt format', () => {
    saveLastReceiptFormat('Thermal');
    expect(loadLastReceiptFormat()).toBe('Thermal');
  });

  it('defaults thermal copies to 2', () => {
    expect(loadThermalCopies()).toBe(2);
  });

  it('persists thermal copies with min 1', () => {
    saveThermalCopies(3);
    expect(loadThermalCopies()).toBe(3);
    saveThermalCopies(0);
    expect(loadThermalCopies()).toBe(1);
  });
});
