import React from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { AppLayout } from '@/components/layout/app-layout'
import { useDetail } from '@/hooks/use-detail'
import { deleteRecords } from '@/lib/api'
import { cn, formatNumber } from '@/lib/utils'
import { Button, buttonVariants } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableRow,
  TableCell,
} from '@/components/ui/table'
import {
  ArrowLeft,
  Pencil,
  Trash2,
  X,
} from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import type { DetailField, RelationValue } from '@/lib/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyLinkTo = any

interface DetailPageProps {
  identity: string
  pk: string
}

export function DetailPage({ identity, pk }: DetailPageProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useDetail(identity, pk)
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)

  const deleteMutation = useMutation({
    mutationFn: () => deleteRecords(identity, [pk]),
    onSuccess: () => {
      toast.success('Record deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['list'] })
      navigate({ to: `/${identity}/list` as AnyLinkTo })
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to delete')
    },
  })

  const handleDelete = () => {
    setDeleteDialogOpen(true)
  }

  const handleConfirmDelete = () => {
    deleteMutation.mutate()
    setDeleteDialogOpen(false)
  }

  const breadcrumbs = data
    ? [
        { label: data.name, href: `/${identity}/list` },
        { label: data.repr },
      ]
    : [{ label: identity }]

  return (
    <AppLayout
      title={data ? data.repr : 'Loading...'}
      breadcrumbs={breadcrumbs}
    >
      {error ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="rounded-full bg-destructive/10 p-3 mb-4">
            <X className="h-6 w-6 text-destructive" />
          </div>
          <h2 className="text-lg font-semibold">Something went wrong</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {(error as Error).message}
          </p>
        </div>
      ) : isLoading || !data ? (
        <DetailSkeleton />
      ) : (
        <div className="space-y-6">
          {/* Actions bar */}
          <div className="flex flex-wrap items-center gap-2">
            <Link
              to={`/${identity}/list` as AnyLinkTo}
              className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
            >
              <ArrowLeft className="h-4 w-4" />
              Back to List
            </Link>
            <div className="flex-1" />
            {data.permissions.can_edit && (
              <Link
                to={`/${identity}/${pk}/edit` as AnyLinkTo}
                className={cn(buttonVariants({ size: 'sm' }))}
              >
                <Pencil className="h-4 w-4" />
                Edit
              </Link>
            )}
            {data.permissions.can_delete && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            )}
            {/* Custom actions */}
            {Object.entries(data.actions).map(([key, label]) => (
              <Button key={key} variant="outline" size="sm">
                {label}
              </Button>
            ))}
          </div>

          {/* Detail table */}
          <div className="rounded-lg border">
            <Table>
              <TableBody>
                {data.fields.map((field) => (
                  <TableRow key={field.name}>
                    <TableCell className="font-medium text-muted-foreground w-1/3 align-top">
                      {field.label}
                    </TableCell>
                    <TableCell>
                      <DetailValue field={field} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Delete</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this record? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  )
}

function DetailValue({
  field,
}: {
  field: DetailField
}) {
  const { value, is_relation, related } = field

  if (value === null || value === undefined) {
    return <span className="text-muted-foreground">—</span>
  }

  if (typeof value === 'boolean') {
    return value ? (
      <Badge variant="success">True</Badge>
    ) : (
      <Badge variant="destructive">False</Badge>
    )
  }

  // Relations
  if (is_relation && related) {
    if (Array.isArray(related)) {
      if (related.length === 0) {
        return <span className="text-muted-foreground">—</span>
      }
      return (
        <div className="flex flex-wrap gap-1">
          {(related as RelationValue[]).map((rel) => (
            <Link
              key={rel.pk}
              to={`/${rel.identity}/${rel.pk}` as AnyLinkTo}
              className="text-primary hover:underline"
            >
              <Badge variant="outline">{rel.repr}</Badge>
            </Link>
          ))}
        </div>
      )
    }
    const rel = related as RelationValue
    return (
      <Link
        to={`/${rel.identity}/${rel.pk}` as AnyLinkTo}
        className="text-primary hover:underline"
      >
        {rel.repr}
      </Link>
    )
  }

  // JSON
  if (typeof value === 'object') {
    return (
      <pre className="text-xs bg-muted rounded-md p-3 overflow-auto max-h-64 whitespace-pre-wrap">
        {JSON.stringify(value, null, 2)}
      </pre>
    )
  }

  // Date strings
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}(T|\s)/.test(value)) {
    try {
      const d = new Date(value)
      return (
        <span>
          {d.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
          {value.includes('T') &&
            ` at ${d.toLocaleTimeString(undefined, {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}`}
        </span>
      )
    } catch {
      // fall through
    }
  }

  // Numbers with comma formatting
  if (typeof value === 'number') {
    return <span>{formatNumber(value)}</span>
  }

  return <span className="whitespace-pre-wrap break-words">{String(value)}</span>
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Skeleton className="h-9 w-28" />
        <div className="flex-1" />
        <Skeleton className="h-9 w-16" />
        <Skeleton className="h-9 w-20" />
      </div>
      <div className="rounded-lg border divide-y">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex gap-4 p-3">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 flex-1" />
          </div>
        ))}
      </div>
    </div>
  )
}
