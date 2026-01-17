import { describe, expect, it } from 'vitest';
import { calculateAgeFromDob, calculateDobFromAge } from './ageDob';

describe('ageDob utils', () => {
  it('calculates age from dob', () => {
    const today = new Date('2024-04-10T00:00:00');
    const age = calculateAgeFromDob('2000-04-10', today);
    expect(age).toEqual({ years: 24, months: 0, days: 0 });
  });

  it('calculates dob from age', () => {
    const today = new Date('2024-04-10T00:00:00');
    const dob = calculateDobFromAge(10, 0, 0, today);
    expect(dob).toBe('2014-04-10');
  });
});
