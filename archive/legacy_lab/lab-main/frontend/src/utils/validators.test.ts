import { describe, it, expect } from 'vitest'
import {
  validateCNIC,
  formatCNIC,
  validatePhone,
  formatPhone,
  validateDOB,
  calculateAge,
  calculateAgeFromDOB,
  calculateDOBFromAge,
  formatCurrency,
} from './validators'

describe('validators', () => {
  describe('CNIC validation', () => {
    it('validates correct CNIC format', () => {
      expect(validateCNIC('12345-1234567-1')).toBe(true)
      expect(validateCNIC('54321-7654321-9')).toBe(true)
    })

    it('rejects invalid CNIC formats', () => {
      expect(validateCNIC('1234-1234567-1')).toBe(false)
      expect(validateCNIC('12345-123456-1')).toBe(false)
      expect(validateCNIC('12345-1234567-12')).toBe(false)
      expect(validateCNIC('123451234567')).toBe(false)
    })

    it('formats CNIC correctly', () => {
      expect(formatCNIC('12345')).toBe('12345')
      expect(formatCNIC('123451234567')).toBe('12345-1234567')
      expect(formatCNIC('1234512345671')).toBe('12345-1234567-1')
      expect(formatCNIC('12345-1234567-1')).toBe('12345-1234567-1')
    })
  })

  describe('Phone validation', () => {
    it('validates correct phone formats', () => {
      expect(validatePhone('03001234567')).toBe(true)
      expect(validatePhone('+923001234567')).toBe(true)
      expect(validatePhone('0300 123 4567')).toBe(true)
    })

    it('rejects invalid phone formats', () => {
      expect(validatePhone('02001234567')).toBe(false)
      expect(validatePhone('030012345')).toBe(false)
      expect(validatePhone('123456789')).toBe(false)
    })

    it('formats phone correctly', () => {
      expect(formatPhone('03001234567')).toBe('03001234567')
      expect(formatPhone('+923001234567')).toBe('+923001234567')
      expect(formatPhone('0300-123-4567')).toBe('03001234567')
    })
  })

  describe('DOB validation', () => {
    it('validates dates not in the future', () => {
      expect(validateDOB('2000-01-01')).toBe(true)
      expect(validateDOB('1990-06-15')).toBe(true)
    })

    it('rejects future dates', () => {
      const futureDate = new Date()
      futureDate.setFullYear(futureDate.getFullYear() + 1)
      expect(validateDOB(futureDate.toISOString().split('T')[0])).toBe(false)
    })

    it('rejects invalid dates', () => {
      expect(validateDOB('invalid-date')).toBe(false)
    })
  })

  describe('Age calculation', () => {
    it('calculates age in years', () => {
      const fiveYearsAgo = new Date()
      fiveYearsAgo.setFullYear(fiveYearsAgo.getFullYear() - 5)
      const result = calculateAge(fiveYearsAgo.toISOString().split('T')[0])
      expect(result.unit).toBe('years')
      expect(result.age).toBeGreaterThanOrEqual(4)
      expect(result.age).toBeLessThanOrEqual(5)
    })

    it('calculates age in months for infants', () => {
      const sixMonthsAgo = new Date()
      sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6)
      const result = calculateAge(sixMonthsAgo.toISOString().split('T')[0])
      expect(result.unit).toBe('months')
      expect(result.age).toBeGreaterThanOrEqual(5)
      expect(result.age).toBeLessThanOrEqual(7)
    })

    it('calculates age in days for newborns', () => {
      const today = new Date().toISOString().split('T')[0]
      const result = calculateAge(today)
      expect(result.unit).toBe('days')
      expect(result.age).toBe(0)
    })
  })

  describe('Age from DOB calculation', () => {
    it('calculates age components correctly', () => {
      const fiveYearsAgo = new Date()
      fiveYearsAgo.setFullYear(fiveYearsAgo.getFullYear() - 5)
      const result = calculateAgeFromDOB(
        fiveYearsAgo.toISOString().split('T')[0]
      )
      expect(result.years).toBeGreaterThanOrEqual(4)
      expect(result.years).toBeLessThanOrEqual(5)
      expect(result.months).toBeGreaterThanOrEqual(0)
      expect(result.days).toBeGreaterThanOrEqual(0)
    })

    it('handles newborn correctly', () => {
      const today = new Date().toISOString().split('T')[0]
      const result = calculateAgeFromDOB(today)
      expect(result.years).toBe(0)
      expect(result.months).toBe(0)
      expect(result.days).toBe(0)
    })
  })

  describe('DOB from age calculation', () => {
    it('calculates DOB from age years', () => {
      const dob = calculateDOBFromAge(5, 0, 0)
      const today = new Date()
      const dobDate = new Date(dob)
      const yearDiff = today.getFullYear() - dobDate.getFullYear()
      expect(yearDiff).toBeGreaterThanOrEqual(4)
      expect(yearDiff).toBeLessThanOrEqual(5)
    })

    it('calculates DOB from age months', () => {
      const dob = calculateDOBFromAge(0, 6, 0)
      const today = new Date()
      const dobDate = new Date(dob)
      const monthDiff =
        (today.getFullYear() - dobDate.getFullYear()) * 12 +
        (today.getMonth() - dobDate.getMonth())
      expect(monthDiff).toBeGreaterThanOrEqual(5)
      expect(monthDiff).toBeLessThanOrEqual(7)
    })

    it('handles zero age as today', () => {
      const dob = calculateDOBFromAge(0, 0, 0)
      const today = new Date().toISOString().split('T')[0]
      expect(dob).toBe(today)
    })

    it('treats undefined values as zero', () => {
      const dob1 = calculateDOBFromAge(0, 0, 0)
      const dob2 = calculateDOBFromAge(
        undefined as unknown as number,
        undefined as unknown as number,
        undefined as unknown as number
      )
      expect(dob1).toBe(dob2)
    })
  })

  describe('Currency formatting', () => {
    it('formats currency correctly', () => {
      const formatted = formatCurrency(1000)
      expect(formatted).toContain('1')
      expect(formatted).toContain('000')
    })

    it('handles zero', () => {
      const formatted = formatCurrency(0)
      expect(formatted).toContain('0')
    })

    it('handles decimal amounts', () => {
      const formatted = formatCurrency(1234.56)
      expect(formatted).toContain('1')
      expect(formatted).toContain('234')
    })
  })
})
