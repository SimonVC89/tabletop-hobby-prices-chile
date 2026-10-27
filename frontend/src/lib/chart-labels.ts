/**
 * Posicion vertical de los nombres de tienda al final de sus lineas en el
 * grafico de historial, sin que se pisen ni queden fuera del area del grafico.
 *
 * Cada nombre ocupa un tramo horizontal [x0, x1] (estimado por el largo del
 * texto) y quiere quedar a la altura `y` del final de su linea. Los nombres
 * cuyos tramos se cruzan forman un grupo; dentro de cada grupo se ordenan por
 * altura y se separan al menos `gap` px, empujando hacia abajo y, si el ultimo
 * se sale por abajo, de vuelta hacia arriba. Todo en pixeles, no en precios:
 * lo que importa es si los textos se tocan en pantalla.
 */

export interface LabelBox {
  key: string
  x0: number
  x1: number
  /** Altura deseada (centro del texto), en px desde arriba. */
  y: number
}

/** Devuelve key -> altura final (centro del texto), en px. */
export function placeLabels(boxes: LabelBox[], top: number, bottom: number, gap = 14): Map<string, number> {
  const result = new Map<string, number>()
  for (const group of overlappingGroups(boxes)) {
    const sorted = [...group].sort((a, b) => a.y - b.y || a.key.localeCompare(b.key))
    const ys = sorted.map((b) => clamp(b.y, top, bottom))
    // Hacia abajo: cada uno al menos `gap` bajo el anterior.
    for (let i = 1; i < ys.length; i++) ys[i] = Math.max(ys[i], ys[i - 1] + gap)
    // Si el ultimo se salio por abajo, se sube y arrastra a los de arriba.
    if (ys.length > 0 && ys[ys.length - 1] > bottom) {
      ys[ys.length - 1] = bottom
      for (let i = ys.length - 2; i >= 0; i--) ys[i] = Math.min(ys[i], ys[i + 1] - gap)
    }
    // Si ni asi caben (demasiados para la altura), el de arriba manda: se
    // prefiere que se toquen a que queden fuera del grafico.
    if (ys.length > 0 && ys[0] < top) {
      ys[0] = top
      for (let i = 1; i < ys.length; i++) ys[i] = Math.max(ys[i], ys[i - 1] + gap)
    }
    sorted.forEach((b, i) => result.set(b.key, ys[i]))
  }
  return result
}

/** Agrupa los nombres cuyos tramos horizontales se cruzan (directa o en cadena). */
function overlappingGroups(boxes: LabelBox[]): LabelBox[][] {
  const groups: LabelBox[][] = []
  let current: LabelBox[] = []
  let currentEnd = Number.NEGATIVE_INFINITY
  for (const b of [...boxes].sort((a, c) => a.x0 - c.x0)) {
    if (current.length > 0 && b.x0 > currentEnd) {
      groups.push(current)
      current = []
      currentEnd = Number.NEGATIVE_INFINITY
    }
    current.push(b)
    currentEnd = Math.max(currentEnd, b.x1)
  }
  if (current.length > 0) groups.push(current)
  return groups
}

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi)
