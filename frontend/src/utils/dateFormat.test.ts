import { describe, expect, it } from 'vitest';
import { formatDateDDMMYY, normalizeDateInputToISO } from './dateFormat';

describe('dateFormat', () => {
  it('formats ISO date as DD/MM/YY', () => {
    expect(formatDateDDMMYY('1992-11-07')).toBe('07/11/92');
  });

  it('normalizes MM/DD/YYYY input at boundary', () => {
    expect(normalizeDateInputToISO('03/25/1992')).toBe('1992-03-25');
  });

  it('normalizes DD/MM/YY input', () => {
    expect(normalizeDateInputToISO('07/11/92')).toBe('1992-11-07');
  });
});
