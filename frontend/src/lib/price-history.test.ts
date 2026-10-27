import { describe, expect, it } from 'vitest'
import type { PriceHistory, ProductDetail } from '@/api/types'
import { analyzePrice, buildMarketDays, median } from './price-history'

describe('median', () => {
  it('impar, par y vacia', () => {
    expect(median([3, 1, 2])).toBe(2)
    expect(median([10, 20, 40, 30])).toBe(25)
    expect(median([])).toBeNull()
  })
})

const history = (series: PriceHistory['series']): PriceHistory => ({ productId: 'p', series })

describe('buildMarketDays', () => {
  it('rellena los dias sin datos con el ultimo precio, hasta 3 dias', () => {
    const days = buildMarketDays(
      history([
        { storeId: 'a', storeName: 'A', points: [{ date: '2026-10-01', price: 100, inStock: true }] },
        { storeId: 'b', storeName: 'B', points: [{ date: '2026-10-06', price: 200, inStock: true }] },
      ]),
    )
    expect(days.map((d) => d.date)).toEqual([
      '2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04', '2026-10-05', '2026-10-06',
    ])
    expect(days[3].stores.a).toEqual({ price: 100, inStock: true }) // 3 dias despues: sigue
    expect(days[4].stores.a).toBeUndefined() // 4 dias despues: ya no
    expect(days.map((d) => d.observed)).toEqual([true, false, false, false, false, true])
  })

  it('el mejor precio y la mediana solo cuentan tiendas con stock', () => {
    const [day] = buildMarketDays(
      history([
        { storeId: 'a', storeName: 'A', points: [{ date: '2026-10-01', price: 50, inStock: false }] },
        { storeId: 'b', storeName: 'B', points: [{ date: '2026-10-01', price: 100, inStock: true }] },
        { storeId: 'c', storeName: 'C', points: [{ date: '2026-10-01', price: 300, inStock: true }] },
      ]),
    )
    expect(day.best).toBe(100)
    expect(day.bestStoreName).toBe('B')
    expect(day.median).toBe(200)
    expect(day.storeCount).toBe(2)
  })
})

const detail = (prices: number[], medianPrice: number): ProductDetail => ({
  id: 'p',
  name: 'Juego',
  imageUrl: null,
  description: null,
  descriptionSource: null,
  listings: prices.map((price, i) => ({
    storeId: `s${i}`,
    storeName: `Tienda ${i}`,
    url: `https://tienda${i}.cl`,
    price,
    inStock: true,
    lastSeenAt: '2026-10-27T08:00:00Z',
  })),
  stats: { medianPrice, minPrice: Math.min(...prices), maxPrice: Math.max(...prices), storeCount: prices.length },
})

describe('analyzePrice', () => {
  it('50% o mas bajo la mediana de 3 tiendas es excepcional', () => {
    const a = analyzePrice(detail([7490, 14990, 14990], 14990), [])
    expect(a.verdict).toBe('excepcional')
    expect(a.savings).toBe(7500)
    expect(Math.round(a.discountPct!)).toBe(50)
  })

  it('entre 20% y 50% es buen precio', () => {
    expect(analyzePrice(detail([7000, 10000, 10000], 10000), []).verdict).toBe('buen-precio')
  })

  it('con menos de 3 tiendas la mediana no es confiable', () => {
    const a = analyzePrice(detail([5000, 10000], 7500), [])
    expect(a.verdict).toBe('pocas-tiendas')
    expect(a.discountPct).toBeNull()
  })
})
