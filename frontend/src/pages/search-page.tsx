import { ChevronLeft, ChevronRight, Search, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { useProducts } from '@/api/hooks'
import type { ProductQuery, ProductSort } from '@/api/types'
import { ProductCard } from '@/components/product-card'
import { Button } from '@/components/ui/button'
import { formatCount } from '@/lib/format'
import { MIN_STORES_FOR_MEDIAN, OFFER_MIN_DISCOUNT } from '@/lib/price-history'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 24
const SEARCH_DELAY_MS = 250

// En la URL van en espanol (se comparten); hacia la API, el valor del contrato.
const SORTS: { value: string; sort: ProductSort; label: string }[] = [
  { value: 'relevancia', sort: 'relevance', label: 'Relevancia' },
  { value: 'menor-precio', sort: 'price-asc', label: 'Menor precio' },
  { value: 'mayor-precio', sort: 'price-desc', label: 'Mayor precio' },
  { value: 'descuento', sort: 'discount', label: 'Mayor descuento' },
  { value: 'tiendas', sort: 'stores', label: 'Más tiendas' },
]

export function SearchPage() {
  const [params, setParams] = useSearchParams()

  const q = params.get('q') ?? ''
  const sortValue = SORTS.some((s) => s.value === params.get('orden')) ? params.get('orden')! : 'relevancia'
  const onlyOffers = params.get('oferta') === '1'
  const onlyComparable = params.get('tiendas') === '3'
  const includeOutOfStock = params.get('agotados') !== '0'
  const page = Math.max(1, Number(params.get('pagina')) || 1)

  const query: ProductQuery = {
    q: q || undefined,
    sort: SORTS.find((s) => s.value === sortValue)!.sort,
    minDiscount: onlyOffers ? OFFER_MIN_DISCOUNT : undefined,
    minStores: onlyComparable ? MIN_STORES_FOR_MEDIAN : undefined,
    includeOutOfStock,
    page,
    pageSize: PAGE_SIZE,
  }
  const { data, isPending, isError, isPlaceholderData, refetch } = useProducts(query)

  /** Cambia un parametro; cualquier cambio de filtro vuelve a la pagina 1. */
  const update = (changes: Record<string, string | null>) => {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(changes)) {
      if (value === null) next.delete(key)
      else next.set(key, value)
    }
    if (!('pagina' in changes)) next.delete('pagina')
    setParams(next, { replace: true })
  }

  const goToPage = (n: number) => {
    update({ pagina: n > 1 ? String(n) : null })
    window.scrollTo({ top: 0 })
  }

  return (
    <div>
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold sm:text-4xl">Buscar juegos</h1>
        <p className="mt-3 text-muted-foreground">
          Todos los juegos de mesa que seguimos en tiendas chilenas, estén o no en oferta. Los agotados aparecen con
          el último precio que vimos.
        </p>
      </header>

      <SearchBox value={q} onChange={(value) => update({ q: value || null })} />

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <FilterChip pressed={onlyOffers} onClick={() => update({ oferta: onlyOffers ? null : '1' })}>
          En oferta
        </FilterChip>
        <FilterChip pressed={onlyComparable} onClick={() => update({ tiendas: onlyComparable ? null : '3' })}>
          En {MIN_STORES_FOR_MEDIAN}+ tiendas
        </FilterChip>
        <FilterChip pressed={includeOutOfStock} onClick={() => update({ agotados: includeOutOfStock ? '0' : null })}>
          Incluir agotados
        </FilterChip>

        <select
          aria-label="Ordenar"
          value={sortValue}
          onChange={(e) => update({ orden: e.target.value === 'relevancia' ? null : e.target.value })}
          className="ml-auto h-9 rounded-lg border bg-background px-3 text-sm"
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      <section aria-live="polite" aria-busy={isPending || isPlaceholderData} className="mt-6">
        {data && (
          <p className="mb-4 text-sm text-muted-foreground">
            {data.totalItems === 1 ? '1 juego' : `${formatCount(data.totalItems)} juegos`}
            {q && (
              <>
                {' '}
                para <span className="text-foreground">“{q}”</span>
              </>
            )}
          </p>
        )}

        {isPending && <GridSkeleton />}

        {isError && (
          <div className="rounded-lg border p-6">
            <p className="font-medium">No pudimos cargar el catálogo.</p>
            <Button variant="outline" className="mt-3" onClick={() => refetch()}>
              Reintentar
            </Button>
          </div>
        )}

        {data && data.items.length === 0 && (
          <div className="rounded-lg border p-6">
            <p className="font-medium">No encontramos juegos{q && ` para “${q}”`}.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Prueba con menos palabras o quita algún filtro. Solo seguimos juegos de mesa de tiendas chilenas.
            </p>
          </div>
        )}

        {data && data.items.length > 0 && (
          // Mientras carga la pagina siguiente se mantiene la actual, atenuada.
          <div className={cn('transition-opacity', isPlaceholderData && 'opacity-60')}>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
              {data.items.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
            {data.totalPages > 1 && <Pagination page={data.page} totalPages={data.totalPages} onChange={goToPage} />}
          </div>
        )}
      </section>
    </div>
  )
}

/**
 * Busca mientras se escribe, pero espera una pausa breve para no buscar en
 * cada tecla ni llenar el historial del navegador.
 */
function SearchBox({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const [text, setText] = useState(value)
  const [syncedValue, setSyncedValue] = useState(value)

  // Si la URL cambia desde afuera (atras/adelante), el campo la sigue; si es
  // el mismo texto, se respeta lo escrito (p. ej. un espacio al final).
  if (value !== syncedValue) {
    setSyncedValue(value)
    if (text.trim() !== value) setText(value)
  }

  useEffect(() => {
    if (text.trim() === value) return
    const timer = setTimeout(() => onChange(text.trim()), SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [text, value, onChange])

  return (
    <form role="search" className="relative mt-8 max-w-2xl" onSubmit={(e) => e.preventDefault()}>
      <Search className="pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
      <input
        type="search"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Catan, Azul, Wingspan…"
        aria-label="Buscar juegos por nombre"
        autoComplete="off"
        className="h-12 w-full rounded-lg border bg-card pr-11 pl-12 text-base outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40 [&::-webkit-search-cancel-button]:hidden"
      />
      {text && (
        <button
          type="button"
          aria-label="Borrar búsqueda"
          onClick={() => setText('')}
          className="absolute top-1/2 right-3 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
        >
          <X className="size-4" />
        </button>
      )}
    </form>
  )
}

function FilterChip({ pressed, onClick, children }: { pressed: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className={cn(
        'h-9 rounded-full border px-3.5 text-sm transition-colors',
        pressed
          ? 'border-primary/60 bg-primary/15 text-foreground'
          : 'text-muted-foreground hover:border-foreground/30 hover:text-foreground',
      )}
    >
      {children}
    </button>
  )
}

function Pagination({ page, totalPages, onChange }: { page: number; totalPages: number; onChange: (n: number) => void }) {
  return (
    <nav aria-label="Paginación" className="mt-8 flex items-center justify-center gap-3">
      <Button variant="outline" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        <ChevronLeft aria-hidden="true" /> Anterior
      </Button>
      <span className="price text-sm text-muted-foreground">
        {page} / {totalPages}
      </span>
      <Button variant="outline" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
        Siguiente <ChevronRight aria-hidden="true" />
      </Button>
    </nav>
  )
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4" aria-label="Cargando juegos">
      {Array.from({ length: 8 }, (_, i) => (
        <div key={i} className="overflow-hidden rounded-lg border bg-card">
          <div className="aspect-[4/3] animate-pulse bg-secondary" />
          <div className="space-y-2 p-3">
            <div className="h-4 w-4/5 animate-pulse rounded bg-secondary" />
            <div className="h-5 w-1/2 animate-pulse rounded bg-secondary" />
          </div>
        </div>
      ))}
    </div>
  )
}
