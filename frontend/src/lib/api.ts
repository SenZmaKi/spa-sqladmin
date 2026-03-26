import type { AdminConfig, SiteData, ListData, DetailData, FormSchema, AuthStatus } from './types'

function getConfig(): AdminConfig {
  return (
    (window as any).__ADMIN_CONFIG__ || {
      baseUrl: '/admin',
      apiUrl: '/admin/api',
    }
  )
}

export function getAdminConfig(): AdminConfig {
  return getConfig()
}

function apiUrl(path: string): string {
  return `${getConfig().apiUrl}${path}`
}

export function getBaseUrl(): string {
  return getConfig().baseUrl
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    const config = getConfig()
    const loginPath = `${config.baseUrl}/login`
    // Avoid infinite redirect if already on the login page
    if (!window.location.pathname.startsWith(loginPath)) {
      window.location.href = loginPath
    }
    throw new Error('Not authenticated')
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: response.statusText }))
    throw new Error(data.error || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function fetchSite(): Promise<SiteData> {
  const res = await fetch(apiUrl('/site'), { credentials: 'include' })
  return handleResponse<SiteData>(res)
}

export async function fetchAuthStatus(): Promise<AuthStatus> {
  const res = await fetch(apiUrl('/auth-status'), { credentials: 'include' })
  return handleResponse<AuthStatus>(res)
}

export interface ListParams {
  identity: string
  page?: number
  pageSize?: number
  search?: string
  sortBy?: string
  sort?: 'asc' | 'desc'
  filters?: Record<string, string>
}

export async function fetchList(params: ListParams): Promise<ListData> {
  const { identity, page = 1, pageSize, search, sortBy, sort, filters = {} } = params
  const qp = new URLSearchParams()
  qp.set('page', String(page))
  if (pageSize) qp.set('pageSize', String(pageSize))
  if (search) qp.set('search', search)
  if (sortBy) qp.set('sortBy', sortBy)
  if (sort) qp.set('sort', sort)
  for (const [key, value] of Object.entries(filters)) {
    if (value) qp.set(key, value)
  }
  const res = await fetch(apiUrl(`/${identity}/list?${qp}`), { credentials: 'include' })
  return handleResponse<ListData>(res)
}

export async function fetchDetail(identity: string, pk: string): Promise<DetailData> {
  const res = await fetch(apiUrl(`/${identity}/detail/${pk}`), { credentials: 'include' })
  return handleResponse<DetailData>(res)
}

export async function fetchFormSchema(
  identity: string,
  action: 'create' | 'edit',
  pk?: string
): Promise<FormSchema> {
  const qp = new URLSearchParams({ action })
  if (pk) qp.set('pk', pk)
  const res = await fetch(apiUrl(`/${identity}/form-schema?${qp}`), {
    credentials: 'include',
  })
  return handleResponse<FormSchema>(res)
}

export async function submitCreate(
  identity: string,
  data: Record<string, any>
): Promise<{ success: boolean; pk: string; repr: string; errors?: Record<string, string[]> }> {
  const res = await fetch(apiUrl(`/${identity}/create`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  })
  if (res.status === 400) {
    const body = await res.json()
    if (body.errors) {
      return { success: false, pk: '', repr: '', errors: body.errors }
    }
    throw new Error(body.error || 'Validation failed')
  }
  return handleResponse(res)
}

export async function submitEdit(
  identity: string,
  pk: string,
  data: Record<string, any>
): Promise<{ success: boolean; pk: string; repr: string; errors?: Record<string, string[]> }> {
  const res = await fetch(apiUrl(`/${identity}/edit/${pk}`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  })
  if (res.status === 400) {
    const body = await res.json()
    if (body.errors) {
      return { success: false, pk: '', repr: '', errors: body.errors }
    }
    throw new Error(body.error || 'Validation failed')
  }
  return handleResponse(res)
}

export async function deleteRecords(
  identity: string,
  pks: string[]
): Promise<{ success: boolean }> {
  const res = await fetch(apiUrl(`/${identity}/delete?pks=${pks.join(',')}`), {
    method: 'DELETE',
    credentials: 'include',
  })
  return handleResponse(res)
}

export function getExportUrl(identity: string, exportType: string): string {
  return apiUrl(`/${identity}/export/${exportType}`)
}

export async function ajaxLookup(
  identity: string,
  name: string,
  term: string
): Promise<{ results: { id: string; text: string }[] }> {
  const qp = new URLSearchParams({ name, term })
  const res = await fetch(apiUrl(`/${identity}/ajax/lookup?${qp}`), {
    credentials: 'include',
  })
  return handleResponse(res)
}

export async function login(formData: FormData): Promise<{ success: boolean }> {
  const res = await fetch(apiUrl('/login'), {
    method: 'POST',
    credentials: 'include',
    body: formData,
  })
  if (res.status === 401) {
    throw new Error('Invalid credentials')
  }
  return handleResponse(res)
}

export async function logout(): Promise<void> {
  await fetch(apiUrl('/logout'), { credentials: 'include' })
}
