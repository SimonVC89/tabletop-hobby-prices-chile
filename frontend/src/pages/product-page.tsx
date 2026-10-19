import { ArrowLeft, ArrowUpRight } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router'
import { NotFoundError } from '@/api/client'
import { usePriceHistory, useProduct } from '@/api/hooks'
import type { ProductDetail } from '@/api/types'
import { PriceAnalysisPanel } from '@/components/product/price-analysis'
import { PriceHistoryChart } from '@/components/product/price-history-chart'
import { RelatedGames } from '@/components/product/related-games'
import { StorePriceList } from '@/components/product/store-price-list'
import { ProductImage } from '@/components/product-image'
import { Button } from '@/components/ui/button'
import { formatCLP, formatPct } from '@/lib/format'
import {
  analyzePrice,
  buildMarketDays,
  FEATURED_MIN_DISCOUNT,
  MIN_STORES_FOR_MEDIAN,
  OFFER_MIN_DISCOUNT,
} from '@/lib/price-history'
import { NotFoundPage } from '@/pages/not-found-page'

export function ProductPage() {
  const { id = '' } = useParams()
  const product = useProduct(id)
  const history = usePriceHistory(id)

  const days = useMemo(() => (history.data ? buildMarketDays(history.data) : null), [history.data])
  const analysis = useMemo(
    () => (product.data && days ? analyzePrice(product.data, days) : null),
    [product.data, days],
  )

  useEffect(() => {
    if (!product.data) return
    document.title = `${product.data.name} · Tabletop Hobby Prices Chile`
    return () => {
      document.title = 'Tabletop Hobby Prices Chile'
    }
  }, [product.data])

  if (product.isPending) return <ProductSkeleton />
  if (product.isError) {
    if (product.error instanceof NotFoundError) return <NotFoundPage />
    return (
      <div className="rounded-lg border p-6">
        <p className="font-medium">No pudimos cargar este juego.</p>
        <Button variant="outline" className="mt-3" onClick={() => product.refetch()}>
          Reintentar
        </Button>
      </div>
    )
  }

  const detail = product.data

  return (
    <article>
      <BackLink />

      <div className="mt-4 grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-10">
        <ProductImage src={detail.imageUrl} alt={detail.name} className="aspect-[4/3] rounded-lg" />

        <div className="min-w-0">
          <h1 className="text-2xl leading-tight font-bold text-balance sm:text-3xl">{detail.name}</h1>
          <BestPriceCard detail={detail} />
          {hasRealDescription(detail) && (
            <p className="mt-6 leading-relaxed text-pretty text-muted-foreground">{detail.description}</p>
          )}
        </div>
      </div>

      <section aria-labelledby="precios-titulo" className="mt-12">
        <h2 id="precios-titulo" className="text-xl font-bold">
          Precios por tienda
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">Precio de hoy en cada tienda que lo vende.</p>
        <StorePriceList listings={detail.listings} className="mt-4" />
      </section>

      <section aria-labelledby="historial-titulo" className="mt-12">
        <h2 id="historial-titulo" className="text-xl font-bold">
          Historial de precios
        </h2>
        {/* En celular el panel va primero (la conclusion antes del detalle);
            en escritorio, el grafico a la izquierda y el panel al lado. */}
        <div className="mt-4 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
          {history.isError ? (
            <p className="rounded-lg border p-5 text-sm text-muted-foreground lg:col-span-2">
              No pudimos cargar el historial de precios.
            </p>
          ) : analysis && history.data && days ? (
            <>
              <PriceAnalysisPanel analysis={analysis} className="lg:col-start-2 lg:row-start-1" />
              <PriceHistoryChart
                key={id}
                history={history.data}
                days={days}
                listings={detail.listings}
                className="lg:col-start-1 lg:row-start-1"
              />
            </>
          ) : (
            <>
              <div className="h-80 animate-pulse rounded-lg border bg-card lg:col-start-2 lg:row-start-1" />
              <div className="h-96 animate-pulse rounded-lg border bg-card lg:col-start-1 lg:row-start-1" />
            </>
          )}
        </div>
      </section>

      <RelatedGames key={id} productId={id} />
    </article>
  )
}

