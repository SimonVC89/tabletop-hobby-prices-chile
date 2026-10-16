import type { PriceHistory, ProductDetail } from '@/api/types'

/** Mismas reglas que las ofertas y el bot de Telegram. */
export const MIN_STORES_FOR_MEDIAN = 3
export const OFFER_MIN_DISCOUNT = 20
export const FEATURED_MIN_DISCOUNT = 50

/** Un dia del mercado, a partir de las series por tienda. */
export interface MarketDay {
  date: string
  /** Mejor precio entre tiendas con stock; null si ninguna tenia stock. */
  best: number | null
  bestStoreName: string | null
  median: number | null
  /** Tiendas con stock ese dia. */
  storeCount: number
  /**
   * Hubo scraping real con stock ese dia (no solo precios arrastrados de
   * dias anteriores). Es lo que cuenta como "dias de precios".
   */
  observed: boolean
  /** Precio de cada tienda (por storeId), con o sin stock. */
  stores: Record<string, { price: number; inStock: boolean }>
}

// Si el scraping de una tienda falla un dia, su ultimo precio sigue valiendo
// hasta 3 dias: el mismo plazo con que un listing pasa a inactivo.
const CARRY_DAYS = 3
const DAY_MS = 24 * 60 * 60 * 1000

const addDays = (iso: string, n: number) => new Date(Date.parse(iso) + n * DAY_MS).toISOString().slice(0, 10)
const daysBetween = (from: string, to: string) => Math.round((Date.parse(to) - Date.parse(from)) / DAY_MS)

export function median(values: number[]): number | null {
  if (values.length === 0) return null
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[mid] : Math.round((sorted[mid - 1] + sorted[mid]) / 2)
}

/** Un registro por dia, del primer al ultimo dia con datos, sin huecos. */
export function buildMarketDays(history: PriceHistory): MarketDay[] {
  const dates = history.series.flatMap((s) => s.points.map((p) => p.date)).sort()
  if (dates.length === 0) return []

  const series = history.series.map((s) => ({
    storeId: s.storeId,
    storeName: s.storeName,
    byDate: new Map(s.points.map((p) => [p.date, p])),
  }))
  const lastSeen = new Map<string, { date: string; price: number; inStock: boolean }>()
  const days: MarketDay[] = []

  for (let date = dates[0]; date <= dates[dates.length - 1]; date = addDays(date, 1)) {
    const stores: MarketDay['stores'] = {}
    const inStock: { price: number; storeName: string }[] = []
    let observed = false

    for (const s of series) {
      const point = s.byDate.get(date)
      if (point) {
        lastSeen.set(s.storeId, { date, price: point.price, inStock: point.inStock })
        if (point.inStock) observed = true
      }
      const seen = lastSeen.get(s.storeId)
      if (!seen || daysBetween(seen.date, date) > CARRY_DAYS) continue

      stores[s.storeId] = { price: seen.price, inStock: seen.inStock }
      if (seen.inStock) inStock.push({ price: seen.price, storeName: s.storeName })
    }

    const cheapest = inStock.reduce<(typeof inStock)[number] | null>(
      (min, x) => (min === null || x.price < min.price ? x : min),
      null,
    )
    days.push({
      date,
      best: cheapest?.price ?? null,
      bestStoreName: cheapest?.storeName ?? null,
      median: median(inStock.map((x) => x.price)),
      storeCount: inStock.length,
      observed,
      stores,
    })
  }
  return days
}

export type Verdict = 'excepcional' | 'buen-precio' | 'normal' | 'pocas-tiendas' | 'sin-stock'

export interface PriceAnalysis {
  verdict: Verdict
  /** Mejor precio actual (tienda con stock). */
  best: { price: number; storeName: string; url: string } | null
  median: number | null
  storeCount: number
  /** Solo con 3+ tiendas: con menos, la mediana no es confiable. */
  discountPct: number | null
  /** Cuanto se ahorra frente a la mediana (si es positivo). */
  savings: number | null
  /** Dias con scraping real y al menos un precio con stock. */
  historyDays: number
  /** Precio mas bajo registrado en el historial. */
  lowest: { price: number; date: string; storeName: string } | null
  /** El dia mas barato antes de hoy, si fue mas barato que ahora. */
  cheaperBefore: { price: number; date: string; storeName: string } | null
}

export function analyzePrice(detail: ProductDetail, days: MarketDay[]): PriceAnalysis {
  const bestListing = detail.listings.filter((l) => l.inStock).sort((a, b) => a.price - b.price)[0]
  const best = bestListing
    ? { price: bestListing.price, storeName: bestListing.storeName, url: bestListing.url }
    : null
  const storeCount = detail.stats?.storeCount ?? 0
  const medianPrice = detail.stats?.medianPrice ?? null

  const discountPct =
    best && medianPrice && storeCount >= MIN_STORES_FOR_MEDIAN
      ? ((medianPrice - best.price) / medianPrice) * 100
      : null
  const savings = best && medianPrice && medianPrice > best.price ? medianPrice - best.price : null

  const withStock = days.filter((d) => d.best !== null)
  let lowest: PriceAnalysis['lowest'] = null
  let cheaperBefore: PriceAnalysis['cheaperBefore'] = null
  const lastDate = days.at(-1)?.date
  for (const d of withStock) {
    const entry = { price: d.best!, date: d.date, storeName: d.bestStoreName! }
    if (!lowest || entry.price < lowest.price) lowest = entry
    if (best && d.date !== lastDate && entry.price < best.price && (!cheaperBefore || entry.price < cheaperBefore.price)) {
      cheaperBefore = entry
    }
  }

  let verdict: Verdict
  if (!best) verdict = 'sin-stock'
  else if (discountPct === null) verdict = 'pocas-tiendas'
  else if (discountPct >= FEATURED_MIN_DISCOUNT) verdict = 'excepcional'
  else if (discountPct >= OFFER_MIN_DISCOUNT) verdict = 'buen-precio'
  else verdict = 'normal'

  return {
    verdict,
    best,
    median: medianPrice,
    storeCount,
    discountPct,
    savings,
    historyDays: days.filter((d) => d.observed).length,
    lowest,
    cheaperBefore,
  }
}
