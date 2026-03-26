import { Menu, ChevronRight, Sun, Moon, Monitor } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { useUIStore, type ThemeMode } from '@/stores/ui-store'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyLinkTo = any

const THEME_CYCLE: ThemeMode[] = ['system', 'light', 'dark']

const THEME_META: Record<ThemeMode, { icon: React.ElementType; label: string }> = {
  system: { icon: Monitor, label: 'System' },
  light: { icon: Sun, label: 'Light' },
  dark: { icon: Moon, label: 'Dark' },
}

function ThemeToggle() {
  const { theme, setTheme } = useUIStore()
  const { icon: Icon, label } = THEME_META[theme]
  const nextTheme = THEME_CYCLE[(THEME_CYCLE.indexOf(theme) + 1) % THEME_CYCLE.length]
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(nextTheme)}
      title={`Theme: ${label} — click to switch`}
      className="shrink-0"
    >
      <Icon className="h-4 w-4" />
    </Button>
  )
}

interface Breadcrumb {
  label: string
  href?: string
}

interface HeaderProps {
  title: string
  breadcrumbs?: Breadcrumb[]
  onMobileMenuToggle: () => void
}

export function Header({ title, breadcrumbs = [], onMobileMenuToggle }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 sm:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden shrink-0"
        onClick={onMobileMenuToggle}
      >
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex flex-col gap-0.5 min-w-0 flex-1">
        {breadcrumbs.length > 0 && (
          <nav className="flex items-center gap-1 text-xs text-muted-foreground">
            <Link to={'/' as AnyLinkTo} className="hover:text-foreground transition-colors">
              Home
            </Link>
            {breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1">
                <ChevronRight className="h-3 w-3" />
                {crumb.href ? (
                  <Link to={crumb.href as AnyLinkTo} className="hover:text-foreground transition-colors">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-foreground">{crumb.label}</span>
                )}
              </span>
            ))}
          </nav>
        )}
        <h1 className="text-lg font-semibold leading-tight truncate">{title}</h1>
      </div>

      <ThemeToggle />
    </header>
  )
}
