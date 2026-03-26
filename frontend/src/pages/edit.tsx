import React from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { AppLayout } from '@/components/layout/app-layout'
import { useFormSchema } from '@/hooks/use-form-schema'
import { submitEdit, submitCreate } from '@/lib/api'
import { cn } from '@/lib/utils'
import { FormField } from './create'
import { Button, buttonVariants } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Save, Copy, Loader2, X } from 'lucide-react'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyLinkTo = any

interface EditPageProps {
  identity: string
  pk: string
}

export function EditPage({ identity, pk }: EditPageProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: schema, isLoading, error } = useFormSchema(identity, 'edit', pk)
  const [formData, setFormData] = React.useState<Record<string, any>>({})
  const [errors, setErrors] = React.useState<Record<string, string[]>>({})
  const [initialized, setInitialized] = React.useState(false)

  // Initialize form data when schema loads
  React.useEffect(() => {
    if (schema && !initialized) {
      const initial: Record<string, any> = {}
      for (const field of schema.fields) {
        initial[field.name] = field.value ?? (field.type === 'boolean' ? false : '')
      }
      setFormData(initial)
      setInitialized(true)
    }
  }, [schema, initialized])

  const editMutation = useMutation({
    mutationFn: (data: Record<string, any>) => submitEdit(identity, pk, data),
    onSuccess: (result) => {
      if (result.errors) {
        setErrors(result.errors)
        toast.error('Please fix the validation errors')
      } else {
        toast.success('Saved successfully')
        queryClient.invalidateQueries({ queryKey: ['detail', identity, pk] })
        queryClient.invalidateQueries({ queryKey: ['list'] })
        queryClient.invalidateQueries({
          queryKey: ['form-schema', identity, 'edit', pk],
        })
      }
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to save')
    },
  })

  const saveAsNewMutation = useMutation({
    mutationFn: (data: Record<string, any>) => submitCreate(identity, data),
    onSuccess: (result) => {
      if (result.errors) {
        setErrors(result.errors)
        toast.error('Please fix the validation errors')
      } else {
        toast.success('Saved as new record')
        queryClient.invalidateQueries({ queryKey: ['list'] })
        navigate({ to: `/${identity}/${result.pk}/edit` as AnyLinkTo })
      }
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to save as new')
    },
  })

  const isPending =
    editMutation.isPending ||
    saveAsNewMutation.isPending

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})
    editMutation.mutate(formData)
  }

  const handleSaveAsNew = () => {
    setErrors({})
    saveAsNewMutation.mutate(formData)
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
        { label: `Edit #${pk}` },
      ]
    : [{ label: identity }]

  return (
    <AppLayout title={`Edit ${schema?.name || ''}`} breadcrumbs={breadcrumbs}>
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
        <EditFormSkeleton />
      ) : (
        <form onSubmit={handleSubmit}>
          <Card className="max-w-3xl mx-auto">
            <CardHeader>
              <CardTitle>Edit {schema.name}</CardTitle>
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

              <div className="flex flex-wrap items-center gap-3 pt-4 border-t">
                <Button type="submit" disabled={isPending}>
                  {editMutation.isPending && (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                  <Save className="h-4 w-4" />
                  Save
                </Button>
                {schema.save_as && (
                  <Button
                    type="button"
                    variant="outline"
                    disabled={isPending}
                    onClick={handleSaveAsNew}
                  >
                    {saveAsNewMutation.isPending && (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    )}
                    <Copy className="h-4 w-4" />
                    Save as new
                  </Button>
                )}
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

function EditFormSkeleton() {
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
          <Skeleton className="h-9 w-36" />
          <Skeleton className="h-9 w-20" />
        </div>
      </CardContent>
    </Card>
  )
}
