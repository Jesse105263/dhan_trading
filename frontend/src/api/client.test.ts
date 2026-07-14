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

  it('sends bounded research command bodies as same-origin JSON', async () => {
    const fetchImplementation = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        new Response(JSON.stringify({ data: { status: 'ANSWERED' } }), { status: 200 }),
      )
    const client = new ApiClient({ fetchImplementation })
    await client.post('/api/v2/analyst/questions', {
      question: 'Explain',
      opportunity_ids: ['one'],
    })
    expect(fetchImplementation).toHaveBeenCalledWith('/api/v2/analyst/questions', {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: 'Explain', opportunity_ids: ['one'] }),
      signal: undefined,
      credentials: 'same-origin',
    })
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
