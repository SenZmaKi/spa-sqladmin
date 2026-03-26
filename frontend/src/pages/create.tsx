import React from 'react'
import { Link } from '@tanstack/react-router'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { AppLayout } from '@/components/layout/app-layout'
import { useFormSchema } from '@/hooks/use-form-schema'
import { submitCreate, ajaxLookup } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Button, buttonVariants } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Combobox } from '@/components/ui/combobox'
import { Switch } from '@/components/ui/switch'
import { DateTimePicker } from '@/components/ui/datetime-picker'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Save, X, Loader2 } from 'lucide-react'
import type { FormFieldDef } from '@/lib/types'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyLinkTo = any

interface CreatePageProps {
  identity: string
}

export function CreatePage({ identity }: CreatePageProps) {
  const { data: schema, isLoading, error } = useFormSchema(identity, 'create')
  const [formData, setFormData] = React.useState<Record<string, any>>({})
  const [errors, setErrors] = React.useState<Record<string, string[]>>({})

  // Initialize form data when schema loads
  React.useEffect(() => {
    if (schema) {
      const initial: Record<string, any> = {}
      for (const field of schema.fields) {
        initial[field.name] = field.value ?? (field.type === 'boolean' ? false : '')
      }
      setFormData(initial)
    }
  }, [schema])

  const mutation = useMutation({
    mutationFn: (data: Record<string, any>) => submitCreate(identity, data),
    onSuccess: (result) => {
      if (result.errors) {
        setErrors(result.errors)
        toast.error('Please fix the validation errors')
      } else {
        toast.success(`${schema?.name || 'Record'} created successfully`)
      }
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to create')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})
    mutation.mutate(formData)
  }

  const setField = (name: string, value: any) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[name]
        return next
      })
    }
  }

  const breadcrumbs = schema
    ? [
        { label: schema.name, href: `/${identity}/list` },
        { label: 'Create' },
      ]
    : [{ label: identity }]

  return (
    <AppLayout title={`Create ${schema?.name || ''}`} breadcrumbs={breadcrumbs}>
      {error ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="rounded-full bg-destructive/10 p-3 mb-4">
            <X className="h-6 w-6 text-destructive" />
          </div>
          <p className="text-sm text-muted-foreground">
            {(error as Error).message}
          </p>
        </div>
      ) : isLoading || !schema ? (
        <FormSkeleton />
      ) : (
        <form onSubmit={handleSubmit}>
          <Card className="max-w-3xl mx-auto">
            <CardHeader>
              <CardTitle>Create {schema.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {schema.fields.map((field) => (
                <FormField
                  key={field.name}
                  field={field}
                  value={formData[field.name]}
                  onChange={(val) => setField(field.name, val)}
                  errors={errors[field.name]}
                  identity={identity}
                />
              ))}

              <div className="flex items-center gap-3 pt-4 border-t">
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending && (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                  <Save className="h-4 w-4" />
                  Save
                </Button>
                <Link
                  to={`/${identity}/list` as AnyLinkTo}
                  className={cn(buttonVariants({ variant: 'outline' }))}
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Link>
              </div>
            </CardContent>
          </Card>
        </form>
      )}
    </AppLayout>
  )
}

// ─── Form Field Renderer ─────────────────────────────────────────────────────

