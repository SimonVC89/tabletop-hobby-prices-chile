import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { PriceDrop } from '@/api/types'
import { HomePage } from './home-page'

// Inicio sin red: los hooks de la API devuelven lo que cada prueba necesita.
const api = vi.hoisted(() => ({ drops: undefined as PriceDrop[] | undefined }))
vi.mock('@/api/hooks', () => ({
  useMeta: () => ({ data: undefined }),
  useOffers: () => ({ data: [], isPending: false }),
  usePriceDrops: () => ({ data: api.drops }),
}))

const drop = (overrides: Partial<PriceDrop>): PriceDrop => ({
  productId: 'p1',
  productName: 'The Number',
  imageUrl: null,
  storeName: 'DeMente Games',
  listingUrl: 'https://dementegames.cl/the-number',
  previousPrice: 14990,
  price: 7490,
  dropPct: 50,
  changedAt: '2026-10-25T22:21:00Z', // 19:21 del 25 en Chile
  ...overrides,
})

const renderHome = () =>
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  )

describe('Inicio: "Bajaron esta semana"', () => {
  beforeEach(() => {
    // Solo la fecha: los temporizadores de React siguen siendo reales.
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-10-27T13:50:00-03:00'))
  })
  afterEach(() => {
    cleanup()
    vi.useRealTimers()
    api.drops = undefined
  })

  it('mientras carga no muestra la seccion', () => {
    renderHome()
    expect(screen.queryByText('Bajaron esta semana')).toBeNull()
  })

  it('sin bajas no desaparece: avisa cuando es la proxima revision', () => {
    api.drops = []
    renderHome()
    expect(screen.getByText('Bajaron esta semana')).toBeTruthy()
    expect(screen.getByText(/Ningún juego bajó de precio esta semana/).textContent).toContain('hoy a las 19:17')
  })

  it('cada baja dice cuando fue', () => {
    api.drops = [drop({}), drop({ productId: 'p2', productName: 'Misty Valley', changedAt: '2026-10-27T08:21:00Z' })]
    renderHome()
    expect(screen.getByText('The Number').closest('a')!.textContent).toContain('hace 2 días')
    expect(screen.getByText('Misty Valley').closest('a')!.textContent).toContain('hoy')
  })
})
