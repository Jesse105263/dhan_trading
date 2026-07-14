import { ApiClient, ApiClientError } from './client'
import { describe, expect, it, vi } from 'vitest'

describe('ApiClient', () => {
  it('uses GET, JSON acceptance, same-origin credentials and the configured base URL', async () => {
    const fetchImplementation = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    const client = new ApiClient({ baseUrl: '/platform/', fetchImplementation })

    await expect(client.get<{ status: string }>('/future-resource')).resolves.toEqual({
      status: 'ok',
    })
    expect(fetchImplementation).toHaveBeenCalledWith('/platform/future-resource', {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: undefined,
      credentials: 'same-origin',
    })
  })

  it('rejects invalid paths without making a request', async () => {
    const fetchImplementation = vi.fn<typeof fetch>()
    const client = new ApiClient({ fetchImplementation })

    await expect(client.get('api/v1')).rejects.toThrow(TypeError)
    expect(fetchImplementation).not.toHaveBeenCalled()
  })

  it('provides a typed HTTP error without assuming a response body', async () => {
    const client = new ApiClient({
      fetchImplementation: vi
        .fn<typeof fetch>()
        .mockResolvedValue(new Response(null, { status: 503 })),
    })

    await expect(client.get('/future-resource')).rejects.toEqual(
      new ApiClientError('API request failed with HTTP 503.', 503),
    )
  })
})
