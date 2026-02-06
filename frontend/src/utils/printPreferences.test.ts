import { describe, expect, it } from 'vitest';
import {
  getStoredReceiptFormat,
  getStoredThermalCopies,
  setStoredReceiptFormat,
  setStoredThermalCopies,
} from './printPreferences';

describe('printPreferences', () => {
  it('remembers receipt print format', () => {
    localStorage.clear();
    setStoredReceiptFormat('Thermal');
    expect(getStoredReceiptFormat()).toBe('Thermal');
  });

  it('defaults thermal copies to 2', () => {
    localStorage.clear();
    expect(getStoredThermalCopies()).toBe(2);
    setStoredThermalCopies(3);
    expect(getStoredThermalCopies()).toBe(3);
  });
});
