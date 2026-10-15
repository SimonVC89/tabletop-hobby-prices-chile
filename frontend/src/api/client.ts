import type {
  Offer,
  Page,
  PriceHistory,
  ProductDetail,
  ProductQuery,
  ProductSummary,
  Store,
} from './types'

/*
 * Dos implementaciones del mismo contrato:
 * - httpApi: el backend real (cuando exista), activado con VITE_API_URL.
 * - mockApi: snapshot JSON en /mock/ (python -m src.export_frontend_snapshot),
 *   que replica en el cliente el filtrado/orden/paginacion que hara el server.
 * Las pantallas solo conocen `api`, asi que cambiar de una a otra no las toca.
 */
export interface Api {
  getStores(): Promise<Store[]>
  getProducts(query?: ProductQuery): Promise<Page<ProductSummary>>
  getOffers(): Promise<Offer[]>
  getProduct(id: string): Promise<ProductDetail>
  getPriceHistory(id: string): Promise<PriceHistory>
  getSimilarProducts(id: string): Promise<ProductSummary[]>
}

export class NotFoundError extends Error {}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (res.status === 404) throw new NotFoundError(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`)
  return res.json() as Promise<T>
}

function toSearchParams(query: ProductQuery): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  const s = params.toString()
  return s ? `?${s}` : ''
}

function createHttpApi(baseUrl: string): Api {
  return {
    getStores: () => getJson(`${baseUrl}/api/stores`),
    getProducts: (query = {}) => getJson(`${baseUrl}/api/products${toSearchParams(query)}`),
    getOffers: () => getJson(`${baseUrl}/api/offers`),
    getProduct: (id) => getJson(`${baseUrl}/api/products/${id}`),
    getPriceHistory: (id) => getJson(`${baseUrl}/api/products/${id}/price-history`),
    getSimilarProducts: (id) => getJson(`${baseUrl}/api/products/${id}/similar`),
  }
}

// --- mock ---------------------------------------------------------------

interface MockProductFile {
  detail: ProductDetail
  history: PriceHistory
  similar: ProductSummary[]
}

const normalize = (s: string) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

function sortProducts(items: ProductSummary[], sort: ProductQuery['sort']) {
  const byPrice = (p: ProductSummary) => p.bestPrice ?? Number.POSITIVE_INFINITY
  const sorted = [...items]
  switch (sort) {
    case 'discount':
      return sorted.sort((a, b) => (b.discountPct ?? -1) - (a.discountPct ?? -1))
    case 'price-asc':
      return sorted.sort((a, b) => byPrice(a) - byPrice(b))
    case 'price-desc':
      return sorted.sort((a, b) => byPrice(b) - byPrice(a))
    case 'stores':
    case 'relevance':
    default:
      // Sin busqueda de texto, "relevancia" = los mas comparables primero.
      return sorted.sort((a, b) => b.storeCount - a.storeCount || a.name.localeCompare(b.name))
  }
}

function createMockApi(): Api {
  let products: Promise<ProductSummary[]> | undefined
  const files = new Map<string, Promise<MockProductFile>>()

  const allProducts = () => (products ??= getJson<ProductSummary[]>('/mock/products.json'))
  const productFile = (id: string) => {
    if (!files.has(id)) files.set(id, getJson<MockProductFile>(`/mock/products/${id}.json`))
    return files.get(id)!
  }

  return {
    getStores: () => getJson('/mock/stores.json'),
    getOffers: () => getJson('/mock/offers.json'),

    async getProducts(query = {}) {
      const { q, minDiscount, minStores, sort = 'relevance', page = 1, pageSize = 24 } = query
      let items = await allProducts()

      if (q) {
        const terms = normalize(q).split(/\s+/).filter(Boolean)
        items = items.filter((p) => {
          const name = normalize(p.name)
          return terms.every((t) => name.includes(t))
        })
      }
      if (minDiscount) items = items.filter((p) => (p.discountPct ?? 0) >= minDiscount)
      if (minStores) items = items.filter((p) => p.storeCount >= minStores)

      items = sortProducts(items, sort)
      const totalItems = items.length
      const start = (page - 1) * pageSize
      return {
        items: items.slice(start, start + pageSize),
        page,
        pageSize,
        totalItems,
        totalPages: Math.max(1, Math.ceil(totalItems / pageSize)),
      }
    },

    getProduct: async (id) => (await productFile(id)).detail,
    getPriceHistory: async (id) => (await productFile(id)).history,
    getSimilarProducts: async (id) => (await productFile(id)).similar,
  }
}

const apiUrl = import.meta.env.VITE_API_URL as string | undefined

export const api: Api = apiUrl ? createHttpApi(apiUrl) : createMockApi()
export const usingMockData = !apiUrl
