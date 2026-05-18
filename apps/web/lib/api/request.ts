import { sleep } from "../utils"
import { ApiError, TimeoutError } from "./types"
import type { RequestConfig } from "./types"

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim()
const API_PREFIX = (process.env.NEXT_PUBLIC_API_PREFIX || "/api/v1").trim()
const GET_CACHE_TTL_MS = 5000
const getCache = new Map<string, { expiresAt: number; value: unknown }>()
const inFlightGets = new Map<string, Promise<unknown>>()

function showToast(type: "success" | "error", message: string) {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("api-toast", { detail: { type, message } }))
  }
}

function buildUrl(endpoint: string, params?: RequestConfig["params"]): string {
  const normalizedEndpoint = endpoint.startsWith("/api/v1")
    ? endpoint.replace(/^\/api\/v1/, API_PREFIX)
    : endpoint
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost"
  const url = API_BASE ? new URL(normalizedEndpoint, API_BASE) : new URL(normalizedEndpoint, origin)
  Object.entries(params || {}).forEach(([key, value]) => {
    const values = Array.isArray(value) ? value : [value]
    values.forEach((item) => {
      if (item !== undefined && item !== null) url.searchParams.append(key, String(item))
    })
  })
  return url.toString()
}

// CRG: Keep retry/timeout behavior reusable as API endpoint modules are split apart.
export async function requestWithRetry<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
  const { method = "GET", headers = {}, body, params, timeout = 15000, retries = 2, retryDelay = 1000, skipToast = false } = config
  const url = buildUrl(endpoint, params)
  const cacheKey = method === "GET" && !body ? url : ""
  if (cacheKey) {
    const cached = getCache.get(cacheKey)
    if (cached && cached.expiresAt > Date.now()) return cached.value as T // CRG: Short-cache hot dashboard reads to avoid repeated identical API calls.
    const pending = inFlightGets.get(cacheKey)
    if (pending) return pending as Promise<T> // CRG: De-duplicate concurrent GETs from parallel UI widgets.
  }
  const pending = requestFresh<T>({ method, headers, body, timeout, retries, retryDelay, skipToast }, url, cacheKey)
  if (!cacheKey) return pending
  inFlightGets.set(cacheKey, pending)
  try {
    const value = await pending
    getCache.set(cacheKey, { expiresAt: Date.now() + GET_CACHE_TTL_MS, value })
    return value
  } finally {
    inFlightGets.delete(cacheKey)
  }
}

async function requestFresh<T>(
  config: Required<Pick<RequestConfig, "method" | "headers" | "timeout" | "retries" | "retryDelay" | "skipToast">> & Pick<RequestConfig, "body">,
  url: string,
  cacheKey: string
): Promise<T> {
  const { method, headers, body, timeout, retries, retryDelay, skipToast } = config
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeout)
    try {
      const init: RequestInit = {
        method,
        headers: { Accept: "application/json", ...(body && !(body instanceof FormData) ? { "Content-Type": "application/json" } : {}), ...headers },
        signal: controller.signal,
      }
      if (body) init.body = body instanceof FormData ? body : JSON.stringify(body) // CRG: exactOptionalPropertyTypes forbids body: undefined.
      const response = await fetch(url, init)
      if (!response.ok) {
        const fallback = `HTTP ${response.status}`
        const err = await response.json().catch(() => undefined)
        // CRG: FastAPI returns 422 detail as an array of validation errors.
        let message = err?.detail || err?.message || fallback
        if (Array.isArray(message)) {
          message = message.map((d: any) => `${d.loc?.join('.') || 'body'}: ${d.msg}`).join('; ')
        } else if (typeof message === 'object' && message !== null) {
          message = JSON.stringify(message)
        }
        throw new ApiError(message, response.status)
      }
      if (!cacheKey) getCache.clear() // CRG: Mutations invalidate short-lived GET cache so UI refreshes do not reuse stale reads.
      return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
    } catch (err) {
      lastError = err instanceof Error && err.name === "AbortError" ? new TimeoutError() : (err as Error)
      const retryable = lastError instanceof TimeoutError || (lastError instanceof ApiError && lastError.statusCode >= 500)
      if (attempt < retries && retryable) await sleep(retryDelay * Math.pow(2, attempt))
      else break
    } finally {
      clearTimeout(timer)
    }
  }
  if (!skipToast && lastError) showToast("error", lastError.message)
  throw lastError
}
