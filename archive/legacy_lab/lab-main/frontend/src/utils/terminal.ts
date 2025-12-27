/**
 * Utility functions for terminal management.
 */

import type { LabTerminal } from '../types'

/**
 * Calculates the utilization percentage of a terminal's MRN range.
 * @param {LabTerminal} terminal - The lab terminal to calculate utilization for.
 * @returns {number} The utilization percentage (0-100).
 */
export function calculateTerminalUtilization(terminal: LabTerminal): number {
  if (terminal.offline_current === 0) return 0

  const total = terminal.offline_range_end - terminal.offline_range_start + 1
  const used = terminal.offline_current - terminal.offline_range_start + 1

  return Math.round((used / total) * 100)
}

/**
 * Calculates the total capacity of a terminal's MRN range.
 * @param {number} start - The start of the range.
 * @param {number} end - The end of the range.
 * @returns {number} The total number of MRNs in the range.
 */
export function calculateRangeCapacity(start: number, end: number): number {
  return end - start + 1
}
