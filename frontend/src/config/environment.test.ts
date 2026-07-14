import { readEnvironment } from './environment'
import { describe, expect, it } from 'vitest'

describe('readEnvironment', () => {
  it('normalizes an optional API base URL', () => {
    expect(readEnvironment({ VITE_API_BASE_URL: ' /platform/ ' } as ImportMetaEnv)).toEqual({
      apiBaseUrl: '/platform',
    })
  })

  it('rejects unsupported API base URL values', () => {
    expect(() => readEnvironment({ VITE_API_BASE_URL: 'example.test' } as ImportMetaEnv)).toThrow(
      'VITE_API_BASE_URL must be empty, an absolute path, or an HTTP(S) URL.',
    )
  })
})
