import { useQuery } from '@tanstack/react-query'
import { fetchFormSchema } from '@/lib/api'

export function useFormSchema(
  identity: string,
  action: 'create' | 'edit',
  pk?: string
) {
  return useQuery({
    queryKey: ['form-schema', identity, action, pk],
    queryFn: () => fetchFormSchema(identity, action, pk),
    enabled: !!identity,
  })
}
