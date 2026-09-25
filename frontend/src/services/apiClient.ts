import { ENV } from '../config/env';
import type { ApiError } from '../types';

class ApiClientError extends Error {
  code: string;
  requestId: string;
  status: number;
  details?: unknown;

  constructor(error: ApiError, status: number) {
    super(error.message);
    this.name = 'ApiClientError';
    this.code = error.code;
    this.requestId = error.request_id;
    this.status = status;
    this.details = error.details;
  }
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

export const TOKEN_STORAGE_KEY = 'enermax_access_token';
export const REFRESH_TOKEN_STORAGE_KEY = 'enermax_refresh_token';

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${ENV.API_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Request ID correlation
  if (!headers.has('X-Request-ID')) {
    headers.set('X-Request-ID', `req_${Math.random().toString(36).substring(2, 10)}`);
  }

  // Inject Bearer token
  if (!options.skipAuth) {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  try {
    const response = await fetch(url, { ...options, headers });

    // Handle 401 Unauthorized with token refresh mechanism
    if (response.status === 401 && !options.skipAuth && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
      if (refreshToken) {
        if (!isRefreshing) {
          isRefreshing = true;
          try {
            const refreshRes = await fetch(`${ENV.API_URL}/auth/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (refreshRes.ok) {
              const resData = await refreshRes.json();
              const newAccessToken = resData.data.access_token;
              const newRefreshToken = resData.data.refresh_token;
              localStorage.setItem(TOKEN_STORAGE_KEY, newAccessToken);
              localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, newRefreshToken);
              isRefreshing = false;
              onRefreshed(newAccessToken);

              // Retry original request with new token
              headers.set('Authorization', `Bearer ${newAccessToken}`);
              const retryRes = await fetch(url, { ...options, headers });
              return handleResponse<T>(retryRes);
            } else {
              // Refresh failed: clear tokens
              localStorage.removeItem(TOKEN_STORAGE_KEY);
              localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
              isRefreshing = false;
            }
          } catch {
            isRefreshing = false;
          }
        } else {
          // Wait for existing refresh in flight
          return new Promise((resolve, reject) => {
            addRefreshSubscriber(async (newToken) => {
              headers.set('Authorization', `Bearer ${newToken}`);
              try {
                const retryRes = await fetch(url, { ...options, headers });
                resolve(await handleResponse<T>(retryRes));
              } catch (err) {
                reject(err);
              }
            });
          });
        }
      }
    }

    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    throw new ApiClientError(
      {
        code: 'NETWORK_ERROR',
        message: error instanceof Error ? error.message : 'Unable to connect to Enermax API server',
        request_id: 'local_failure',
      },
      0
    );
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');

  if (!response.ok) {
    const requestId = response.headers.get('x-request-id') || 'unknown';
    if (isJson) {
      const errorBody = await response.json();
      if (errorBody && errorBody.error) {
        throw new ApiClientError(errorBody.error, response.status);
      }
    }
    throw new ApiClientError(
      {
        code: `HTTP_${response.status}`,
        message: response.statusText || 'An unexpected server error occurred',
        request_id: requestId,
      },
      response.status
    );
  }

  if (isJson) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

export { ApiClientError };
