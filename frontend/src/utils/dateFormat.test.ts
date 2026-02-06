import { describe, expect, it } from 'vitest';
import { formatDobDisplay, normalizeDobInput, parseDobToDate } from './dateFormat';

describe('dateFormat utils', () => {
  it('formats ISO to DD/MM/YY', () => {
    expect(formatDobDisplay('1990-05-15')).toBe('15/05/90');
  });

  it('parses day-first input', () => {
    const date = parseDobToDate('15/05/90');
    expect(date?.getFullYear()).toBe(1990);
    expect(date?.getMonth()).toBe(4);
    expect(date?.getDate()).toBe(15);
  });

  it('normalizes to ISO', () => {
    const { iso, display } = normalizeDobInput('02-01-24');
    expect(iso).toBe('2024-01-02');
    expect(display).toBe('02/01/24');
  });
});
