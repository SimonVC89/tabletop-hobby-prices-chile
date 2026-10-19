/*
 * Contrato de la API REST. El frontend se construye contra estos tipos y
 * el backend (Spring Boot) debe devolver exactamente esta forma.
 *
 * Convenciones:
 * - JSON en camelCase (default de Jackson en Spring Boot).
 * - Precios en pesos chilenos como enteros (CLP no usa decimales).
 * - Fechas en ISO 8601: "2026-10-15" para dias, con hora para timestamps.
 * - discountPct es positivo cuando el precio esta BAJO la mediana.
 */

export interface Store {
  id: string
  name: string
  baseUrl: string
  /** Listings activos (vistos en el scraping de los ultimos dias). */
  activeListings: number
  status: StoreStatus
}

/**
 * - daily: se scrapea sola todos los dias (cron).
 * - manual: bloquea las IPs de datacenter; solo se actualiza a mano.
 * - excluded: bloquea el acceso automatizado; se respeto y se dejo de
 *   scrapear (se conserva su historial).
 */
export type StoreStatus = 'daily' | 'manual' | 'excluded'

/** Tarjeta de producto en catalogo, busqueda y "relacionados". */
export interface ProductSummary {
  id: string
  name: string
  imageUrl: string | null
  /** Tiendas con un listing activo y en stock. */
  storeCount: number
  bestPrice: number | null
  bestStoreName: string | null
  /** Mediana entre tiendas; null si no hay precios en stock. */
  medianPrice: number | null
  /**
   * Descuento del mejor precio vs. la mediana. Solo se calcula con 3+
   * tiendas (con menos, la mediana no es confiable); si no, null.
   */
  discountPct: number | null
  /** Solo si esta agotado en todas las tiendas: ultimo precio visto. */
  lastPrice: number | null
  /** Solo si esta agotado: cuando se vio ese ultimo precio (ISO 8601). */
  lastSeenAt: string | null
}

export type OfferTier = 'destacada' | 'oferta'

/** Una tienda vendiendo bajo la mediana (misma regla que el bot de Telegram). */
export interface Offer {
  productId: string
  productName: string
  imageUrl: string | null
  storeName: string
  /** Link directo al producto en la tienda. */
  listingUrl: string
  price: number
  medianPrice: number
  /** Rango de precios en stock entre todas las tiendas que lo venden. */
  minPrice: number
  maxPrice: number
  discountPct: number
  storeCount: number
  /** 'destacada' >= 50% bajo la mediana, 'oferta' >= 20%. */
  tier: OfferTier
}

export interface Meta {
  /** Momento del ultimo scraping con datos (ISO 8601). */
  lastUpdated: string
}

export interface ProductListing {
  storeId: string
  storeName: string
  url: string
  price: number
  inStock: boolean
  lastSeenAt: string
}

export interface PriceStats {
  medianPrice: number
  minPrice: number
  maxPrice: number
  storeCount: number
}

export interface ProductDetail {
  id: string
  name: string
  imageUrl: string | null
  /** Extracto corto (hasta ~300 caracteres) de la descripcion de una tienda. */
  description: string | null
  /** Tienda de la que salio la descripcion, para citarla; null si no se conoce. */
  descriptionSource: string | null
  /**
   * Uno por tienda (si una tienda publica el juego en dos paginas, la mas
   * barata con stock). Ordenados de menor a mayor precio.
   */
  listings: ProductListing[]
  stats: PriceStats | null
}

/** Ultimo precio visto de una tienda en un dia. */
export interface PricePoint {
  date: string
  price: number
  /**
   * Si tenia stock ese dia. El "mejor precio del dia" y la mediana del
   * grafico solo consideran puntos con stock.
   */
  inStock: boolean
}

/** Una serie por tienda: el grafico permite mostrar/ocultar cada una. */
export interface PriceHistorySeries {
  storeId: string
  storeName: string
  points: PricePoint[]
}

export interface PriceHistory {
  productId: string
  series: PriceHistorySeries[]
}

export interface Page<T> {
  items: T[]
  page: number
  pageSize: number
  totalItems: number
  totalPages: number
}

export type ProductSort = 'relevance' | 'discount' | 'price-asc' | 'price-desc' | 'stores'

/**
 * Busqueda del catalogo. Los juegos con stock van siempre antes que los
 * agotados; dentro de cada grupo se aplica `sort`.
 */
export interface ProductQuery {
  /** Texto libre; ignora tildes y mayusculas. */
  q?: string
  minDiscount?: number
  minStores?: number
  /** Incluir juegos agotados en todas las tiendas (por defecto true). */
  includeOutOfStock?: boolean
  sort?: ProductSort
  page?: number
  pageSize?: number
}
