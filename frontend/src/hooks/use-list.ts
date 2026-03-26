import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchList, type ListParams } from '@/lib/api'

export function useList(params: ListParams) {
  return useQuery({
    queryKey: ['list', params],
    queryFn: () => fetchList(params),
    placeholderData: keepPreviousData,
  })
}
