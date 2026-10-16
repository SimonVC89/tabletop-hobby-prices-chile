import { ArrowUpRight } from 'lucide-react'
import type { Offer } from '@/api/types'
import { PriceRangeBar } from '@/components/price-range-bar'
import { ProductImage } from '@/components/product-image'
import { formatCLP, formatPct } from '@/lib/format'
import { cn } from '@/lib/utils'

export function OfferCard({ offer }: { offer: Offer }) {
  const destacada = offer.tier === 'destacada'

  return (
    <article
      className={cn(
        'flex flex-col overflow-hidden rounded-lg border bg-card',
        destacada && 'border-highlight/40',
      )}
    >
      <div className="relative">
        <ProductImage src={offer.imageUrl} alt={offer.productName} className="aspect-[4/3] rounded-none" />
        <span className="price absolute top-3 left-3 rounded-md bg-deal px-2 py-1 text-sm font-semibold text-background">
          −{formatPct(offer.discountPct)}
        </span>
        {destacada && (
          <span className="absolute top-3 right-3 rounded-md bg-background/90 px-2 py-1 font-mono text-xs font-semibold tracking-wide text-highlight uppercase">
            Destacada
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col p-4">
        <p className="text-sm text-muted-foreground">{offer.storeName}</p>
        <h2 className="mt-1 line-clamp-2 text-base leading-snug font-semibold">{offer.productName}</h2>

        <div className="mt-3 flex items-baseline gap-2">
          <span className="price text-2xl font-semibold">{formatCLP(offer.price)}</span>
          <span className="text-sm text-muted-foreground">
            mediana <span className="price">{formatCLP(offer.medianPrice)}</span>
          </span>
        </div>

        <PriceRangeBar
          className="mt-4"
          price={offer.price}
          median={offer.medianPrice}
          min={offer.minPrice}
          max={offer.maxPrice}
          storeCount={offer.storeCount}
        />

        <div className="mt-auto flex items-center justify-between gap-3 pt-4">
          <span className="text-xs text-muted-foreground">Comparado en {offer.storeCount} tiendas</span>
          <a
            href={offer.listingUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
          >
            Ver en tienda <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
        </div>
      </div>
    </article>
  )
}
