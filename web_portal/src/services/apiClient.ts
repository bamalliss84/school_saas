import { ApiErrorResponse } from '../types/api';

const API_BASE = '/api/v1';

// In-memory token store for security
let accessToken: string | null = localStorage.getItem('access_token');
let refreshToken: string | null = localStorage.getItem('refresh_token');
let activeMembershipId: number | null = localStorage.getItem('active_membership_id')
  ? Number(localStorage.getItem('active_membership_id'))
  : null;

// Callbacks for global events
let onUnauthorizedCallback: (() => void) | null = null;
let onContextRequiredCallback: (() => void) | null = null;

export const setAuthTokens = (access: string | null, refresh: string | null) => {
  accessToken = access;
  refreshToken = refresh;
  if (access) {
    localStorage.setItem('access_token', access);
  } else {
    localStorage.removeItem('access_token');
  }
  if (refresh) {
    localStorage.setItem('refresh_token', refresh);
  } else {
    localStorage.removeItem('refresh_token');
  }
};

export const getAccessToken = () => accessToken;
export const getRefreshToken = () => refreshToken;

export const setActiveMembershipId = (id: number | null) => {
  activeMembershipId = id;
  if (id !== null) {
    localStorage.setItem('active_membership_id', String(id));
  } else {
    localStorage.removeItem('active_membership_id');
  }
};

export const getActiveMembershipId = () => activeMembershipId;

export const setOnUnauthorized = (cb: () => void) => {
  onUnauthorizedCallback = cb;
};

export const setOnContextRequired = (cb: () => void) => {
  onContextRequiredCallback = cb;
};

// Single-flight refresh mutex
let refreshPromise: Promise<string | null> | null = null;

const refreshAccessToken = async (): Promise<string | null> => {
  if (!refreshToken) {
    return null;
  }
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (!response.ok) {
        setAuthTokens(null, null);
        setActiveMembershipId(null);
        if (onUnauthorizedCallback) {
          onUnauthorizedCallback();
        }
        return null;
      }

      const data = await response.json();
      const newAccess = data.access;
      const newRefresh = data.refresh || refreshToken;
      setAuthTokens(newAccess, newRefresh);
      return newAccess;
    } catch {
      setAuthTokens(null, null);
      setActiveMembershipId(null);
      if (onUnauthorizedCallback) {
        onUnauthorizedCallback();
      }
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

export class ApiError extends Error {
  status: number;
  errors: Record<string, unknown>;

  constructor(status: number, message: string, errors: Record<string, unknown> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errors = errors;
  }
}

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
  skipContext?: boolean;
}

export const request = async <T = unknown>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> => {
  const { params, skipContext, headers: customHeaders, ...restOptions } = options;

  let url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        searchParams.append(key, String(val));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  const buildHeaders = (token: string | null): Headers => {
    const headers = new Headers(customHeaders);
    if (!headers.has('Content-Type') && !(restOptions.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    if (!skipContext && activeMembershipId !== null) {
      headers.set('X-School-Membership-ID', String(activeMembershipId));
    }
    return headers;
  };

  let response: Response;
  try {
    response = await fetch(url, {
      ...restOptions,
      headers: buildHeaders(accessToken),
    });
  } catch (err: unknown) {
    const errMessage = err instanceof Error ? err.message : 'Network error';
    throw new ApiError(0, 'تعذر الاتصال بالخادم، يرجى التحقق من اتصال الشبكة.', {
      network_error: errMessage,
    });
  }

  // Handle 401 Unauthorized with token refresh retry
  if (response.status === 401 && refreshToken && !endpoint.includes('/auth/login/') && !endpoint.includes('/auth/refresh/')) {
    const newAccessToken = await refreshAccessToken();
    if (newAccessToken) {
      response = await fetch(url, {
        ...restOptions,
        headers: buildHeaders(newAccessToken),
      });
    } else {
      throw new ApiError(401, 'انتهت صلاحية الجلسة، يرجى تسجيل الدخول مجددًا.');
    }
  }

  // Parse error or success
  if (!response.ok) {
    let errorData: Partial<ApiErrorResponse> = {};
    try {
      errorData = await response.json();
    } catch {
      // Non-JSON response
    }

    const message = errorData.message || (
      response.status === 401 ? 'يرجى تسجيل الدخول أولاً' :
      response.status === 403 ? 'ليس لديك صلاحية لتنفيذ هذا الإجراء' :
      response.status === 404 ? 'المورد المطلوب غير موجود' :
      response.status === 409 ? 'يوجد تعارض في البيانات أو يلزم تحديد السياق' :
      'حدث خطأ غير متوقع أثناء معالجة الطلب.'
    );

    const errors = errorData.errors || {};

    // 409 context_required handler
    if (response.status === 409 && errors.code === 'context_required') {
      if (onContextRequiredCallback) {
        onContextRequiredCallback();
      }
    }

    // 401 handler without refresh
    if (response.status === 401) {
      setAuthTokens(null, null);
      if (onUnauthorizedCallback) {
        onUnauthorizedCallback();
      }
    }

    throw new ApiError(response.status, message, errors);
  }

  if (response.status === 204 || response.status === 205) {
    return null as T;
  }

  return response.json() as Promise<T>;
};

export const apiClient = {
  get: <T = unknown>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),
  post: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  put: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  patch: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  delete: <T = unknown>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
};
