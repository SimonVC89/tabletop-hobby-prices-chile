import { ArrowRight, BookOpen, Search, Send } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router'
import { useMeta, useOffers, usePriceDrops } from '@/api/hooks'
import type { Offer, PriceDrop } from '@/api/types'
import { ProductImage } from '@/components/product-image'
import { Button } from '@/components/ui/button'
import { formatCLP, formatCount, formatPct, formatUpdated } from '@/lib/format'
import { cn } from '@/lib/utils'

const BOARD_SIZE = 6
const DROPS_SHOWN = 8

/**
 * Portada "mesa de juego": a la izquierda que es esto y un buscador; a la derecha
 * un tablero con las 6 mejores ofertas del dia. Debajo, lo que bajo de precio en las
 * ultimas 24 horas y dos invitaciones (Telegram y como funciona).
 */
export function HomePage() {
  const { data: meta } = useMeta()
  const { data: offers, isPending: offersPending } = useOffers()

  return (
    <div className="space-y-16 sm:space-y-20">
      <section className="grid items-center gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] lg:gap-14">
        <div>
          <p className="font-mono text-xs font-semibold tracking-wide text-highlight uppercase">
            {meta ? `Actualizado ${formatUpdated(meta.lastUpdated)}` : 'Precios de tiendas chilenas'}
          </p>
          <h1 className="mt-3 text-4xl leading-[1.1] font-bold text-balance sm:text-5xl">
            Las ofertas reales de juegos de mesa en Chile
          </h1>
          <p className="mt-4 max-w-xl text-lg text-pretty text-muted-foreground">
            Precios de {meta ? meta.activeStores : 'varias'} tiendas chilenas, comparados dos veces al día. Aquí
            solo es oferta lo que una tienda vende al menos 20% bajo lo que cobra el resto.
          </p>

          <dl className="mt-8 grid max-w-md grid-cols-3 gap-3">
            <Stat label="juegos" value={meta && formatCount(meta.totalGames)} />
            <Stat label="tiendas" value={meta && formatCount(meta.activeStores)} />
            <Stat label="ofertas hoy" value={offers && formatCount(offers.length)} />
          </dl>

          <HomeSearch />
        </div>

        <OfferBoard offers={offers} pending={offersPending} />
      </section>

      <PriceDrops />

      <section aria-label="Más sobre el sitio" className="grid gap-4 md:grid-cols-2">
        <InviteCard
          to="/telegram"
          icon={<Send className="size-5" aria-hidden="true" />}
          title="Avisos por Telegram"
          text="Un resumen de las ofertas en tu celular y aviso cuando baja un juego que sigues."
          cta="Ver cómo funcionan los avisos"
        />
        <InviteCard
          to="/como-funciona"
          icon={<BookOpen className="size-5" aria-hidden="true" />}
          title="Cómo funciona"
          text="De dónde salen los precios, cómo se decide qué es oferta y cómo se reconoce el mismo juego en tiendas distintas."
          cta="Leer cómo está hecho"
        />
      </section>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | undefined | null }) {
  return (
    // En un <dl> el <dt> va primero; flex-col-reverse pone la cifra arriba en pantalla.
    <div className="flex flex-col-reverse rounded-lg border bg-card px-3 py-3">
      <dt className="mt-0.5 text-xs text-muted-foreground">{label}</dt>
      <dd className="price text-2xl font-semibold">
        {value ?? <span className="inline-block h-7 w-12 animate-pulse rounded bg-secondary align-middle" />}
      </dd>
    </div>
  )
}

function HomeSearch() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')

  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault()
        const query = q.trim()
        navigate(query ? `/juegos?q=${encodeURIComponent(query)}` : '/juegos')
      }}
      className="mt-8 flex max-w-md gap-2"
    >
      <label htmlFor="home-search" className="sr-only">
        Buscar un juego
      </label>
      <div className="relative flex-1">
        <Search
          className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <input
          id="home-search"
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Busca un juego, ej. Catan"
          className="h-11 w-full rounded-lg border bg-background pr-3 pl-9 text-base outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>
      <Button type="submit" className="h-11 px-5">
        Buscar
      </Button>
    </form>
  )
}

// --- tablero de ofertas ------------------------------------------------

