export interface ApiClientOptions {
  baseUrl?: string
  fetchImplementation?: typeof fetch
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

export class ApiClient {
  private readonly baseUrl: string
  private readonly fetchImplementation: typeof fetch

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl?.replace(/\/$/, '') ?? ''
    this.fetchImplementation = options.fetchImplementation ?? fetch
  }

  async get<T>(path: string, signal?: AbortSignal): Promise<T> {
    if (!path.startsWith('/')) {
      throw new TypeError('API paths must start with a slash.')
    }

    const response = await this.fetchImplementation(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal,
      credentials: 'same-origin',
    })

    if (!response.ok) {
      throw new ApiClientError(`API request failed with HTTP ${response.status}.`, response.status)
    }

    return (await response.json()) as T
  }
}
