import { ArrowUpRight } from 'lucide-react'
import { useRef } from 'react'
import { Link } from 'react-router'
import type { Offer } from '@/api/types'
import { FullNameCaption } from '@/components/full-name-caption'
import { PriceRangeBar } from '@/components/price-range-bar'
import { ProductImage } from '@/components/product-image'
import { useIsTruncated } from '@/hooks/use-is-truncated'
import { formatCLP, formatPct } from '@/lib/format'
import { cn } from '@/lib/utils'

export function OfferCard({ offer }: { offer: Offer }) {
  const nameRef = useRef<HTMLHeadingElement>(null)
  const truncated = useIsTruncated(nameRef)
  const destacada = offer.tier === 'destacada'
  const productUrl = `/juego/${offer.productId}`

  return (
    <article
      className={cn(
        'group flex flex-col overflow-hidden rounded-lg border bg-card',
        destacada && 'border-highlight/40',
      )}
    >
      <div className="relative">
        {/* Duplica el link del titulo: fuera del orden de tabulacion y del arbol de accesibilidad. */}
        <Link to={productUrl} tabIndex={-1} aria-hidden="true">
          <ProductImage
            src={offer.imageUrl}
            alt=""
            className="aspect-[4/3] rounded-none transition-opacity hover:opacity-90"
          />
        </Link>
        <span className="price absolute top-3 left-3 rounded-md bg-deal px-2 py-1 text-sm font-semibold text-background">
          −{formatPct(offer.discountPct)}
        </span>
        {destacada && (
          <span className="absolute top-3 right-3 rounded-md bg-background/90 px-2 py-1 font-mono text-xs font-semibold tracking-wide text-highlight uppercase">
            Destacada
          </span>
        )}
        {truncated && <FullNameCaption name={offer.productName} className="px-4 text-base" />}
      </div>

      <div className="flex flex-1 flex-col p-4">
        <p className="text-sm text-muted-foreground">{offer.storeName}</p>
        <h2 ref={nameRef} className="mt-1 line-clamp-2 text-base leading-snug font-semibold">
          <Link to={productUrl} className="rounded-sm hover:text-primary hover:underline underline-offset-4">
            {offer.productName}
          </Link>
        </h2>

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
