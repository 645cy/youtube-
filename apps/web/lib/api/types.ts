// CRG: Shared API primitives are separated from the large endpoint registry.
export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

export interface RequestConfig {
  method?: HttpMethod
  headers?: Record<string, string>
  body?: unknown
  params?: Record<string, unknown>
  timeout?: number
  retries?: number
  retryDelay?: number
  skipToast?: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  offset: number
  limit: number
}

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code?: string
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export class TimeoutError extends Error {
  constructor(message = "请求超时") {
    super(message)
    this.name = "TimeoutError"
  }
}