export function FormField({
  field,
  value,
  onChange,
  errors,
  identity,
}: {
  field: FormFieldDef
  value: any
  onChange: (value: any) => void
  errors?: string[]
  identity: string
}) {
  const hasError = errors && errors.length > 0

  return (
    <div className="space-y-2">
      <Label htmlFor={field.name} className="flex items-center gap-1">
        {field.label}
        {field.required && <span className="text-destructive">*</span>}
      </Label>

      {field.description && (
        <p className="text-xs text-muted-foreground">{field.description}</p>
      )}

      <FieldInput
        field={field}
        value={value}
        onChange={onChange}
        hasError={hasError}
        identity={identity}
      />

      {hasError && (
        <div className="space-y-1">
          {errors!.map((err, i) => (
            <p key={i} className="text-xs text-destructive">
              {err}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

function FieldInput({
  field,
  value,
  onChange,
  hasError,
  identity,
}: {
  field: FormFieldDef
  value: any
  onChange: (value: any) => void
  hasError?: boolean
  identity: string
}) {
  const errorClass = hasError ? 'border-destructive' : ''

  switch (field.type) {
    case 'boolean':
      return (
        <div className="flex items-center gap-2">
          <Switch
            checked={!!value}
            onCheckedChange={onChange}
          />
          <span className="text-sm text-muted-foreground">
            {value ? 'Yes' : 'No'}
          </span>
        </div>
      )

    case 'textarea':
      return (
        <Textarea
          id={field.name}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          required={field.required}
          rows={4}
          className={errorClass}
        />
      )

    case 'json':
      return (
        <JsonField
          value={value}
          onChange={onChange}
          required={field.required}
          hasError={hasError}
        />
      )

    case 'select':
    case 'relation_select':
      return (
        <Combobox
          options={[
            { value: '', label: '— Select —' },
            ...(field.options?.map((opt) => ({ value: opt.value, label: opt.label })) || []),
          ]}
          value={value ?? ''}
          onChange={(val) => onChange(typeof val === 'string' ? val : val[0] || '')}
          placeholder="— Select —"
          searchPlaceholder="Search options..."
        />
      )

    case 'relation_select_multiple':
      return (
        <MultiSelect
          field={field}
          value={value}
          onChange={onChange}
          hasError={hasError}
        />
      )

    case 'ajax_select':
      return (
        <AjaxSelect
          field={field}
          value={value}
          onChange={onChange}
          identity={identity}
          hasError={hasError}
        />
      )

    case 'integer':
    case 'float':
    case 'decimal':
      return (
        <Input
          id={field.name}
          type="number"
          step={field.type === 'integer' ? '1' : 'any'}
          value={value ?? ''}
          onChange={(e) =>
            onChange(e.target.value === '' ? null : Number(e.target.value))
          }
          required={field.required}
          className={errorClass}
        />
      )

    case 'date':
      return (
        <DateTimePicker
          id={field.name}
          value={value || null}
          onChange={(val) => onChange(val || '')}
          mode="date"
          required={field.required}
          hasError={hasError}
        />
      )

    case 'datetime':
      return (
        <DateTimePicker
          id={field.name}
          value={value || null}
          onChange={(val) => onChange(val || '')}
          mode="datetime"
          required={field.required}
          hasError={hasError}
        />
      )

    case 'file':
      return (
        <Input
          id={field.name}
          type="file"
          onChange={(e) => {
            const file = e.target.files?.[0]
            onChange(file || null)
          }}
          required={field.required}
          className={errorClass}
        />
      )

    default:
      return (
        <Input
          id={field.name}
          type="text"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          required={field.required}
          className={errorClass}
        />
      )
  }
}

// ─── JSON Field ──────────────────────────────────────────────────────────────

function JsonField({
  value,
  onChange,
  required,
  hasError,
}: {
  value: any
  onChange: (value: any) => void
  required?: boolean
  hasError?: boolean
}) {
  const [text, setText] = React.useState(() =>
    value ? JSON.stringify(value, null, 2) : ''
  )
  const [jsonError, setJsonError] = React.useState<string | null>(null)

  const handleBlur = () => {
    if (!text.trim()) {
      setJsonError(null)
      onChange(null)
      return
    }
    try {
      const parsed = JSON.parse(text)
      setJsonError(null)
      onChange(parsed)
    } catch (e: any) {
      setJsonError(e.message)
    }
  }

  return (
    <div className="space-y-1">
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={handleBlur}
        required={required}
        rows={6}
        className={`font-mono text-xs ${hasError || jsonError ? 'border-destructive' : ''}`}
        placeholder='{"key": "value"}'
      />
      {jsonError && (
        <p className="text-xs text-destructive">Invalid JSON: {jsonError}</p>
      )}
    </div>
  )
}

// ─── Multi-Select ────────────────────────────────────────────────────────────

function MultiSelect({
  field,
  value,
  onChange,
  hasError,
}: {
  field: FormFieldDef
  value: any
  onChange: (value: any) => void
  hasError?: boolean
}) {
  const selected = Array.isArray(value) ? value : value ? [value] : []

  return (
    <Combobox
      multiple
      options={field.options?.map((o) => ({ value: o.value, label: o.label })) || []}
      value={selected}
      onChange={(val) => onChange(Array.isArray(val) ? val : [val])}
      placeholder="Select items..."
      searchPlaceholder="Search options..."
    />
  )
}

// ─── AJAX Select ─────────────────────────────────────────────────────────────

function AjaxSelect({
  field,
  value,
  onChange,
  identity,
  hasError,
}: {
  field: FormFieldDef
  value: any
  onChange: (value: any) => void
  identity: string
  hasError?: boolean
}) {
  const [query, setQuery] = React.useState('')
  const [results, setResults] = React.useState<{ id: string; text: string }[]>(
    []
  )
  const [loading, setLoading] = React.useState(false)
  const [showResults, setShowResults] = React.useState(false)
  const [selectedLabel, setSelectedLabel] = React.useState(
    field.value_label || ''
  )
  const wrapperRef = React.useRef<HTMLDivElement>(null)
  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)

  React.useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(e.target as Node)
      ) {
        setShowResults(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const doSearch = (term: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!term.trim()) {
      setResults([])
      return
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await ajaxLookup(identity, field.name, term)
        setResults(res.results)
      } catch {
        setResults([])
      }
      setLoading(false)
    }, 300)
  }

  return (
    <div ref={wrapperRef} className="relative">
      <Input
        value={showResults ? query : selectedLabel || (value ? String(value) : '')}
        onChange={(e) => {
          setQuery(e.target.value)
          doSearch(e.target.value)
          setShowResults(true)
        }}
        onFocus={() => {
          setQuery('')
          setShowResults(true)
        }}
        placeholder="Search..."
        className={hasError ? 'border-destructive' : ''}
      />
      {value && (
        <button
          type="button"
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          onClick={() => {
            onChange(null)
            setSelectedLabel('')
            setQuery('')
          }}
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
      {showResults && (
        <div className="absolute z-50 top-full mt-1 w-full rounded-md border bg-popover shadow-md max-h-48 overflow-auto">
          {loading && (
            <div className="p-2 text-xs text-muted-foreground">
              Searching...
            </div>
          )}
          {!loading && results.length === 0 && query && (
            <div className="p-2 text-xs text-muted-foreground">
              No results found
            </div>
          )}
          {results.map((r) => (
            <button
              key={r.id}
              type="button"
              className="w-full text-left px-3 py-2 text-sm hover:bg-accent"
              onClick={() => {
                onChange(r.id)
                setSelectedLabel(r.text)
                setShowResults(false)
                setQuery('')
              }}
            >
              {r.text}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function FormSkeleton() {
  return (
    <Card className="max-w-3xl mx-auto">
      <CardHeader>
        <Skeleton className="h-6 w-40" />
      </CardHeader>
      <CardContent className="space-y-6">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-9 w-full" />
          </div>
        ))}
        <div className="flex gap-3 pt-4">
          <Skeleton className="h-9 w-20" />
          <Skeleton className="h-9 w-20" />
        </div>
      </CardContent>
    </Card>
  )
}
