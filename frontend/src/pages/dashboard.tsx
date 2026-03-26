import React from 'react'
import { Link } from '@tanstack/react-router'
import { AppLayout } from '@/components/layout/app-layout'
import { useSite } from '@/hooks/use-site'
import { resolveIcon, SvgIcon } from '@/components/layout/sidebar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { buttonVariants } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import {
  List,
  Plus,
  ChevronDown,
  ChevronRight,
  LayoutDashboard,
} from 'lucide-react'
import type { MenuItem, ModelInfo } from '@/lib/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyLinkTo = any

export function DashboardPage() {
  const { data: site, isLoading } = useSite()

  return (
    <AppLayout title="Dashboard">
      {isLoading || !site ? (
        <DashboardSkeleton />
      ) : site.models.length === 0 ? (
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
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-full" />
          </CardContent>
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
        No models registered
      </h2>
      <p className="text-sm text-muted-foreground mt-1">
        Add models to your admin to see them here.
      </p>
    </div>
  )
}

function DashboardContent({
  site,
}: {
  site: { menu: MenuItem[]; models: ModelInfo[] }
}) {
  const hasCategories = site.menu.some((m) => m.type === 'category')

  if (hasCategories) {
    return (
      <div className="space-y-6">
        {site.menu.map((menuItem, i) => {
          if (menuItem.type === 'category') {
            return (
              <CategorySection
                key={`${menuItem.name}-${i}`}
                category={menuItem}
                models={site.models}
              />
            )
          }
          const model = site.models.find((m) => m.identity === menuItem.identity)
          if (!model) return null
          return (
            <div
              key={`${menuItem.name}-${i}`}
              className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
            >
              <ModelCard model={model} />
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {site.models.map((model) => (
        <ModelCard key={model.identity} model={model} />
      ))}
    </div>
  )
}

function CategorySection({
  category,
  models,
}: {
  category: MenuItem
  models: ModelInfo[]
}) {
  const [expanded, setExpanded] = React.useState(true)

  const childModels = (category.children || [])
    .filter((c) => c.identity)
    .map((c) => models.find((m) => m.identity === c.identity))
    .filter(Boolean) as ModelInfo[]

  if (childModels.length === 0) return null

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
          {childModels.map((model) => (
            <ModelCard key={model.identity} model={model} />
          ))}
        </div>
      )}
    </div>
  )
}

function ModelCard({
  model,
}: {
  model: ModelInfo
}) {
  const resolved = resolveIcon(model.icon)

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            {resolved.type === 'lucide' ? (
              <resolved.icon className="h-4 w-4" />
            ) : (
              <SvgIcon svg={resolved.svg} className="h-4 w-4" />
            )}
          </div>
          <span>{model.name_plural}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex gap-2">
        <Link
          to={`/${model.identity}/list` as AnyLinkTo}
          className={cn(buttonVariants({ variant: 'outline', size: 'sm' }), 'flex-1')}
        >
          <List className="h-3.5 w-3.5" />
          View List
        </Link>
        {model.permissions.can_create && (
          <Link
            to={`/${model.identity}/create` as AnyLinkTo}
            className={cn(buttonVariants({ variant: 'outline', size: 'sm' }), 'flex-1')}
          >
            <Plus className="h-3.5 w-3.5" />
            Create
          </Link>
        )}
      </CardContent>
    </Card>
  )
}
