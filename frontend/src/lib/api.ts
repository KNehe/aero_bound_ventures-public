/**
 * Centralized API Client with HTTP-only cookie support.
 *
 * This module provides a unified way to make API calls with:
 * - Automatic cookie credentials inclusion
 * - Consistent error handling
 * - 401 response detection for automatic logout
 * - TypeScript support
 */

const API_BASE_URL =  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

export class ApiClientError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.detail = detail;
  }
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

interface RequestOptions {
  headers?: Record<string, string>;
  params?: Record<string, string>;
}

/**
 * Internal fetch wrapper that includes credentials for HTTP-only cookies.
 */
async function request<T>(
  method: HttpMethod,
  endpoint: string,
  body?: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const url = new URL(`${API_BASE_URL}${endpoint}`);

  // Add query parameters if provided
  if (options.params) {
    Object.entries(options.params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }

  const headers: Record<string, string> = {
    ...options.headers,
  };

  // Add Content-Type for requests with body
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url.toString(), {
    method,
    headers,
    credentials: 'include', 
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });

  // Handle non-OK responses
  if (!response.ok) {
    let detail: string | undefined;
    try {
      const errorData = await response.json();
      detail = errorData.detail || errorData.message;
    } catch {
      // Response body is not JSON
    }

    throw new ApiClientError(
      response.status,
      detail || `Request failed with status ${response.status}`,
      detail
    );
  }

  // Handle empty responses (204 No Content, etc.)
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return {} as T;
  }

  return response.json();
}

/**
 * API Client object with methods for each HTTP verb.
 */
export const apiClient = {
  /**
   * Make a GET request.
   */
  get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>('GET', endpoint, undefined, options);
  },

  /**
   * Make a POST request.
   */
  post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('POST', endpoint, body, options);
  },

  /**
   * Make a PUT request.
   */
  put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('PUT', endpoint, body, options);
  },

  /**
   * Make a PATCH request.
   */
  patch<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('PATCH', endpoint, body, options);
  },

  /**
   * Make a DELETE request.
   */
  delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>('DELETE', endpoint, undefined, options);
  },

  /**
   * Upload a file using FormData.
   */
  upload<T>(endpoint: string, formData: FormData, options?: RequestOptions): Promise<T> {
    return request<T>('POST', endpoint, formData, options);
  },
};

/**
 * Check if an error is a 401 Unauthorized error.
 */
export function isUnauthorizedError(error: unknown): boolean {
  return error instanceof ApiClientError && error.status === 401;
}

/**
 * Get the API base URL (useful for SSE endpoints).
 */
export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export default apiClient;
