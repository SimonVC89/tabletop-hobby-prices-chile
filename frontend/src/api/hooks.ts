import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api } from './client'
import type { ProductQuery } from './types'

// Los datos cambian una vez al dia (cron), asi que un staleTime largo
// evita refetches innecesarios al navegar entre paginas.
const DAY_DATA = { staleTime: 30 * 60 * 1000 }

export const useMeta = () =>
  useQuery({ queryKey: ['meta'], queryFn: api.getMeta, ...DAY_DATA })

export const useStores = () =>
  useQuery({ queryKey: ['stores'], queryFn: api.getStores, ...DAY_DATA })

export const useOffers = () =>
  useQuery({ queryKey: ['offers'], queryFn: api.getOffers, ...DAY_DATA })

export const useProducts = (query: ProductQuery) =>
  useQuery({
    queryKey: ['products', query],
    queryFn: () => api.getProducts(query),
    placeholderData: keepPreviousData, // la grilla no parpadea al paginar/filtrar
    ...DAY_DATA,
  })

export const useProduct = (id: string) =>
  useQuery({ queryKey: ['product', id], queryFn: () => api.getProduct(id), ...DAY_DATA })

export const usePriceHistory = (id: string) =>
  useQuery({
    queryKey: ['product', id, 'history'],
    queryFn: () => api.getPriceHistory(id),
    ...DAY_DATA,
  })

export const useSimilarProducts = (id: string) =>
  useQuery({
    queryKey: ['product', id, 'similar'],
    queryFn: () => api.getSimilarProducts(id),
    ...DAY_DATA,
  })
