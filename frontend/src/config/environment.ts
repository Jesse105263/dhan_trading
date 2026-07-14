export interface FrontendEnvironment {
  apiBaseUrl: string
}

function normalizeBaseUrl(value: string | undefined): string {
  const normalized = value?.trim().replace(/\/$/, '') ?? ''

  if (normalized && !normalized.startsWith('/') && !/^https?:\/\//u.test(normalized)) {
    throw new Error('VITE_API_BASE_URL must be empty, an absolute path, or an HTTP(S) URL.')
  }

  return normalized
}

export function readEnvironment(source: ImportMetaEnv = import.meta.env): FrontendEnvironment {
  return { apiBaseUrl: normalizeBaseUrl(source.VITE_API_BASE_URL) }
}
