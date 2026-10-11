import { describe, it, expect } from 'vitest'
import {
  maskMacrosForJsonValidation,
  validateJsonWithMacros,
  formatJsonWithMacros,
} from '@/utils/jsonMacroHelper'

describe('jsonMacroHelper', () => {
  it('masks macros inside strings and as unquoted values', () => {
    const input = '{"id": {{uuid}}, "msg": "Hello {{name}}"}'
    expect(maskMacrosForJsonValidation(input)).toBe('{"id": "MACRO", "msg": "Hello MACRO"}')
  })

  it('validates macro inside a JSON string without false syntax errors', () => {
    const input = '{\n  "message": "Hello {{random.name}}"\n}'
    expect(validateJsonWithMacros(input)).toBeNull()
  })

  it('validates unquoted macro as a JSON value', () => {
    const input = '{\n  "id": {{uuid}},\n  "active": true\n}'
    expect(validateJsonWithMacros(input)).toBeNull()
  })

  it('validates array of macros', () => {
    const input = '[\n  {{uuid}},\n  "User: {{random.name}}"\n]'
    expect(validateJsonWithMacros(input)).toBeNull()
  })

  it('returns syntax error for genuine invalid JSON', () => {
    const input = '{\n  "message": "Hello"\n'
    expect(validateJsonWithMacros(input)).not.toBeNull()
  })

  it('formats JSON with macros preserved inside strings and as unquoted values', () => {
    const unformatted = '{"id":{{uuid}},"message":"Hello {{random.name}}"}'
    const result = formatJsonWithMacros(unformatted)
    expect(result.error).toBeUndefined()
    expect(result.formatted).toBe('{\n  "id": {{uuid}},\n  "message": "Hello {{random.name}}"\n}')
  })

  it('returns error when formatting genuinely invalid JSON', () => {
    const invalid = '{"bad_json'
    const result = formatJsonWithMacros(invalid)
    expect(result.error).toBeDefined()
  })

  it('handles empty string gracefully', () => {
    expect(validateJsonWithMacros('')).toBeNull()
    expect(formatJsonWithMacros('').formatted).toBe('')
  })
})
