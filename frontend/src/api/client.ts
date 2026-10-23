import type {
  Meta,
  Offer,
  Page,
  PriceDrop,
  PriceHistory,
  ProductDetail,
  ProductQuery,
  ProductSummary,
  Store,
} from './types'

/*
 * Dos implementaciones del mismo contrato:
 * - httpApi: el backend real (cuando exista), activado con VITE_API_URL.
 * - mockApi: respuestas de la API grabadas en JSON (npm run mock:record o la muestra
 *   versionada de mock:sample), que replica en el cliente el filtrado/orden/paginacion
 *   que hace el server.
 * Las pantallas solo conocen `api`, asi que cambiar de una a otra no las toca.
 */
export interface Api {
  getMeta(): Promise<Meta>
  getStores(): Promise<Store[]>
  getProducts(query?: ProductQuery): Promise<Page<ProductSummary>>
  getOffers(): Promise<Offer[]>
  /** Bajas de precio de los ultimos 7 dias; ver PriceDrop para la regla. */
  getPriceDrops(): Promise<PriceDrop[]>
  getProduct(id: string): Promise<ProductDetail>
  getPriceHistory(id: string): Promise<PriceHistory>
  /**
   * Juegos relacionados (hasta 6), solo los que hoy tienen stock. Regla del
   * backend (SimilarProducts.java): misma saga (primera palabra del nombre) con
   * similitud de embedding >= 0.45, o similitud >= 0.78; la saga va primero.
   * Los embeddings son de titulos: captan sagas, no mecanicas de juego.
   */
  getSimilarProducts(id: string): Promise<ProductSummary[]>
}

export class NotFoundError extends Error {}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (res.status === 404) throw new NotFoundError(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`)
  // En el mock, Vite responde index.html (200) a un archivo que no existe.
  if (!res.headers.get('content-type')?.includes('json')) throw new NotFoundError(url)
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
    getMeta: () => getJson(`${baseUrl}/api/meta`),
    getStores: () => getJson(`${baseUrl}/api/stores`),
    getProducts: (query = {}) => getJson(`${baseUrl}/api/products${toSearchParams(query)}`),
    getOffers: () => getJson(`${baseUrl}/api/offers`),
    getPriceDrops: () => getJson(`${baseUrl}/api/price-drops`),
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

/**
 * Que tan bien calza un nombre con la busqueda: nombre exacto, luego que
 * empiece igual, luego palabras que empiecen con cada termino. A igualdad,
 * nombres mas cortos primero (el juego base antes que sus expansiones).
 */
function relevance(name: string, query: string, terms: string[]) {
  const n = normalize(name)
  const words = n.split(/[^a-z0-9]+/)
  let score = 0
  if (n === query) score += 100
  else if (n.startsWith(query)) score += 50
  for (const t of terms) if (words.some((w) => w.startsWith(t))) score += 10
  return score - n.length / 100
}

function sortProducts(items: ProductSummary[], sort: ProductQuery['sort'], q: string) {
  const byPrice = (p: ProductSummary) => p.bestPrice ?? Number.POSITIVE_INFINITY
  const query = normalize(q).trim()
  const terms = query.split(/\s+/).filter(Boolean)
  const scores = new Map(query ? items.map((p) => [p.id, relevance(p.name, query, terms)]) : [])

  const compare: (a: ProductSummary, b: ProductSummary) => number = (() => {
    switch (sort) {
      case 'discount':
        return (a, b) => (b.discountPct ?? -1) - (a.discountPct ?? -1)
      case 'price-asc':
        return (a, b) => byPrice(a) - byPrice(b)
      case 'price-desc':
        return (a, b) => byPrice(b) - byPrice(a)
      case 'stores':
        return (a, b) => b.storeCount - a.storeCount
      case 'relevance':
      default:
        // Sin texto, "relevancia" = los mas comparables primero.
        return (a, b) => (scores.get(b.id) ?? 0) - (scores.get(a.id) ?? 0) || b.storeCount - a.storeCount
    }
  })()

  // Desempate explicito, igual al del backend (ProductSearch.java): nombre normalizado
  // caracter a caracter y luego id. localeCompare ordena distinto que Java.
  const names = new Map(items.map((p) => [p.id, normalize(p.name)]))
  const byText = (x: string, y: string) => (x < y ? -1 : x > y ? 1 : 0)
  const outOfStock = (p: ProductSummary) => (p.bestPrice === null ? 1 : 0)
  return [...items].sort(
    (a, b) =>
      outOfStock(a) - outOfStock(b) || compare(a, b) || byText(names.get(a.id)!, names.get(b.id)!) || byText(a.id, b.id),
  )
}

function createMockApi(): Api {
  let products: Promise<ProductSummary[]> | undefined
  const files = new Map<string, Promise<MockProductFile>>()

  // La copia completa (/mock/, npm run mock:record) no se versiona; si no esta, como
  // recien clonado el repo, se usa la muestra versionada (/mock-sample/).
  let base: Promise<string> | undefined
  const mockBase = () =>
    (base ??= getJson('/mock/meta.json').then(
      () => '/mock',
      () => '/mock-sample',
    ))
  const mock = async <T,>(file: string) => getJson<T>(`${await mockBase()}/${file}`)

  const allProducts = () => (products ??= mock<ProductSummary[]>('products.json'))
  const productFile = (id: string) => {
    if (!files.has(id)) files.set(id, mock<MockProductFile>(`products/${id}.json`))
    return files.get(id)!
  }

  return {
    getMeta: () => mock('meta.json'),
    getStores: () => mock('stores.json'),
    getOffers: () => mock('offers.json'),
    getPriceDrops: () => mock('price-drops.json'),

    async getProducts(query = {}) {
      const {
        q = '',
        minDiscount,
        minStores,
        includeOutOfStock = true,
        sort = 'relevance',
        page = 1,
        pageSize = 24,
      } = query
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
      if (!includeOutOfStock) items = items.filter((p) => p.bestPrice !== null)

      items = sortProducts(items, sort, q)
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
