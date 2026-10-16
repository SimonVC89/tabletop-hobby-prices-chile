import { useRef } from 'react'
import { Link } from 'react-router'
import type { ProductSummary } from '@/api/types'
import { FullNameCaption } from '@/components/full-name-caption'
import { ProductImage } from '@/components/product-image'
import { useIsTruncated } from '@/hooks/use-is-truncated'
import { formatCLP, formatPct, formatShortDate } from '@/lib/format'
import { OFFER_MIN_DISCOUNT } from '@/lib/price-history'
import { cn } from '@/lib/utils'

/**
 * Tarjeta de juego para el buscador y los "similares". Toda la tarjeta es
 * clickeable (el link del nombre se estira sobre ella), asi que el nombre
 * completo aparece al pasar sobre cualquier parte. Los agotados se muestran
 * apagados con su ultimo precio visto.
 */
export function ProductCard({ product, className }: { product: ProductSummary; className?: string }) {
  const nameRef = useRef<HTMLHeadingElement>(null)
  const truncated = useIsTruncated(nameRef)
  const inStock = product.bestPrice !== null
  const isOffer = product.discountPct !== null && product.discountPct >= OFFER_MIN_DISCOUNT

  return (
    <article
      className={cn(
        'group relative flex flex-col overflow-hidden rounded-lg border bg-card transition-colors hover:border-foreground/30',
        className,
      )}
    >
      <div className="relative">
        <ProductImage
          src={product.imageUrl}
          alt=""
          // Agotado: se apaga la foto, no el fondo (si no, queda un bloque gris).
          className={cn('aspect-[4/3] rounded-none', !inStock && '[&_img]:opacity-50 [&_img]:grayscale')}
        />
        {isOffer && (
          <span className="price absolute top-2 left-2 rounded-md bg-deal px-1.5 py-0.5 text-xs font-semibold text-background">
            −{formatPct(product.discountPct!)}
          </span>
        )}
        {!inStock && (
          <span className="absolute top-2 left-2 rounded-md bg-background/90 px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
            Agotado
          </span>
        )}
        {truncated && <FullNameCaption name={product.name} />}
      </div>

      <div className="flex flex-1 flex-col p-3">
        <h2 ref={nameRef} className="line-clamp-2 text-sm leading-snug font-semibold">
          <Link
            to={`/juego/${product.id}`}
            className="outline-none after:absolute after:inset-0 after:rounded-lg focus-visible:after:ring-2 focus-visible:after:ring-ring group-hover:text-primary"
          >
            {product.name}
          </Link>
        </h2>

        <div className="mt-auto pt-2">
          {inStock ? (
            <>
              <p className="price text-lg font-semibold">{formatCLP(product.bestPrice!)}</p>
              <p className="truncate text-xs text-muted-foreground">
                {product.bestStoreName}
                {product.storeCount > 1 && ` · ${product.storeCount} tiendas`}
              </p>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">
              {product.lastPrice !== null ? (
                <>
                  Último precio <span className="price">{formatCLP(product.lastPrice)}</span>
                  {product.lastSeenAt && <> · {formatShortDate(product.lastSeenAt)}</>}
                </>
              ) : (
                'Sin precios recientes'
              )}
            </p>
          )}
        </div>
      </div>
    </article>
  )
}
