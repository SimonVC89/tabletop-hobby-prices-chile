import { formatCLP } from '@/lib/format'
import { cn } from '@/lib/utils'

interface PriceRangeBarProps {
  price: number
  median: number
  min: number
  max: number
  storeCount: number
  className?: string
}

const position = (value: number, min: number, max: number) =>
  max === min ? 50 : ((value - min) / (max - min)) * 100

/**
 * Donde cae un precio dentro del rango del mercado (min..max entre tiendas
 * con stock), con la mediana como referencia. Marcas segun la guia de
 * visualizacion: pista fina neutra, mediana como tick neutro, el precio
 * como punto >= 8px con anillo del color de la superficie; los valores
 * van como texto en tokens de texto, nunca en el color de la marca.
 */
export function PriceRangeBar({ price, median, min, max, storeCount, className }: PriceRangeBarProps) {
  const pricePos = position(price, min, max)
  const medianPos = position(median, min, max)
  const summary =
    `Precio ${formatCLP(price)} frente a una mediana de ${formatCLP(median)}; ` +
    `rango entre ${formatCLP(min)} y ${formatCLP(max)} en ${storeCount} tiendas.`

  return (
    <div className={cn('group relative', className)}>
      <div
        role="img"
        aria-label={summary}
        tabIndex={0}
        className="rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <div className="relative mx-1.5 h-4">
          <div className="absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-border" />
          <div
            className="absolute top-1/2 h-3.5 w-0.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-muted-foreground"
            style={{ left: `${medianPos}%` }}
          />
          <div
            className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-deal ring-2 ring-card"
            style={{ left: `${pricePos}%` }}
          />
        </div>
        <div className="price mt-1 flex justify-between text-xs text-muted-foreground">
          <span>{formatCLP(min)}</span>
          <span>{formatCLP(max)}</span>
        </div>
      </div>

      <div
        role="presentation"
        className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 w-max max-w-64 -translate-x-1/2 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
      >
        <p className="flex items-center gap-2">
          <span className="size-2 rounded-full bg-deal" aria-hidden="true" />
          Esta tienda <span className="price ml-auto font-medium">{formatCLP(price)}</span>
        </p>
        <p className="mt-1 flex items-center gap-2">
          <span className="h-2.5 w-0.5 rounded-full bg-muted-foreground" aria-hidden="true" />
          Mediana <span className="price ml-auto font-medium">{formatCLP(median)}</span>
        </p>
        <p className="mt-1 text-muted-foreground">Rango en {storeCount} tiendas con stock</p>
      </div>
    </div>
  )
}
