import { ArrowUpRight } from 'lucide-react'
import type { ProductListing } from '@/api/types'
import { formatCLP, formatShortDate } from '@/lib/format'
import { cn } from '@/lib/utils'

// Un listing sin verse por mas de 3 dias pasa a inactivo: la tienda ya no lo publica.
const STALE_MS = 3 * 24 * 60 * 60 * 1000
const isStale = (iso: string) => Date.now() - Date.parse(iso) > STALE_MS

/** Precio actual en cada tienda: primero las con stock, de menor a mayor. */
export function StorePriceList({ listings, className }: { listings: ProductListing[]; className?: string }) {
  const sorted = [...listings].sort((a, b) => Number(b.inStock) - Number(a.inStock) || a.price - b.price)
  const best = sorted.find((l) => l.inStock)

  return (
    <ol className={cn('divide-y rounded-lg border bg-card', className)}>
      {sorted.map((l) => {
        const isBest = l === best
        return (
          <li key={l.storeId} className="flex items-center gap-4 px-4 py-3">
            <div className="min-w-0 flex-1">
              <p className={cn('truncate font-medium', !l.inStock && 'text-muted-foreground')}>{l.storeName}</p>
              <p className={cn('text-xs', isBest ? 'text-deal' : 'text-muted-foreground')}>
                {!l.inStock
                  ? isStale(l.lastSeenAt)
                    ? `Sin stock · visto el ${formatShortDate(l.lastSeenAt)}`
                    : 'Sin stock'
                  : isBest
                    ? 'Mejor precio'
                    : best && (
                        <>
                          <span className="price">+{formatCLP(l.price - best.price)}</span> sobre el mejor
                        </>
                      )}
              </p>
            </div>
            <span className={cn('price text-lg font-semibold', !l.inStock && 'text-muted-foreground line-through decoration-1')}>
              {formatCLP(l.price)}
            </span>
            <a
              href={l.url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Ver en ${l.storeName} (se abre en otra pestaña)`}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-sm font-medium text-primary hover:bg-secondary"
            >
              <span className="hidden sm:inline">Ver</span>
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
          </li>
        )
      })}
    </ol>
  )
}
