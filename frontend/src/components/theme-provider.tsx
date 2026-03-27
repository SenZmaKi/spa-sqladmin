import React from 'react'
import { useUIStore } from '@/stores/ui-store'
import { getAdminConfig } from '@/lib/api'

function applyPaletteVars(colors: Record<string, string>) {
  const root = document.documentElement
  for (const [key, value] of Object.entries(colors)) {
    root.style.setProperty(`--${key}`, value)
  }
}

function clearPaletteVars(colors: Record<string, string>) {
  const root = document.documentElement
  for (const key of Object.keys(colors)) {
    root.style.removeProperty(`--${key}`)
  }
}

function applyFontConfig(fontConfig: { url?: string; family?: string } | null | undefined) {
  if (!fontConfig) return
  if (fontConfig.url) {
    const existingLink = document.querySelector<HTMLLinkElement>('link[data-admin-font]')
    if (!existingLink) {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = fontConfig.url
      link.setAttribute('data-admin-font', '')
      document.head.appendChild(link)
    }
  }
  if (fontConfig.family) {
    document.documentElement.style.setProperty('--font-family', fontConfig.family)
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useUIStore((s) => s.theme)
  const config = React.useMemo(() => getAdminConfig(), [])
  const palette = React.useMemo(() => config.colorPalette ?? null, [config])

  React.useEffect(() => {
    applyFontConfig(config.fontConfig)
  }, [config.fontConfig])

  React.useEffect(() => {
    const root = document.documentElement

    const apply = (isDark: boolean) => {
      if (isDark) {
        root.classList.add('dark')
        if (palette?.dark) applyPaletteVars(palette.dark)
        else if (palette?.light) clearPaletteVars(palette.light)
      } else {
        root.classList.remove('dark')
        if (palette?.light) applyPaletteVars(palette.light)
        else if (palette?.dark) clearPaletteVars(palette.dark)
      }
    }

    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      apply(mq.matches)
      const handler = (e: MediaQueryListEvent) => apply(e.matches)
      mq.addEventListener('change', handler)
      return () => mq.removeEventListener('change', handler)
    } else {
      apply(theme === 'dark')
    }
  }, [theme, palette])

  return <>{children}</>
}
