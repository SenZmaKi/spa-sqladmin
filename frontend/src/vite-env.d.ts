/// <reference types="vite/client" />

interface AdminConfig {
  baseUrl: string
  apiUrl: string
}

interface Window {
  __ADMIN_CONFIG__?: AdminConfig
}
