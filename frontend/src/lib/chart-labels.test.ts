import { describe, expect, it } from 'vitest'
import { type LabelBox, placeLabels } from './chart-labels'

const TOP = 10
const BOTTOM = 210
const GAP = 14

/** Un nombre que termina en x=500 (anclado a la derecha), de 100 px de ancho. */
const box = (key: string, y: number, x1 = 500): LabelBox => ({ key, x0: x1 - 100, x1, y })

const spacedAndInside = (ys: number[]) => {
  const sorted = [...ys].sort((a, b) => a - b)
  sorted.forEach((y, i) => {
    expect(y).toBeGreaterThanOrEqual(TOP)
    expect(y).toBeLessThanOrEqual(BOTTOM)
    if (i > 0) expect(y - sorted[i - 1]).toBeGreaterThanOrEqual(GAP)
  })
}

describe('placeLabels', () => {
  it('deja donde estan los nombres que no se tocan', () => {
    const ys = placeLabels([box('a', 50), box('b', 120)], TOP, BOTTOM, GAP)
    expect(ys.get('a')).toBe(50)
    expect(ys.get('b')).toBe(120)
  })

  it('separa dos tiendas que terminan en el mismo precio', () => {
    const ys = placeLabels([box('a', 100), box('b', 100)], TOP, BOTTOM, GAP)
    expect(ys.get('a')).toBe(100)
    expect(ys.get('b')).toBe(114)
  })

  it('separa tres precios parecidos aunque no sean consecutivos al ordenar', () => {
    // Era el error del grafico: solo se comparaba cada nombre con el anterior.
    const ys = placeLabels([box('a', 100), box('b', 105), box('c', 110)], TOP, BOTTOM, GAP)
    spacedAndInside([...ys.values()])
  })

  it('no mueve nombres que estan a la misma altura pero lejos en horizontal', () => {
    const ys = placeLabels([box('a', 100, 150), box('b', 100, 500)], TOP, BOTTOM, GAP)
    expect(ys.get('a')).toBe(100)
    expect(ys.get('b')).toBe(100)
  })

  it('agrupa en cadena: a toca a b y b toca a c', () => {
    // a [0,100], b [90,190], c [180,280]: a y c no se tocan, pero b los une.
    const boxes: LabelBox[] = [
      { key: 'a', x0: 0, x1: 100, y: 100 },
      { key: 'b', x0: 90, x1: 190, y: 100 },
      { key: 'c', x0: 180, x1: 280, y: 100 },
    ]
    spacedAndInside([...placeLabels(boxes, TOP, BOTTOM, GAP).values()])
  })

  it('sube los nombres que se saldrian por abajo', () => {
    const ys = placeLabels([box('a', 205), box('b', 208), box('c', 210)], TOP, BOTTOM, GAP)
    spacedAndInside([...ys.values()])
    expect(Math.max(...ys.values())).toBe(BOTTOM)
  })

  it('baja un nombre que se saldria por arriba', () => {
    expect(placeLabels([box('a', -20)], TOP, BOTTOM, GAP).get('a')).toBe(TOP)
  })

  it('caben las 8 tiendas terminando en el mismo precio', () => {
    const boxes = Array.from({ length: 8 }, (_, i) => box(`s${i}`, 150))
    const ys = placeLabels(boxes, TOP, BOTTOM, GAP)
    expect(ys.size).toBe(8)
    spacedAndInside([...ys.values()])
  })
})