const simplify = (s: string) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()

/**
 * Algunas tiendas no traen descripcion y repiten el titulo ("Dominations -
 * Español"): eso no aporta nada debajo del nombre, asi que se omite.
 */
function hasRealDescription({ name, description }: ProductDetail) {
  if (!description) return false
  const d = simplify(description)
  return !(d.length < 60 && d.includes(simplify(name)))
}

/** Vuelve a la pagina anterior si se llego navegando; si no, a las ofertas. */
function BackLink() {
  const navigate = useNavigate()
  const location = useLocation()
  const cameFromApp = location.key !== 'default'

  return (
    <Link
      to="/"
      onClick={(e) => {
        if (!cameFromApp) return
        e.preventDefault()
        navigate(-1)
      }}
      className="inline-flex items-center gap-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft className="size-4" aria-hidden="true" />
      Volver
    </Link>
  )
}

function BestPriceCard({ detail }: { detail: ProductDetail }) {
  const best = detail.listings.filter((l) => l.inStock).sort((a, b) => a.price - b.price)[0]
  const stats = detail.stats
  // Mismo calculo que el panel, pero sin esperar a que cargue el historial.
  const discountPct =
    stats && stats.storeCount >= MIN_STORES_FOR_MEDIAN
      ? ((stats.medianPrice - best.price) / stats.medianPrice) * 100
      : null
  const isOffer = discountPct !== null && discountPct >= OFFER_MIN_DISCOUNT
  const isFeatured = discountPct !== null && discountPct >= FEATURED_MIN_DISCOUNT

  if (!best) {
    return (
      <div className="mt-6 rounded-lg border bg-card p-5">
        <p className="font-medium">Sin stock en las tiendas que seguimos</p>
        <p className="mt-1 text-sm text-muted-foreground">Abajo están los últimos precios que vimos en cada una.</p>
      </div>
    )
  }

  return (
    <div className="mt-6 rounded-lg border bg-card p-5">
      <p className="text-sm text-muted-foreground">Mejor precio hoy</p>
      <div className="mt-1 flex flex-wrap items-center gap-3">
        <span className="price text-4xl font-semibold">{formatCLP(best.price)}</span>
        {isOffer && (
          <span className="price rounded-md bg-deal px-2 py-1 text-sm font-semibold text-background">
            −{formatPct(discountPct)}
          </span>
        )}
        {isFeatured && (
          <span className="font-mono text-xs font-semibold tracking-wide text-highlight uppercase">Destacada</span>
        )}
      </div>
      <p className="mt-2 text-sm text-muted-foreground">
        en <span className="text-foreground">{best.storeName}</span>
        {stats && stats.storeCount > 1 && (
          <>
            {' '}
            · mediana <span className="price">{formatCLP(stats.medianPrice)}</span> entre {stats.storeCount} tiendas con
            stock
          </>
        )}
      </p>
      <Button asChild size="lg" className="mt-5 h-11 w-full px-5 text-base sm:w-auto">
        <a href={best.url} target="_blank" rel="noopener noreferrer">
          Ver en {best.storeName}
          <ArrowUpRight className="size-4" aria-hidden="true" />
        </a>
      </Button>
    </div>
  )
}

function ProductSkeleton() {
  return (
    <div aria-label="Cargando juego">
      <div className="h-4 w-16 animate-pulse rounded bg-secondary" />
      <div className="mt-4 grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-10">
        <div className="aspect-[4/3] animate-pulse rounded-lg bg-secondary" />
        <div className="space-y-4">
          <div className="h-8 w-3/4 animate-pulse rounded bg-secondary" />
          <div className="h-44 animate-pulse rounded-lg bg-secondary" />
        </div>
      </div>
    </div>
  )
}
