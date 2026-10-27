import { describe, expect, it } from 'vitest'
import { nextScraperRun } from './scraper-schedule'

const chile = (time: string) => new Date(`2026-10-27T${time}:00-03:00`)

describe('nextScraperRun', () => {
  it('antes de las 5:17 toca la de la mañana', () => {
    expect(nextScraperRun(chile('03:00'))).toBe('hoy a las 5:17')
  })

  it('durante el dia toca la de la tarde', () => {
    expect(nextScraperRun(chile('13:50'))).toBe('hoy a las 19:17')
  })

  it('despues de las 19:17 toca la de mañana', () => {
    expect(nextScraperRun(chile('19:18'))).toBe('mañana a las 5:17')
  })

  it('usa la hora de Chile aunque el instante se escriba en otra zona', () => {
    // 22:50 UTC = 19:50 en Chile: ya paso la de la tarde.
    expect(nextScraperRun(new Date('2026-10-27T22:50:00Z'))).toBe('mañana a las 5:17')
  })
})
