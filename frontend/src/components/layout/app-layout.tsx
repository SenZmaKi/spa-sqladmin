import React from 'react'
import { cn } from '@/lib/utils'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { useSite } from '@/hooks/use-site'
import { useUIStore } from '@/stores/ui-store'
import { Skeleton } from '@/components/ui/skeleton'

interface Breadcrumb {
  label: string
  href?: string
}

interface AppLayoutProps {
  title: string
  breadcrumbs?: Breadcrumb[]
  children: React.ReactNode
}

export function AppLayout({ title, breadcrumbs, children }: AppLayoutProps) {
  const { data: site, isLoading } = useSite()
  const { sidebarCollapsed: collapsed, setSidebarCollapsed: setCollapsed } = useUIStore()
  const [mobileOpen, setMobileOpen] = React.useState(false)

  React.useEffect(() => {
    if (site?.title) {
      document.title = site.title
    }
    if (site?.favicon_url) {
      let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
      if (!link) {
        link = document.createElement('link')
        link.rel = 'icon'
        document.head.appendChild(link)
      }
      link.href = site.favicon_url
    }
  }, [site?.title, site?.favicon_url])

  if (isLoading || !site) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="space-y-4 w-64">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar
        site={site}
        collapsed={collapsed}
        onCollapsedChange={setCollapsed}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <div
        className={cn(
          'flex flex-col transition-all duration-300',
          collapsed ? 'lg:ml-16' : 'lg:ml-64'
        )}
      >
        <Header
          title={title}
          breadcrumbs={breadcrumbs}
          onMobileMenuToggle={() => setMobileOpen(!mobileOpen)}
        />

        <main className="flex-1 p-4 sm:p-6">{children}</main>
      </div>
    </div>
  )
}
