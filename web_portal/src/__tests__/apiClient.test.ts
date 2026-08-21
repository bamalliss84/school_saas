import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  apiClient,
  setAuthTokens,
  setActiveMembershipId,
  setOnContextRequired,
  ApiError,
} from '../services/apiClient';

describe('apiClient', () => {
  beforeEach(() => {
    setAuthTokens(null, null);
    setActiveMembershipId(null);
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('injects Authorization and X-School-Membership-ID headers when available', async () => {
    setAuthTokens('test-access-token', 'test-refresh-token');
    setActiveMembershipId(42);

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: 1, name: 'Test' }),
    });
    global.fetch = mockFetch;

    const result = await apiClient.get('/test-endpoint');

    expect(result).toEqual({ id: 1, name: 'Test' });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const callHeaders = mockFetch.mock.calls[0][1]?.headers as Headers;
    expect(callHeaders.get('Authorization')).toBe('Bearer test-access-token');
    expect(callHeaders.get('X-School-Membership-ID')).toBe('42');
  });

  it('normalizes error responses according to backend error envelope', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        success: false,
        message: 'Validation failed.',
        errors: { name: ['This field is required.'] },
      }),
    });
    global.fetch = mockFetch;

    try {
      await apiClient.post('/create', { name: '' });
      expect.fail('Should have thrown an error');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(400);
      expect(apiErr.message).toBe('Validation failed.');
      expect(apiErr.errors).toEqual({ name: ['This field is required.'] });
    }
  });

  it('triggers onContextRequired callback on 409 context_required', async () => {
    const contextRequiredCallback = vi.fn();
    setOnContextRequired(contextRequiredCallback);

    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({
        success: false,
        message: 'A school membership context is required.',
        errors: { code: 'context_required' },
      }),
    });
    global.fetch = mockFetch;

    try {
      await apiClient.get('/timetable/grid/');
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(409);
      expect(contextRequiredCallback).toHaveBeenCalledTimes(1);
    }
  });

  it('performs single-flight token refresh on 401 Unauthorized and retries request', async () => {
    setAuthTokens('expired-access', 'valid-refresh');

    const mockFetch = vi
      .fn()
      // First call fails with 401
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ success: false, message: 'Token is expired.' }),
      })
      // Refresh call succeeds
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ access: 'new-access-token', refresh: 'new-refresh-token' }),
      })
      // Retried call succeeds
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: 'secret payload' }),
      });

    global.fetch = mockFetch;

    const result = await apiClient.get('/protected-resource');

    expect(result).toEqual({ data: 'secret payload' });
    expect(mockFetch).toHaveBeenCalledTimes(3);
    expect(localStorage.getItem('access_token')).toBe('new-access-token');
  });
});
