import { useQuery } from '@tanstack/react-query'
import { fetchSite } from '@/lib/api'

export function useSite() {
  return useQuery({
    queryKey: ['site'],
    queryFn: fetchSite,
    staleTime: 5 * 60 * 1000,
  })
}
