/**
 * Validates a CNIC string.
 * @param {string} cnic - The CNIC to validate.
 * @returns {boolean} True if the CNIC is valid, false otherwise.
 */
export function validateCNIC(cnic: string): boolean {
  const cnicRegex = /^\d{5}-\d{7}-\d$/
  return cnicRegex.test(cnic)
}

/**
 * Formats a CNIC string.
 * @param {string} value - The CNIC string to format.
 * @returns {string} The formatted CNIC string.
 */
export function formatCNIC(value: string): string {
  const digits = value.replace(/\D/g, '')
  if (digits.length <= 5) {
    return digits
  } else if (digits.length <= 12) {
    return `${digits.slice(0, 5)}-${digits.slice(5)}`
  } else {
    return `${digits.slice(0, 5)}-${digits.slice(5, 12)}-${digits.slice(12, 13)}`
  }
}

/**
 * Validates a phone number.
 * @param {string} phone - The phone number to validate.
 * @returns {boolean} True if the phone number is valid, false otherwise.
 */
export function validatePhone(phone: string): boolean {
  const phoneRegex = /^(\+92|0)?3\d{9}$/
  return phoneRegex.test(phone.replace(/\s|-/g, ''))
}

/**
 * Formats a phone number.
 * @param {string} value - The phone number to format.
 * @returns {string} The formatted phone number.
 */
export function formatPhone(value: string): string {
  const cleaned = value.replace(/[^\d+]/g, '')
  if (cleaned.startsWith('+92')) {
    return cleaned.slice(0, 13)
  } else if (cleaned.startsWith('0')) {
    return cleaned.slice(0, 11)
  }
  return cleaned.slice(0, 11)
}

/**
 * Validates a date of birth.
 * @param {string} dob - The date of birth to validate.
 * @returns {boolean} True if the date of birth is valid, false otherwise.
 */
export function validateDOB(dob: string): boolean {
  if (!dob) return false
  const date = new Date(dob)
  const today = new Date()
  return date <= today && !isNaN(date.getTime())
}

/**
 * Calculates the age from a date of birth.
 * @param {string} dob - The date of birth.
 * @returns {{ years: number; months: number; days: number }} An object with the age in years, months, and days.
 */
export function calculateAgeFromDOB(dob: string): {
  years: number
  months: number
  days: number
} {
  const birthDate = new Date(dob)
  const today = new Date()

  let years = today.getFullYear() - birthDate.getFullYear()
  let months = today.getMonth() - birthDate.getMonth()
  let days = today.getDate() - birthDate.getDate()

  if (days < 0) {
    months--
    const lastMonth = new Date(today.getFullYear(), today.getMonth(), 0)
    days += lastMonth.getDate()
  }

  if (months < 0) {
    years--
    months += 12
  }

  return {
    years: Math.max(0, years),
    months: Math.max(0, months),
    days: Math.max(0, days),
  }
}

/**
 * Calculates the date of birth from an age.
 * @param {number} years - The age in years.
 * @param {number} months - The age in months.
 * @param {number} days - The age in days.
 * @returns {string} The date of birth in 'YYYY-MM-DD' format.
 */
export function calculateDOBFromAge(
  years: number,
  months: number,
  days: number
): string {
  const today = new Date()
  
  const y = years || 0
  const m = months || 0
  const d = days || 0
  
  const dob = new Date(today)
  dob.setFullYear(today.getFullYear() - y)
  dob.setMonth(today.getMonth() - m)
  dob.setDate(today.getDate() - d)
  
  return dob.toISOString().split('T')[0]
}

/**
 * Calculates the age from a date of birth (legacy function).
 * @param {string} dob - The date of birth.
 * @returns {{ age: number; unit: 'years' | 'months' | 'days' }} An object with the age and unit.
 */
export function calculateAge(dob: string): {
  age: number
  unit: 'years' | 'months' | 'days'
} {
  const { years, months, days } = calculateAgeFromDOB(dob)

  if (years > 0) {
    return { age: years, unit: 'years' }
  } else if (months > 0) {
    return { age: months, unit: 'months' }
  } else {
    return { age: Math.max(days, 0), unit: 'days' }
  }
}

/**
 * Formats a number as currency.
 * @param {number} amount - The amount to format.
 * @returns {string} The formatted currency string.
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-PK', {
    style: 'currency',
    currency: 'PKR',
  }).format(amount)
}

/**
 * Formats a date string.
 * @param {string | Date} date - The date to format.
 * @returns {string} The formatted date string.
 */
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-PK', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

/**
 * Formats a time string.
 * @param {string | Date} date - The date to format.
 * @returns {string} The formatted time string.
 */
export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString('en-PK', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

/**
 * Formats a date and time string.
 * @param {string | Date} date - The date to format.
 * @returns {string} The formatted date and time string.
 */
export function formatDateTime(date: string | Date): string {
  return `${formatDate(date)} ${formatTime(date)}`
}
