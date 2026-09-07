import { describe, it, expect } from 'vitest'
import { isValidPin } from '../utils/pinValidation.js'

describe('isValidPin', () => {
  it('accepts 4-6 digits', () => {
    expect(isValidPin('1234')).toBe(true)
    expect(isValidPin('12345')).toBe(true)
    expect(isValidPin('123456')).toBe(true)
  })
  it('rejects invalid formats', () => {
    expect(isValidPin('123')).toBe(false)
    expect(isValidPin('1234567')).toBe(false)
    expect(isValidPin('12ab')).toBe(false)
    expect(isValidPin('abcd')).toBe(false)
    expect(isValidPin('')).toBe(false)
    expect(isValidPin(null)).toBe(false)
  })
})