function OfferBoard({ offers, pending }: { offers: Offer[] | undefined; pending: boolean }) {
  // Un juego por casilla: si dos tiendas lo tienen en oferta, gana el mayor descuento.
  const top: Offer[] = []
  for (const o of [...(offers ?? [])].sort((a, b) => b.discountPct - a.discountPct)) {
    if (top.length === BOARD_SIZE) break
    if (!top.some((t) => t.productId === o.productId)) top.push(o)
  }

  if (!pending && top.length === 0) return null

  return (
    <section aria-labelledby="board-title" className="rounded-2xl border bg-secondary/40 p-3 sm:p-4">
      <div className="flex items-baseline justify-between gap-3 px-1 pb-3">
        <h2 id="board-title" className="text-sm font-semibold">
          Mejores ofertas de hoy
        </h2>
        {offers && (
          <Link to="/ofertas" className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">
            Ver las {offers.length} <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        )}
      </div>

      <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3">
        {pending
          ? Array.from({ length: BOARD_SIZE }, (_, i) => (
              <li key={i} className="aspect-[4/5] animate-pulse rounded-lg bg-secondary" aria-hidden="true" />
            ))
          : top.map((offer) => (
              <li key={offer.productId}>
                <BoardTile offer={offer} />
              </li>
            ))}
      </ul>
    </section>
  )
}

function BoardTile({ offer }: { offer: Offer }) {
  return (
    <Link
      to={`/juego/${offer.productId}`}
      aria-label={`${offer.productName}: ${formatCLP(offer.price)} en ${offer.storeName}, ${formatPct(offer.discountPct)} bajo la mediana`}
      className="group relative flex aspect-[4/5] flex-col overflow-hidden rounded-lg border bg-card outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <ProductImage
        src={offer.imageUrl}
        alt=""
        imagePadding="p-2"
        className="min-h-0 flex-1 rounded-none transition-transform duration-300 group-hover:scale-[1.03] motion-reduce:transition-none"
      />
      <span className="price absolute top-2 left-2 rounded-md bg-deal px-1.5 py-0.5 text-xs font-semibold text-background">
        −{formatPct(offer.discountPct)}
      </span>
      <div className="border-t bg-card px-2.5 py-2">
        <p className="truncate text-xs text-muted-foreground group-hover:text-foreground">{offer.productName}</p>
        <p className="price text-base font-semibold">{formatCLP(offer.price)}</p>
      </div>
    </Link>
  )
}

// --- bajas del dia -----------------------------------------------------

function PriceDrops() {
  const { data: drops } = usePriceDrops()
  // Se oculta si no hay bajas (o mientras carga): es un extra, no el centro de la portada.
  if (!drops || drops.length === 0) return null

  return (
    <section aria-labelledby="drops-title">
      <h2 id="drops-title" className="text-2xl font-bold">
        Bajaron en las últimas 24 horas
      </h2>
      <p className="mt-2 text-muted-foreground">
        Juegos con stock cuyo precio bajó 5% o más en alguna tienda. No siempre es oferta: a veces solo vuelve a su
        precio normal.
      </p>

      <ul className="mt-6 divide-y rounded-lg border bg-card">
        {drops.slice(0, DROPS_SHOWN).map((drop) => (
          <li key={drop.productId}>
            <DropRow drop={drop} />
          </li>
        ))}
      </ul>
    </section>
  )
}

function DropRow({ drop }: { drop: PriceDrop }) {
  return (
    <Link
      to={`/juego/${drop.productId}`}
      className="flex items-center gap-3 px-3 py-3 transition-colors outline-none hover:bg-secondary/50 focus-visible:bg-secondary/50 sm:gap-4 sm:px-4"
    >
      <ProductImage src={drop.imageUrl} alt="" imagePadding="p-1" className="size-14 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{drop.productName}</p>
        <p className="text-sm text-muted-foreground">{drop.storeName}</p>
      </div>
      <div className="shrink-0 text-right">
        <p className="price font-semibold">
          <span className="sr-only">Antes </span>
          <s className="mr-2 text-sm font-normal text-muted-foreground">{formatCLP(drop.previousPrice)}</s>
          <span className="sr-only">, ahora </span>
          {formatCLP(drop.price)}
        </p>
        <p className="price text-sm font-semibold text-deal">−{formatPct(drop.dropPct)}</p>
      </div>
    </Link>
  )
}

// --- invitaciones ------------------------------------------------------

function InviteCard({ to, icon, title, text, cta }: { to: string; icon: ReactNode; title: string; text: string; cta: string }) {
  return (
    <Link
      to={to}
      className={cn(
        'group flex flex-col rounded-lg border bg-card p-5 transition-colors outline-none',
        'hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring',
      )}
    >
      <span className="inline-flex size-9 items-center justify-center rounded-md bg-secondary text-primary">{icon}</span>
      <h2 className="mt-4 text-lg font-semibold">{title}</h2>
      <p className="mt-1 text-muted-foreground">{text}</p>
      <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary">
        {cta} <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
      </span>
    </Link>
  )
}
