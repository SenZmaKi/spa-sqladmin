import React from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { AppLayout } from '@/components/layout/app-layout'
import { useList } from '@/hooks/use-list'
import { deleteRecords, getExportUrl } from '@/lib/api'
import { cn, formatNumber } from '@/lib/utils'
import { Button, buttonVariants } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Combobox, type ComboboxOption } from '@/components/ui/combobox'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table'
import {
  Plus,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Eye,
  Pencil,
  Trash2,
  Download,
  Columns3,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  X,
} from 'lucide-react'
import type { ListData, ColumnDef, FilterDef, RelationValue } from '@/lib/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyLinkTo = any

interface ListPageProps {
  identity: string
}

export function ListPage({ identity }: ListPageProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [page, setPage] = React.useState(1)
  const [pageSize, setPageSize] = React.useState<number | undefined>(undefined)
  const [search, setSearch] = React.useState('')
  const [searchInput, setSearchInput] = React.useState('')
  const [sortBy, setSortBy] = React.useState<string | undefined>(undefined)
  const [sort, setSort] = React.useState<'asc' | 'desc' | undefined>(undefined)
  const [filters, setFilters] = React.useState<Record<string, string>>({})
  const [selectedRows, setSelectedRows] = React.useState<Set<string>>(new Set())
  const [hiddenColumns, setHiddenColumns] = React.useState<Set<string>>(new Set())
  const [showColumnPicker, setShowColumnPicker] = React.useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)
  const [pendingDeletePks, setPendingDeletePks] = React.useState<string[]>([])
  const columnPickerRef = React.useRef<HTMLDivElement>(null)

  // Reset state when identity changes
  React.useEffect(() => {
    setPage(1)
    setSearch('')
    setSearchInput('')
    setSortBy(undefined)
    setSort(undefined)
    setFilters({})
    setSelectedRows(new Set())
    setHiddenColumns(new Set())
  }, [identity])

  const { data, isLoading, isFetching, error } = useList({
    identity,
    page,
    pageSize,
    search: search || undefined,
    sortBy,
    sort,
    filters,
  })

  // Close column picker on outside click
  React.useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        columnPickerRef.current &&
        !columnPickerRef.current.contains(e.target as Node)
      ) {
        setShowColumnPicker(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const deleteMutation = useMutation({
    mutationFn: (pks: string[]) => deleteRecords(identity, pks),
    onSuccess: () => {
      toast.success('Records deleted successfully')
      setSelectedRows(new Set())
      queryClient.invalidateQueries({ queryKey: ['list', { identity }] })
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to delete records')
    },
  })

  const handleSort = (columnName: string) => {
    if (sortBy === columnName) {
      if (sort === 'asc') {
        setSort('desc')
      } else if (sort === 'desc') {
        setSortBy(undefined)
        setSort(undefined)
      }
    } else {
      setSortBy(columnName)
      setSort('asc')
    }
    setPage(1)
  }

  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== search) {
        setSearch(searchInput)
        setPage(1)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [searchInput]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleDelete = (pks: string[]) => {
    setPendingDeletePks(pks)
    setDeleteDialogOpen(true)
  }

  const handleConfirmDelete = () => {
    deleteMutation.mutate(pendingDeletePks)
    setDeleteDialogOpen(false)
    setPendingDeletePks([])
  }

  const handleFilterChange = (name: string, value: string) => {
    setFilters((prev) => {
      const next = { ...prev }
      if (value) {
        next[name] = value
      } else {
        delete next[name]
      }
      return next
    })
    setPage(1)
  }

  const breadcrumbs = data
    ? [{ label: data.name_plural }]
    : [{ label: identity }]

  return (
    <AppLayout
      title={data?.name_plural || identity}
      breadcrumbs={breadcrumbs}
    >
      {error ? (
        <ErrorState message={(error as Error).message} />
      ) : !data && isLoading ? (
        <ListSkeleton />
      ) : data ? (
        <div className="space-y-4">
          {/* Toolbar — always rendered so search input keeps focus */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              {data.searchable && (
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder={data.search_placeholder || 'Search...'}
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    className="pl-9 w-48 sm:w-64"
                  />
                  {searchInput && (
                    <button
                      type="button"
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      onClick={() => {
                        setSearchInput('')
                        setSearch('')
                        setPage(1)
                      }}
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              )}

              {/* Filters */}
              {data.filters.map((filter) => (
                <FilterControl
                  key={filter.name}
                  filter={filter}
                  value={filters[filter.name] || ''}
                  onChange={(val) => handleFilterChange(filter.name, val)}
                />
              ))}
            </div>

            <div className="flex items-center gap-2">
              {/* Column visibility */}
              <div className="relative" ref={columnPickerRef}>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowColumnPicker(!showColumnPicker)}
                >
                  <Columns3 className="h-4 w-4" />
                  <span className="hidden sm:inline">Columns</span>
                </Button>
                {showColumnPicker && (
                  <div className="absolute right-0 top-full z-50 mt-1 w-48 rounded-md border bg-popover p-2 shadow-md">
                    {data.columns.map((col) => (
                      <label
                        key={col.name}
                        className="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent cursor-pointer"
                      >
                        <Checkbox
                          checked={!hiddenColumns.has(col.name)}
                          onChange={() => {
                            setHiddenColumns((prev) => {
                              const next = new Set(prev)
                              if (next.has(col.name)) {
                                next.delete(col.name)
                              } else {
                                next.add(col.name)
                              }
                              return next
                            })
                          }}
                        />
                        <span>{col.label}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Export */}
              {data.permissions.can_export &&
                data.export_types.map((type) => (
                  <a
                    key={type}
                    href={getExportUrl(identity, type)}
                    target="_blank"
                    rel="noopener"
                    className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                  >
                    <Download className="h-4 w-4" />
                    <span className="hidden sm:inline">
                      {type.toUpperCase()}
                    </span>
                  </a>
                ))}

              {/* Create */}
              {data.permissions.can_create && (
                <Link
                  to={`/${identity}/create` as AnyLinkTo}
                  className={cn(buttonVariants({ size: 'sm' }))}
                >
                  <Plus className="h-4 w-4" />
                  <span className="hidden sm:inline">Create</span>
                </Link>
              )}
            </div>
          </div>

          {/* Bulk actions */}
          {selectedRows.size > 0 && data.permissions.can_delete && (
            <div className="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
              <span className="text-sm font-medium">
                {selectedRows.size} selected
              </span>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => handleDelete(Array.from(selectedRows))}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedRows(new Set())}
              >
                Clear
              </Button>
            </div>
          )}

          {/* Table — shows loading overlay during refetch */}
          <div className={cn(isFetching && 'opacity-50 pointer-events-none transition-opacity')}>
            <DataTable
              data={data}
              hiddenColumns={hiddenColumns}
              selectedRows={selectedRows}
              onSelectedRowsChange={setSelectedRows}
              sortBy={sortBy}
              sort={sort}
              onSort={handleSort}
              onDelete={handleDelete}
              identity={identity}
            />
          </div>

          {/* Pagination */}
          <PaginationControls
            page={data.page}
            pageSize={data.page_size}
            count={data.count}
            pageSizeOptions={data.page_size_options}
            onPageChange={setPage}
            onPageSizeChange={(size) => {
              setPageSize(size)
              setPage(1)
            }}
          />
        </div>
      ) : null}

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Delete</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {pendingDeletePks.length} {pendingDeletePks.length === 1 ? 'record' : 'records'}? This action cannot be undone.
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

// ─── Filter Control ──────────────────────────────────────────────────────────

function FilterControl({
  filter,
  value,
  onChange,
}: {
  filter: FilterDef
  value: string
  onChange: (val: string) => void
}) {
  if (filter.options && !filter.has_operator) {
    return (
      <Combobox
        options={[
          { value: '', label: `All` },
          ...filter.options.map(([v, l]) => ({ value: v, label: l })),
        ]}
        value={value}
        onChange={(val) => {
          const v = typeof val === 'string' ? val : val[0] || ''
          onChange(v)
        }}
        placeholder={`Filter ${filter.title}...`}
        className="w-36 text-xs h-8"
      />
    )
  }

  if (filter.has_operator && filter.operations) {
    const opKey = `${filter.name}-op`
    const currentOp = value ? value.split(':')[0] : ''
    const currentVal = value ? value.split(':').slice(1).join(':') : ''

    return (
      <div className="flex items-center gap-1">
        <Select
          value={currentOp}
          onChange={(e) => {
            const op = e.target.value
            if (op && currentVal) {
              onChange(`${op}:${currentVal}`)
            } else if (!op) {
              onChange('')
            }
          }}
          className="w-24 text-xs h-8"
        >
          <option value="">{filter.title}</option>
          {filter.operations.map(([val, label]) => (
            <option key={val} value={val}>
              {label}
            </option>
          ))}
        </Select>
        {currentOp && (
          <Input
            value={currentVal}
            onChange={(e) => onChange(`${currentOp}:${e.target.value}`)}
            placeholder="Value..."
            className="w-24 text-xs h-8"
          />
        )}
      </div>
    )
  }

  return (
    <Input
      placeholder={filter.title}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-36 text-xs h-8"
    />
  )
}

// ─── Data Table ──────────────────────────────────────────────────────────────

function DataTable({
  data,
  hiddenColumns,
  selectedRows,
  onSelectedRowsChange,
  sortBy,
  sort,
  onSort,
  onDelete,
  identity,
}: {
  data: ListData
  hiddenColumns: Set<string>
  selectedRows: Set<string>
  onSelectedRowsChange: (rows: Set<string>) => void
  sortBy?: string
  sort?: 'asc' | 'desc'
  onSort: (col: string) => void
  onDelete: (pks: string[]) => void
  identity: string
}) {
  const visibleColumns = data.columns.filter(
    (col) => !hiddenColumns.has(col.name)
  )
  const allPks = data.rows.map((row) => String(row._pk ?? row.pk ?? row.id ?? ''))
  const allSelected =
    allPks.length > 0 && allPks.every((pk) => selectedRows.has(pk))

  const toggleAll = () => {
    if (allSelected) {
      onSelectedRowsChange(new Set())
    } else {
      onSelectedRowsChange(new Set(allPks))
    }
  }

  const toggleRow = (pk: string) => {
    const next = new Set(selectedRows)
    if (next.has(pk)) {
      next.delete(pk)
    } else {
      next.add(pk)
    }
    onSelectedRowsChange(next)
  }

  return (
    <div className="rounded-lg border">
      {/* Desktop Table */}
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              {data.permissions.can_delete && (
                <TableHead className="w-10">
                  <Checkbox
                    checked={allSelected}
                    onChange={toggleAll}
                  />
                </TableHead>
              )}
              {visibleColumns.map((col) => (
                <TableHead key={col.name}>
                  {col.sortable ? (
                    <button
                      className="flex items-center gap-1 hover:text-foreground transition-colors -ml-1 px-1 py-0.5 rounded"
                      onClick={() => onSort(col.name)}
                    >
                      {col.label}
                      {sortBy === col.name ? (
                        sort === 'asc' ? (
                          <ArrowUp className="h-3.5 w-3.5" />
                        ) : (
                          <ArrowDown className="h-3.5 w-3.5" />
                        )
                      ) : (
                        <ArrowUpDown className="h-3.5 w-3.5 opacity-40" />
                      )}
                    </button>
                  ) : (
                    col.label
                  )}
                </TableHead>
              ))}
              <TableHead className="w-24 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={
                    visibleColumns.length +
                    (data.permissions.can_delete ? 2 : 1)
                  }
                  className="h-24 text-center text-muted-foreground"
                >
                  No records found.
                </TableCell>
              </TableRow>
            ) : (
              data.rows.map((row, rowIdx) => {
                const pk = String(row._pk ?? row.pk ?? row.id ?? rowIdx)
                return (
                  <TableRow
                    key={pk}
                    data-state={selectedRows.has(pk) ? 'selected' : undefined}
                  >
                    {data.permissions.can_delete && (
                      <TableCell>
                        <Checkbox
                          checked={selectedRows.has(pk)}
                          onChange={() => toggleRow(pk)}
                        />
                      </TableCell>
                    )}
                    {visibleColumns.map((col) => (
                      <TableCell key={col.name}>
                        <CellValue
                          value={row[col.name]}
                          column={col}
                        />
                      </TableCell>
                    ))}
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        {data.permissions.can_view_details && (
                          <Link
                            to={`/${identity}/${pk}` as AnyLinkTo}
                            className={cn(buttonVariants({ variant: 'ghost', size: 'icon' }), 'h-8 w-8')}
                          >
                            <Eye className="h-4 w-4" />
                          </Link>
                        )}
                        {data.permissions.can_edit && (
                          <Link
                            to={`/${identity}/${pk}/edit` as AnyLinkTo}
                            className={cn(buttonVariants({ variant: 'ghost', size: 'icon' }), 'h-8 w-8')}
                          >
                            <Pencil className="h-4 w-4" />
                          </Link>
                        )}
                        {data.permissions.can_delete && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => onDelete([pk])}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden divide-y">
        {data.rows.length === 0 ? (
          <div className="p-6 text-center text-muted-foreground">
            No records found.
          </div>
        ) : (
          data.rows.map((row, rowIdx) => {
            const pk = String(row._pk ?? row.pk ?? row.id ?? rowIdx)
            return (
              <div key={pk} className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {data.permissions.can_delete && (
                      <Checkbox
                        checked={selectedRows.has(pk)}
                        onChange={() => toggleRow(pk)}
                      />
                    )}
                    <span className="font-medium text-sm">#{pk}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {data.permissions.can_view_details && (
                      <Link
                        to={`/${identity}/${pk}` as AnyLinkTo}
                        className={cn(buttonVariants({ variant: 'ghost', size: 'icon' }), 'h-7 w-7')}
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </Link>
                    )}
                    {data.permissions.can_edit && (
                      <Link
                        to={`/${identity}/${pk}/edit` as AnyLinkTo}
                        className={cn(buttonVariants({ variant: 'ghost', size: 'icon' }), 'h-7 w-7')}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Link>
                    )}
                    {data.permissions.can_delete && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive"
                        onClick={() => onDelete([pk])}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                  {visibleColumns.slice(0, 6).map((col) => (
                    <div key={col.name}>
                      <span className="text-muted-foreground text-xs">
                        {col.label}
                      </span>
                      <div className="truncate">
                        <CellValue
                          value={row[col.name]}
                          column={col}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

// ─── Cell Value Renderer ─────────────────────────────────────────────────────

function CellValue({
  value,
  column,
}: {
  value: any
  column: ColumnDef
}) {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground">—</span>
  }

  if (typeof value === 'boolean') {
    return value ? (
      <Badge variant="success">✓</Badge>
    ) : (
      <Badge variant="destructive">✗</Badge>
    )
  }

  // Relation object
  if (column.is_relation && value && typeof value === 'object') {
    if (Array.isArray(value)) {
      return (
        <span>
          {(value as RelationValue[]).map((rel, i) => (
            <span key={rel.pk}>
              {i > 0 && ', '}
              <Link
                to={`/${rel.identity}/${rel.pk}` as AnyLinkTo}
                className="text-primary hover:underline"
              >
                {rel.repr}
              </Link>
            </span>
          ))}
        </span>
      )
    }
    const rel = value as RelationValue
    if (rel.identity && rel.pk) {
      return (
        <Link
          to={`/${rel.identity}/${rel.pk}` as AnyLinkTo}
          className="text-primary hover:underline"
        >
          {rel.repr}
        </Link>
      )
    }
  }

  // Date strings
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}(T|\s)/.test(value)) {
    try {
      const d = new Date(value)
      return (
        <span title={value}>
          {d.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}
          {value.includes('T') &&
            ` ${d.toLocaleTimeString(undefined, {
              hour: '2-digit',
              minute: '2-digit',
            })}`}
        </span>
      )
    } catch {
      return <span>{String(value)}</span>
    }
  }

  if (typeof value === 'number') {
    return <span className="truncate max-w-xs block">{formatNumber(value)}</span>
  }

  return <span className="truncate max-w-xs block">{String(value)}</span>
}

// ─── Pagination ──────────────────────────────────────────────────────────────

function PaginationControls({
  page,
  pageSize,
  count,
  pageSizeOptions,
  onPageChange,
  onPageSizeChange,
}: {
  page: number
  pageSize: number
  count: number
  pageSizeOptions: number[]
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  const start = (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, count)

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="text-sm text-muted-foreground">
        {count > 0 ? (
          <>
            Showing {start}–{end} of {count} results
          </>
        ) : (
          'No results'
        )}
      </div>
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1 text-sm">
          <span className="text-muted-foreground hidden sm:inline">Rows:</span>
          <Select
            value={String(pageSize)}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="w-16 h-8 text-xs"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={String(size)}>
                {size}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            disabled={page <= 1}
            onClick={() => onPageChange(1)}
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="px-2 text-sm text-muted-foreground">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            disabled={page >= totalPages}
            onClick={() => onPageChange(totalPages)}
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

// ─── Skeletons & Error ───────────────────────────────────────────────────────

function ListSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-9 w-24" />
      </div>
      <div className="rounded-lg border">
        <div className="space-y-0">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-4 p-3 border-b last:border-0"
            >
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-48" />
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="rounded-full bg-destructive/10 p-3 mb-4">
        <X className="h-6 w-6 text-destructive" />
      </div>
      <h2 className="text-lg font-semibold">Something went wrong</h2>
      <p className="text-sm text-muted-foreground mt-1">{message}</p>
    </div>
  )
}
