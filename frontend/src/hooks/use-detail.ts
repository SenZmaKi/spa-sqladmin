import { useQuery } from '@tanstack/react-query'
import { fetchDetail } from '@/lib/api'

export function useDetail(identity: string, pk: string) {
  return useQuery({
    queryKey: ['detail', identity, pk],
    queryFn: () => fetchDetail(identity, pk),
    enabled: !!identity && !!pk,
  })
}
