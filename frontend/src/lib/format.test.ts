import { describe, expect, it } from 'vitest'
import { formatCLP, formatCount, formatDay, formatDaysAgo, formatPct, formatUpdated } from './format'

// Las pruebas corren en hora de Chile (vite.config.ts). En octubre es UTC-3.
const NOW = new Date('2026-10-27T13:50:00-03:00')

describe('formatos de numeros', () => {
  it('precios en pesos chilenos, con punto de miles y sin decimales', () => {
    expect(formatCLP(31990)).toBe('$31.990')
    expect(formatCLP(7490)).toBe('$7.490')
  })

  it('porcentajes redondeados, sin decimales', () => {
    expect(formatPct(32.4)).toBe('32%')
    expect(formatPct(49.6)).toBe('50%')
  })

  it('cantidades con punto de miles', () => {
    expect(formatCount(6008)).toBe('6.008')
  })

  it('un dia del historial no se corre por la zona horaria', () => {
    // "2026-10-13" es medianoche UTC: en Chile seria el 12 si no se formateara en UTC.
    expect(formatDay('2026-10-13')).toBe('13 oct')
  })
})

describe('formatDaysAgo', () => {
  it('cuenta dias de calendario en Chile, no bloques de 24 horas', () => {
    expect(formatDaysAgo('2026-10-27T08:21:00Z', NOW)).toBe('hoy') // 05:21 en Chile
    expect(formatDaysAgo('2026-10-26T22:20:00Z', NOW)).toBe('ayer') // 19:20 del 26
    // 23:30 del 26 en Chile, aunque en UTC ya sea el 27.
    expect(formatDaysAgo('2026-10-27T02:30:00Z', NOW)).toBe('ayer')
    expect(formatDaysAgo('2026-10-23T10:00:00Z', NOW)).toBe('hace 4 días')
  })
})

describe('formatUpdated', () => {
  it('hoy, ayer o la fecha completa', () => {
    expect(formatUpdated('2026-10-27T08:21:00Z', NOW)).toBe('hoy a las 05:21')
    expect(formatUpdated('2026-10-26T22:20:00Z', NOW)).toBe('ayer a las 19:20')
    expect(formatUpdated('2026-10-20T22:20:00Z', NOW)).toBe('el 20 de octubre, 19:20')
  })
})
