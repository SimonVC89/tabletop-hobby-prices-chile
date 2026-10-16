import { Info, Minus, PackageX, Sparkles, TrendingDown, type LucideIcon } from 'lucide-react'
import { formatCLP, formatDay, formatPct } from '@/lib/format'
import { MIN_STORES_FOR_MEDIAN, type PriceAnalysis, type Verdict } from '@/lib/price-history'
import { cn } from '@/lib/utils'

// El veredicto nunca va solo con color: siempre icono + texto.
const VERDICTS: Record<Verdict, { label: string; icon: LucideIcon; className: string }> = {
  excepcional: { label: 'Precio excepcional', icon: Sparkles, className: 'text-highlight' },
  'buen-precio': { label: 'Buen precio hoy', icon: TrendingDown, className: 'text-deal' },
  normal: { label: 'Precio de mercado', icon: Minus, className: 'text-foreground' },
  'pocas-tiendas': { label: 'Pocas tiendas para comparar', icon: Info, className: 'text-muted-foreground' },
  'sin-stock': { label: 'Sin stock hoy', icon: PackageX, className: 'text-muted-foreground' },
}

// Bajo este numero de dias se avisa que el analisis todavia es preliminar.
const SHORT_HISTORY_DAYS = 30

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

export function PriceAnalysisPanel({ analysis, className }: { analysis: PriceAnalysis; className?: string }) {
  const { verdict, best, median, storeCount, discountPct, savings, historyDays, lowest, cheaperBefore } = analysis
  const v = VERDICTS[verdict]
  const highlighted = verdict === 'excepcional' || verdict === 'buen-precio'

  return (
    <section
      aria-labelledby="analisis-titulo"
      className={cn('rounded-lg border bg-card p-5', highlighted && 'border-deal/40', className)}
    >
      <h3 id="analisis-titulo" className="text-base font-semibold">
        Análisis del precio
      </h3>

      <p className={cn('mt-4 flex items-center gap-2 text-sm font-medium', v.className)}>
        <v.icon className="size-4" aria-hidden="true" />
        {v.label}
      </p>

      {best && (
        <p className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="price text-3xl font-semibold">{formatCLP(best.price)}</span>
          {savings !== null && discountPct !== null && (
            <span className="text-sm text-deal">
              ahorras <span className="price">{formatCLP(savings)}</span>
            </span>
          )}
        </p>
      )}

      <div className="mt-3 space-y-1 text-sm text-muted-foreground">
        {discountPct !== null && (
          <p>
            {discountPct >= 0.5 ? (
              <>
                Está <strong className="font-medium text-foreground">{formatPct(discountPct)} bajo la mediana</strong> de{' '}
                {plural(storeCount, 'tienda', 'tiendas')} con stock.
              </>
            ) : (
              <>Está en la mediana de {plural(storeCount, 'tienda', 'tiendas')} con stock.</>
            )}
          </p>
        )}
        {verdict === 'pocas-tiendas' && (
          <p>
            Solo {plural(storeCount, 'tienda tiene', 'tiendas tienen')} stock: con menos de {MIN_STORES_FOR_MEDIAN} la
            mediana no es confiable.
          </p>
        )}
        {verdict === 'sin-stock' && <p>Ninguna de las tiendas que seguimos lo tiene disponible hoy.</p>}
        {historyDays === 0 ? (
          <p>Todavía no lo hemos visto con stock en las tiendas que seguimos.</p>
        ) : (
          <p>
            Basado en <strong className="font-medium text-foreground">{plural(historyDays, 'día', 'días')}</strong> de
            precios.
            {historyDays < SHORT_HISTORY_DAYS && ' El análisis mejora a medida que juntamos más historial.'}
          </p>
        )}
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-4 border-t pt-4 text-sm">
        {/* Con una sola tienda, la "mediana" seria su propio precio. */}
        <Stat label="Mediana del mercado">{median !== null && storeCount > 1 ? formatCLP(median) : '—'}</Stat>
        <Stat label="Más bajo registrado">
          {lowest ? (
            <>
              {formatCLP(lowest.price)}
              <span className="mt-0.5 block font-sans text-xs font-normal text-muted-foreground">
                {formatDay(lowest.date)} · {lowest.storeName}
              </span>
            </>
          ) : (
            '—'
          )}
        </Stat>
        <Stat label="¿Estuvo más barato antes?" className="col-span-2">
          {!best ? (
            '—'
          ) : historyDays <= 1 ? (
            <span className="font-sans font-normal text-muted-foreground">Todavía no hay días anteriores para comparar</span>
          ) : cheaperBefore ? (
            <>
              Sí, {formatCLP(cheaperBefore.price)}
              <span className="font-sans font-normal text-muted-foreground">
                {' '}
                el {formatDay(cheaperBefore.date)} en {cheaperBefore.storeName}
              </span>
            </>
          ) : (
            <span className="font-sans">No, es el más bajo que hemos visto</span>
          )}
        </Stat>
      </dl>
    </section>
  )
}

function Stat({ label, className, children }: { label: string; className?: string; children: React.ReactNode }) {
  return (
    <div className={className}>
      <dt className="text-xs tracking-wide text-muted-foreground uppercase">{label}</dt>
      <dd className="price mt-1 font-medium">{children}</dd>
    </div>
  )
}
