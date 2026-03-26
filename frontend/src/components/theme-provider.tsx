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

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useUIStore((s) => s.theme)
  // Read palette once from injected config (synchronous, no flash)
  const palette = React.useMemo(() => getAdminConfig().colorPalette ?? null, [])

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
