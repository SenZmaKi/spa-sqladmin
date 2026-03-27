import React from 'react'
import { Link } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/app-layout'
import { useSite } from '@/hooks/use-site'
import { resolveIcon, SvgIcon } from '@/components/layout/sidebar'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ChevronDown,
  ChevronRight,
  ExternalLink,
  LayoutDashboard,
} from 'lucide-react'
import type { MenuItem, ModelInfo, SiteData } from '@/lib/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyLinkTo = any

/** Derive the navigation href for any menu item. */
function getItemHref(item: MenuItem, baseUrl: string): string {
  if (item.is_model) return `/${item.identity}/list`
  if (item.is_link && item.url) return item.url   // DirectLinkMenu (embed_docs)
  return `${baseUrl}/${item.identity}`             // LinkView with get_response
}

/** True when the href is an external / absolute URL. */
function isExternal(href: string): boolean {
  return href.startsWith('http://') || href.startsWith('https://')
}

export function DashboardPage() {
  const { data: site, isLoading } = useSite()

  return (
    <AppLayout title="Dashboard">
      {isLoading || !site ? (
        <DashboardSkeleton />
      ) : site.menu.length === 0 ? (
        <EmptyState />
      ) : (
        <DashboardContent site={site} />
      )}
    </AppLayout>
  )
}

function DashboardSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-16 mt-1" />
          </CardHeader>
        </Card>
      ))}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <LayoutDashboard className="h-16 w-16 text-muted-foreground/50 mb-4" />
      <h2 className="text-xl font-semibold text-muted-foreground">
        No views registered
      </h2>
      <p className="text-sm text-muted-foreground mt-1">
        Add views to your admin to see them here.
      </p>
    </div>
  )
}

function DashboardContent({ site }: { site: SiteData }) {
  const { menu, models, base_url: baseUrl } = site
  const hasCategories = menu.some((m) => m.type === 'category')

  if (hasCategories) {
    return (
      <div className="space-y-6">
        {menu.map((menuItem, i) => {
          if (menuItem.type === 'category') {
            return (
              <CategorySection
                key={`${menuItem.name}-${i}`}
                category={menuItem}
                models={models}
                baseUrl={baseUrl}
              />
            )
          }
          if (!menuItem.identity) return null
          return (
            <div
              key={`${menuItem.name}-${i}`}
              className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
            >
              <ViewCard item={menuItem} models={models} baseUrl={baseUrl} />
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {menu
        .filter((m) => m.type === 'item' && m.identity)
        .map((item, i) => (
          <ViewCard key={`${item.identity}-${i}`} item={item} models={models} baseUrl={baseUrl} />
        ))}
    </div>
  )
}

function CategorySection({
  category,
  models,
  baseUrl,
}: {
  category: MenuItem
  models: ModelInfo[]
  baseUrl: string
}) {
  const [expanded, setExpanded] = React.useState(true)
  const children = (category.children || []).filter((c) => c.identity)

  if (children.length === 0) return null

  return (
    <div>
      <button
        className="flex items-center gap-2 mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
        {category.name}
      </button>
      {expanded && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {children.map((item, i) => (
            <ViewCard key={`${item.identity}-${i}`} item={item} models={models} baseUrl={baseUrl} />
          ))}
        </div>
      )}
    </div>
  )
}

function ViewCard({
  item,
  models,
  baseUrl,
}: {
  item: MenuItem
  models: ModelInfo[]
  baseUrl: string
}) {
  const modelInfo = item.is_model
    ? models.find((m) => m.identity === item.identity)
    : undefined
  const displayName = modelInfo?.name_plural ?? item.name
  const resolved = resolveIcon(item.icon)
  const href = getItemHref(item, baseUrl)
  const external = isExternal(href)

  const cardContent = (
    <Card className="h-full transition-all duration-200 hover:shadow-md hover:border-primary/40 cursor-pointer">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary/20">
            {resolved.type === 'lucide' ? (
              <resolved.icon className="h-4 w-4" />
            ) : (
              <SvgIcon svg={resolved.svg} className="h-4 w-4" />
            )}
          </div>
          <span className="group-hover:text-primary transition-colors flex-1">
            {displayName}
          </span>
          {external && (
            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />
          )}
        </CardTitle>
      </CardHeader>
    </Card>
  )

  if (external) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="block group">
        {cardContent}
      </a>
    )
  }

  return (
    <Link to={href as AnyLinkTo} className="block group">
      {cardContent}
    </Link>
  )
}

