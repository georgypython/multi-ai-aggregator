import tg from './telegram'

type RequestOptions = {
  method?: 'GET' | 'POST'
  body?: unknown
  retryOnUnauthorized?: boolean
  headers?: Record<string, string>
}

export type PaymentProduct = {
  plan_id: string
  tariff_code: string
  name: string
  display_name: string
  description: string | null
  billing_interval: string
  duration_days: number
  price_rub: string
  tokens_amount: string
  is_vpn_bonus_enabled: boolean
  llm_max_limit?: number
  image_max_limit?: number
  video_max_limit?: number
}

export type PaymentMethod = {
  code: string
  enabled: boolean
  is_soon: boolean
}

export type InvoiceResponse = {
  order_id: string
  payment_intent_id: string
  payment_url: string | null
  amount: string
  currency: string
  provider: string
  payment_method: string
}

const API_BASE = String(import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
const API_V1 = `${API_BASE}/v1`

async function parseError(response: Response): Promise<Error> {
  try {
    const data = (await response.json()) as { detail?: string }
    if (typeof data.detail === 'string' && data.detail.trim()) {
      return new Error(data.detail)
    }
  } catch {
    // Ignore JSON parse errors and fallback to status text.
  }
  return new Error(`Request failed: ${response.status} ${response.statusText}`)
}

async function refreshSession(): Promise<boolean> {
  const response = await fetch(`${API_V1}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  })
  return response.ok
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body,
    retryOnUnauthorized = true,
    headers = {},
  } = options

  const response = await fetch(`${API_V1}${path}`, {
    method,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: body != null ? JSON.stringify(body) : undefined,
  })

  if (response.status === 401 && retryOnUnauthorized) {
    const refreshed = await refreshSession()
    if (refreshed) {
      return request<T>(path, { ...options, retryOnUnauthorized: false })
    }
  }

  if (!response.ok) {
    throw await parseError(response)
  }

  return (await response.json()) as T
}

export async function createMiniAppSession(initData: string): Promise<void> {
  const token = window.btoa(initData)

  const response = await fetch(`${API_V1}/users/me`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw await parseError(response)
  }
}

export async function fetchPaymentProducts(): Promise<PaymentProduct[]> {
  const data = await request<{ products: PaymentProduct[] }>('/invoice/products')
  return data.products
}

export async function fetchPaymentMethods(): Promise<PaymentMethod[]> {
  const data = await request<{ methods: PaymentMethod[] }>('/invoice/methods')
  return data.methods
}

export async function createInvoice(planId: string, paymentMethod: string): Promise<InvoiceResponse> {
  return request<InvoiceResponse>('/invoice', {
    method: 'POST',
    body: {
      plan_id: planId,
      payment_method: paymentMethod,
    },
  })
}

export function openPaymentLink(url: string): void {
  if (tg.isAvailable) {
    tg.openLink(url)
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}
