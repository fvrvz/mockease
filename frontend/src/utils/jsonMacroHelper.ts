/**
 * Mask macros like {{uuid}}, {{random.name}} in JSON text so that JSON.parse()
 * can validate the syntax without false syntax errors, regardless of whether
 * the macro is placed inside a string (e.g. "Hello {{random.name}}") or as an
 * unquoted value (e.g. "id": {{uuid}}).
 */
export function maskMacrosForJsonValidation(text: string): string {
  let result = ''
  let inString = false
  let escaped = false
  let i = 0

  while (i < text.length) {
    const char = text[i]

    if (inString) {
      if (escaped) {
        escaped = false
        result += char
        i++
      } else if (char === '\\') {
        escaped = true
        result += char
        i++
      } else if (char === '"') {
        inString = false
        result += char
        i++
      } else if (char === '{' && text[i + 1] === '{') {
        // Macro inside string: find closing '}}'
        const closeIdx = text.indexOf('}}', i + 2)
        if (closeIdx !== -1) {
          result += 'MACRO'
          i = closeIdx + 2
        } else {
          result += char
          i++
        }
      } else {
        result += char
        i++
      }
    } else {
      if (char === '"') {
        inString = true
        result += char
        i++
      } else if (char === '{' && text[i + 1] === '{') {
        // Macro outside string: find closing '}}' and replace with a quoted string value
        const closeIdx = text.indexOf('}}', i + 2)
        if (closeIdx !== -1) {
          result += '"MACRO"'
          i = closeIdx + 2
        } else {
          result += char
          i++
        }
      } else {
        result += char
        i++
      }
    }
  }

  return result
}

/**
 * Validates a JSON string that may contain MockEase macros.
 * Returns null if valid, or an error string if invalid.
 */
export function validateJsonWithMacros(text: string): string | null {
  if (!text.trim()) return null
  const masked = maskMacrosForJsonValidation(text)
  try {
    JSON.parse(masked)
    return null
  } catch (err: unknown) {
    return err instanceof Error ? err.message : 'Invalid JSON syntax'
  }
}

/**
 * Prettifies JSON that may contain MockEase macros, preserving exact macro tokens
 * both inside strings and as unquoted values.
 */
export function formatJsonWithMacros(text: string): { formatted: string; error?: string } {
  if (!text.trim()) return { formatted: text }

  const macros: { token: string; inString: boolean; original: string }[] = []
  let masked = ''
  let inString = false
  let escaped = false
  let i = 0

  while (i < text.length) {
    const char = text[i]

    if (inString) {
      if (escaped) {
        escaped = false
        masked += char
        i++
      } else if (char === '\\') {
        escaped = true
        masked += char
        i++
      } else if (char === '"') {
        inString = false
        masked += char
        i++
      } else if (char === '{' && text[i + 1] === '{') {
        const closeIdx = text.indexOf('}}', i + 2)
        if (closeIdx !== -1) {
          const original = text.substring(i, closeIdx + 2)
          const token = `__M_IN_${macros.length}__`
          macros.push({ token, inString: true, original })
          masked += token
          i = closeIdx + 2
        } else {
          masked += char
          i++
        }
      } else {
        masked += char
        i++
      }
    } else {
      if (char === '"') {
        inString = true
        masked += char
        i++
      } else if (char === '{' && text[i + 1] === '{') {
        const closeIdx = text.indexOf('}}', i + 2)
        if (closeIdx !== -1) {
          const original = text.substring(i, closeIdx + 2)
          const token = `__M_OUT_${macros.length}__`
          macros.push({ token, inString: false, original })
          masked += `"${token}"`
          i = closeIdx + 2
        } else {
          masked += char
          i++
        }
      } else {
        masked += char
        i++
      }
    }
  }

  try {
    const parsed = JSON.parse(masked)
    let formatted = JSON.stringify(parsed, null, 2)

    for (const { token, inString, original } of macros) {
      if (inString) {
        formatted = formatted.replace(token, original)
      } else {
        formatted = formatted.replace(`"${token}"`, original)
      }
    }

    return { formatted }
  } catch (err: unknown) {
    return {
      formatted: text,
      error: err instanceof Error ? err.message : 'Cannot beautify invalid JSON',
    }
  }
}
