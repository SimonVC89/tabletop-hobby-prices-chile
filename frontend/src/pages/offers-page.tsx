import { useMemo } from 'react'
import { useSearchParams } from 'react-router'
import { useOffers, useStores } from '@/api/hooks'
import type { Offer } from '@/api/types'
import { OfferCard } from '@/components/offer-card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type TierFilter = 'todas' | 'destacadas'
type Sort = 'descuento' | 'precio'

const SORTERS: Record<Sort, (a: Offer, b: Offer) => number> = {
  descuento: (a, b) => b.discountPct - a.discountPct,
  precio: (a, b) => a.price - b.price,
}

export function OffersPage() {
  const { data: offers, isPending, isError, refetch } = useOffers()
  const [params, setParams] = useSearchParams()

  // Los filtros viven en la URL: un link filtrado se puede compartir.
  const tier: TierFilter = params.get('tipo') === 'destacadas' ? 'destacadas' : 'todas'
  const store = params.get('tienda') ?? ''
  const sort: Sort = params.get('orden') === 'precio' ? 'precio' : 'descuento'

  const setParam = (key: string, value: string, defaultValue: string) => {
    const next = new URLSearchParams(params)
    if (value === defaultValue) next.delete(key)
    else next.set(key, value)
    setParams(next, { replace: true })
  }

  // Todas las tiendas rastreadas, no solo las que tienen ofertas hoy: asi se
  // ve que una tienda se revisa aunque hoy no tenga ninguna (queda en 0).
  const { data: allStores } = useStores()
  const storeOptions = useMemo(() => {
    const counts = new Map<string, number>()
    for (const o of offers ?? []) counts.set(o.storeName, (counts.get(o.storeName) ?? 0) + 1)
    return (allStores ?? [])
      .filter((s) => s.status !== 'excluded')
      .map((s) => ({ name: s.name, count: counts.get(s.name) ?? 0 }))
      .sort((a, b) => a.name.localeCompare(b.name, 'es'))
  }, [allStores, offers])
  const destacadasCount = offers?.filter((o) => o.tier === 'destacada').length ?? 0

  const visible = useMemo(
    () =>
      (offers ?? [])
        .filter((o) => tier === 'todas' || o.tier === 'destacada')
        .filter((o) => !store || o.storeName === store)
        .sort(SORTERS[sort]),
    [offers, tier, store, sort],
  )

  return (
    <div>
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold sm:text-4xl">Ofertas de hoy</h1>
        <p className="mt-3 text-muted-foreground">
          Juegos que una tienda vende al menos un 20% bajo la mediana del mercado, comparando 3 o más
          tiendas chilenas con stock. Las <span className="text-highlight">destacadas</span> están 50% o más
          por debajo.
        </p>
      </header>

      <div className="mt-8 flex flex-wrap items-center gap-3">
        <div role="group" aria-label="Tipo de oferta" className="inline-flex rounded-lg border p-1">
          {(
            [
              ['todas', `Todas${offers ? ` (${offers.length})` : ''}`],
              ['destacadas', `Destacadas (${destacadasCount})`],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              aria-pressed={tier === value}
              onClick={() => setParam('tipo', value, 'todas')}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                tier === value ? 'bg-secondary text-foreground' : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <select
          aria-label="Tienda"
          value={store}
          onChange={(e) => setParam('tienda', e.target.value, '')}
          className="h-10 rounded-lg border bg-background px-3 text-sm"
        >
          <option value="">Todas las tiendas</option>
          {storeOptions.map((s) => (
            // La seleccionada no se deshabilita aunque quede en 0: si no, un
            // link compartido de ayer mostraria el select en blanco.
            <option key={s.name} value={s.name} disabled={s.count === 0 && s.name !== store}>
              {s.name} ({s.count})
            </option>
          ))}
        </select>

        <select
          aria-label="Ordenar"
          value={sort}
          onChange={(e) => setParam('orden', e.target.value, 'descuento')}
          className="h-10 rounded-lg border bg-background px-3 text-sm"
        >
          <option value="descuento">Mayor descuento</option>
          <option value="precio">Menor precio</option>
        </select>
      </div>

      <section aria-live="polite" className="mt-6">
        {isPending && <OfferGridSkeleton />}

        {isError && (
          <div className="rounded-lg border p-6">
            <p className="font-medium">No pudimos cargar las ofertas.</p>
            <Button variant="outline" className="mt-3" onClick={() => refetch()}>
              Reintentar
            </Button>
          </div>
        )}

        {offers && visible.length === 0 && (
          <p className="rounded-lg border p-6 text-muted-foreground">No hay ofertas con estos filtros.</p>
        )}

        {visible.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((offer) => (
              <OfferCard key={`${offer.productId}-${offer.storeName}`} offer={offer} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function OfferGridSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Cargando ofertas">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="overflow-hidden rounded-lg border bg-card">
          <div className="aspect-[4/3] animate-pulse bg-secondary" />
          <div className="space-y-3 p-4">
            <div className="h-3 w-1/3 animate-pulse rounded bg-secondary" />
            <div className="h-4 w-4/5 animate-pulse rounded bg-secondary" />
            <div className="h-6 w-1/2 animate-pulse rounded bg-secondary" />
          </div>
        </div>
      ))}
    </div>
  )
}
