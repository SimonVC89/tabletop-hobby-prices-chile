import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useStores } from '@/api/hooks'
import type { PriceHistory, ProductListing } from '@/api/types'
import { formatCLP, formatDay } from '@/lib/format'
import { addDays, daysBetween, type MarketDay } from '@/lib/price-history'
import { cn } from '@/lib/utils'

/*
 * Historial del mercado: el mejor precio con stock de cada dia (linea
 * principal) y la mediana entre tiendas como referencia punteada. Las
 * tiendas se agregan como lineas propias desde la leyenda, hasta 8 a la vez:
 * con mas, las lineas dejan de distinguirse.
 */

const MAX_STORES = 8
// Hasta cuantas tiendas activas se rotulan con su nombre al final de la linea.
const MAX_LABELED = 4
const SERIES_COLORS = Array.from({ length: MAX_STORES }, (_, i) => `var(--series-${i + 1})`)

const RANGES = [
  { key: '1m', label: '1M', days: 30 },
  { key: '3m', label: '3M', days: 90 },
  { key: '6m', label: '6M', days: 180 },
  { key: 'todo', label: 'Todo', days: Number.POSITIVE_INFINITY },
] as const
type RangeKey = (typeof RANGES)[number]['key']

type StoreStatus = 'stock' | 'sin-stock' | 'sin-datos' | 'excluida'
const STATUS_NOTE: Record<StoreStatus, string | null> = {
  stock: null,
  'sin-stock': 'sin stock',
  'sin-datos': 'sin datos recientes',
  excluida: 'ya no se sigue',
}

interface StoreOption {
  storeId: string
  storeName: string
  status: StoreStatus
  price: number | null
}

type Row = { date: string } & Record<string, number | string | null>

// Claves de datos por tienda: con stock (linea continua) y sin stock (punteada).
const inKey = (id: string) => `s_${id}`
const outKey = (id: string) => `o_${id}`

interface Props {
  history: PriceHistory
  days: MarketDay[]
  listings: ProductListing[]
  className?: string
}

export function PriceHistoryChart({ history, days, listings, className }: Props) {
  const { data: stores } = useStores()
  const [range, setRange] = useState<RangeKey>('todo')
  // Si nunca lo vimos con stock no hay linea de mejor precio: se parte con
  // las tiendas activadas para que se vea su precio publicado (punteado).
  const neverInStock = !days.some((d) => d.best !== null)
  // storeId -> posicion en la paleta. Se asigna al activar y se mantiene
  // mientras siga activa: agregar o quitar otra tienda no la repinta.
  const [active, setActive] = useState<Record<string, number>>(() =>
    neverInStock
      ? Object.fromEntries(
          storeOptions(history, listings, undefined)
            .slice(0, MAX_STORES)
            .map((o, i) => [o.storeId, i]),
        )
      : {},
  )
  const [hoverDate, setHoverDate] = useState<string | null>(null)
  // Tienda resaltada al pasar sobre su linea o su boton: las demas se atenuan.
  const [hovered, setHovered] = useState<string | null>(null)

  const options = useMemo(() => storeOptions(history, listings, stores), [history, listings, stores])
  const activeIds = Object.keys(active)
  const activeCount = activeIds.length
  const emphasis = hovered !== null && hovered in active ? hovered : null

  const lastDate = days.at(-1)?.date
  const span = days.length > 0 && lastDate ? daysBetween(days[0].date, lastDate) : 0
  const selectedRange = RANGES.find((r) => r.key === range)!
  const visibleDays = useMemo(() => {
    if (!lastDate || !Number.isFinite(selectedRange.days)) return days
    const from = addDays(lastDate, -selectedRange.days)
    return days.filter((d) => d.date >= from)
  }, [days, lastDate, selectedRange])

  const rows = useMemo(() => buildRows(visibleDays, Object.keys(active)), [visibleDays, active])
  const yAxis = useMemo(() => priceAxis(rows), [rows])
  // Nombre al final de cada linea solo con pocas tiendas: con mas se pisan.
  const labels = useMemo(
    () => (Object.keys(active).length <= MAX_LABELED ? endLabels(rows, Object.keys(active), yAxis.domain) : new Map()),
    [rows, active, yAxis.domain],
  )

  if (days.length === 0) {
    return (
      <div className={cn('rounded-lg border bg-card p-5 text-sm text-muted-foreground', className)}>
        Todavía no tenemos historial de precios para este juego.
      </div>
    )
  }

  const toggle = (storeId: string) =>
    setActive((prev) => {
      if (storeId in prev) {
        const { [storeId]: _removed, ...rest } = prev
        return rest
      }
      const used = new Set(Object.values(prev))
      const slot = SERIES_COLORS.findIndex((_, i) => !used.has(i))
      return slot === -1 ? prev : { ...prev, [storeId]: slot }
    })

  // Lectura de arriba: el dia bajo el puntero, o el ultimo con datos.
  const readoutDay =
    (hoverDate && visibleDays.find((d) => d.date === hoverDate)) ||
    [...visibleDays].reverse().find((d) => d.observed) ||
    visibleDays.at(-1)!
  const nameById = new Map(options.map((o) => [o.storeId, o.storeName]))
  const dimmed = (storeId?: string) => emphasis !== null && emphasis !== storeId
  const labelFor = (key: string) => {
    const l = labels.get(key)
    if (!l) return undefined
    return endLabel(l.index, l.dy, nameById.get(l.storeId) ?? '', dimmed(l.storeId), l.index < rows.length / 4)
  }

  return (
    <div className={cn('rounded-lg border bg-card p-4 sm:p-5', className)}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <dl className="flex flex-wrap gap-x-6 gap-y-2" aria-live="off">
          <Readout label="Fecha">{formatDay(readoutDay.date)}</Readout>
          <Readout label="Mejor precio">
            {readoutDay.best !== null ? formatCLP(readoutDay.best) : 'Sin stock'}
            {readoutDay.bestStoreName && (
              <span className="ml-2 font-sans text-sm font-normal text-muted-foreground">
                {readoutDay.bestStoreName}
              </span>
            )}
          </Readout>
          <Readout label="Mediana" muted>
            {readoutDay.median !== null && readoutDay.storeCount > 1 ? formatCLP(readoutDay.median) : '—'}
          </Readout>
        </dl>

        <div role="group" aria-label="Rango de tiempo" className="inline-flex rounded-lg border p-1">
          {RANGES.map((r) => {
            // Un rango mas largo que el historial mostraria lo mismo que "Todo".
            const enabled = !Number.isFinite(r.days) || span > r.days
            return (
              <button
                key={r.key}
                type="button"
                disabled={!enabled}
                aria-pressed={range === r.key}
                title={enabled ? undefined : 'Todavía no hay historial suficiente para este rango'}
                onClick={() => setRange(r.key)}
                className={cn(
                  'price rounded-md px-2.5 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40',
                  range === r.key ? 'bg-secondary text-foreground' : 'text-muted-foreground enabled:hover:text-foreground',
                )}
              >
                {r.label}
              </button>
            )
          })}
        </div>
      </div>

      {neverInStock && (
        <p className="mt-3 text-sm text-muted-foreground">
          No lo hemos visto con stock en este período: las líneas punteadas son el precio que publicaban las tiendas
          sin stock.
        </p>
      )}

      <div className="mt-4 h-60 sm:h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            // Recharts 3 pinta las lineas en el orden en que se registran: una
            // tienda agregada despues quedaria encima del mejor precio. Al
            // remontar con cada cambio se respeta el orden del JSX.
            key={Object.keys(active).join()}
            data={rows}
            // Margen derecho para que la ultima fecha del eje no se corte.
            margin={{ top: 8, right: 20, bottom: 0, left: 0 }}
            onMouseMove={(state) => {
              const i = Number(state.activeTooltipIndex)
              setHoverDate(Number.isInteger(i) ? (rows[i]?.date ?? null) : null)
            }}
            onMouseLeave={() => setHoverDate(null)}
          >
            <CartesianGrid vertical={false} stroke="var(--border)" strokeOpacity={0.6} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDay}
              interval="preserveStartEnd"
              minTickGap={28}
              tickLine={false}
              axisLine={{ stroke: 'var(--border)' }}
              tick={{ fill: 'var(--muted-foreground)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
              tickMargin={8}
            />
            <YAxis
              domain={yAxis.domain}
              ticks={yAxis.ticks}
              tickFormatter={formatCLP}
              width={72}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--muted-foreground)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
            />
            <Tooltip
              cursor={{ stroke: 'var(--muted-foreground)', strokeDasharray: '3 3' }}
              isAnimationActive={false}
              content={({ active: shown, label }) =>
                shown && typeof label === 'string' ? (
                  <ChartTooltip
                    day={visibleDays.find((d) => d.date === label)}
                    activeStores={Object.entries(active)}
                    nameById={nameById}
                    emphasis={emphasis}
                  />
                ) : null
              }
            />
            {lastDate && <ReferenceLine x={lastDate} stroke="var(--highlight)" strokeOpacity={0.5} />}

            {Object.entries(active).flatMap(([id, slot]) => [
              <Line
                key={outKey(id)}
                dataKey={outKey(id)}
                type="stepAfter"
                stroke={SERIES_COLORS[slot]}
                strokeWidth={1.5}
                strokeDasharray="2 4"
                strokeOpacity={dimmed(id) ? 0.2 : 0.8}
                dot={false}
                activeDot={false}
                label={labelFor(outKey(id))}
                isAnimationActive={false}
              />,
              <Line
                key={inKey(id)}
                dataKey={inKey(id)}
                type="stepAfter"
                stroke={SERIES_COLORS[slot]}
                strokeWidth={emphasis === id ? 3 : 2}
                strokeOpacity={dimmed(id) ? 0.25 : 1}
                dot={isolatedDot(rows, inKey(id), SERIES_COLORS[slot])}
                activeDot={{ r: 4, fill: SERIES_COLORS[slot], stroke: 'var(--card)', strokeWidth: 2 }}
                label={labelFor(inKey(id))}
                isAnimationActive={false}
              />,
            ])}
            <Line
              dataKey="median"
              type="stepAfter"
              stroke="var(--chart-neutral)"
              strokeWidth={1.5}
              strokeDasharray="5 4"
              strokeOpacity={emphasis ? 0.35 : 1}
              dot={false}
              activeDot={false}
              isAnimationActive={false}
            />
            <Line
              dataKey="best"
              type="stepAfter"
              stroke="var(--foreground)"
              strokeOpacity={emphasis ? 0.35 : 1}
              strokeWidth={2.5}
              dot={isolatedDot(rows, 'best', 'var(--foreground)')}
              activeDot={{ r: 4.5, fill: 'var(--foreground)', stroke: 'var(--card)', strokeWidth: 2 }}
              isAnimationActive={false}
            />
            {/* Zonas invisibles de 14px sobre cada tienda: apuntarle a una
                linea de 2px es casi imposible, asi el resaltado responde. */}
            {activeIds.map((id) => (
              <Line
                key={`hit_${id}`}
                dataKey={(r: Row) => r[inKey(id)] ?? r[outKey(id)]}
                type="stepAfter"
                stroke="transparent"
                strokeWidth={14}
                dot={false}
                activeDot={false}
                isAnimationActive={false}
                onMouseEnter={() => setHovered(id)}
                onMouseLeave={() => setHovered(null)}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <Legend
        options={options}
        active={active}
        emphasis={emphasis}
        onToggle={toggle}
        onHover={setHovered}
        onClear={() => setActive({})}
        full={activeCount >= MAX_STORES}
      />

      <DataTable days={visibleDays} activeStores={Object.entries(active)} nameById={nameById} />
    </div>
  )
}

function Readout({ label, muted, children }: { label: string; muted?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={cn('price mt-0.5 text-lg font-semibold', muted && 'text-muted-foreground')}>{children}</dd>
    </div>
  )
}

function ChartTooltip({
  day,
  activeStores,
  nameById,
  emphasis,
}: {
  day: MarketDay | undefined
  activeStores: [string, number][]
  nameById: Map<string, string>
  emphasis: string | null
}) {
  if (!day) return null
  return (
    <div className="min-w-48 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-lg">
      <p className="text-muted-foreground">{formatDay(day.date)}</p>
      <TooltipRow swatch={<LineKey color="var(--foreground)" />} value={day.best !== null ? formatCLP(day.best) : 'Sin stock'}>
        Mejor precio{day.bestStoreName && ` · ${day.bestStoreName}`}
      </TooltipRow>
      {day.median !== null && day.storeCount > 1 && (
        <TooltipRow swatch={<LineKey color="var(--chart-neutral)" dashed />} value={formatCLP(day.median)}>
          Mediana
        </TooltipRow>
      )}
      {activeStores.length > 0 && <div className="my-1.5 border-t" />}
      {activeStores.map(([id, slot]) => {
        const p = day.stores[id]
        return (
          <TooltipRow
            key={id}
            swatch={<LineKey color={SERIES_COLORS[slot]} dashed={p ? !p.inStock : false} />}
            value={p ? formatCLP(p.price) : '—'}
            muted={!p || !p.inStock}
            highlighted={emphasis === id}
          >
            {nameById.get(id)}
            {p && !p.inStock && ' · sin stock'}
          </TooltipRow>
        )
      })}
    </div>
  )
}

/** Valor primero y en alto contraste; el nombre de la serie, secundario. */
function TooltipRow({
  swatch,
  value,
  muted,
  highlighted,
  children,
}: {
  swatch: React.ReactNode
  value: string
  muted?: boolean
  highlighted?: boolean
  children: React.ReactNode
}) {
  return (
    <p className={cn('mt-1 flex items-center gap-2', highlighted && '-mx-1.5 rounded bg-secondary px-1.5 py-0.5')}>
      {swatch}
      <span className={cn('price font-semibold', muted && 'text-muted-foreground')}>{value}</span>
      <span className={cn('ml-auto pl-3', highlighted ? 'text-foreground' : 'text-muted-foreground')}>{children}</span>
    </p>
  )
}

function LineKey({ color, dashed }: { color: string; dashed?: boolean }) {
  return (
    <svg width="14" height="4" aria-hidden="true" className="shrink-0">
      <line
        x1="0"
        y1="2"
        x2="14"
        y2="2"
        stroke={color}
        strokeWidth="2"
        strokeDasharray={dashed ? '3 2' : undefined}
        strokeLinecap="round"
      />
    </svg>
  )
}

function Legend({
  options,
  active,
  emphasis,
  onToggle,
  onHover,
  onClear,
  full,
}: {
  options: StoreOption[]
  active: Record<string, number>
  emphasis: string | null
  onToggle: (storeId: string) => void
  onHover: (storeId: string | null) => void
  onClear: () => void
  full: boolean
}) {
  const anyActive = Object.keys(active).length > 0
  return (
    <div className="mt-4 border-t pt-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-2">
          <LineKey color="var(--foreground)" /> Mejor precio con stock
        </span>
        <span className="inline-flex items-center gap-2">
          <LineKey color="var(--chart-neutral)" dashed /> Mediana entre tiendas
        </span>
        <span className="inline-flex items-center gap-2">
          <LineKey color="var(--muted-foreground)" dashed /> Tienda sin stock
        </span>
      </div>

      <div className="mt-3 flex items-center justify-between gap-3">
        <p className="text-sm font-medium">
          Comparar tiendas
          <span className="ml-2 text-xs font-normal text-muted-foreground">
            {full ? `Máximo ${MAX_STORES}: quita una para agregar otra` : `hasta ${MAX_STORES} a la vez`}
          </span>
        </p>
        {anyActive && (
          <button
            type="button"
            onClick={onClear}
            className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            Quitar todas
          </button>
        )}
      </div>

      <ul className="mt-2 flex flex-wrap gap-2">
        {options.map((o) => {
          const slot = active[o.storeId]
          const isActive = slot !== undefined
          const note = STATUS_NOTE[o.status]
          return (
            <li key={o.storeId}>
              <button
                type="button"
                aria-pressed={isActive}
                disabled={!isActive && full}
                onClick={() => onToggle(o.storeId)}
                // Pasar por el boton (o enfocarlo con teclado) resalta su linea.
                onMouseEnter={() => onHover(o.storeId)}
                onMouseLeave={() => onHover(null)}
                onFocus={() => onHover(o.storeId)}
                onBlur={() => onHover(null)}
                className={cn(
                  'inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition-colors disabled:cursor-not-allowed disabled:opacity-40',
                  isActive
                    ? 'border-foreground/30 bg-secondary text-foreground'
                    : 'text-muted-foreground enabled:hover:border-foreground/30 enabled:hover:text-foreground',
                  emphasis === o.storeId && 'border-foreground/70',
                )}
              >
                {isActive ? (
                  <LineKey color={SERIES_COLORS[slot]} />
                ) : (
                  <span className="size-2 rounded-full border border-current" aria-hidden="true" />
                )}
                <span className="font-medium">{o.storeName}</span>
                {o.price !== null && <span className="price">{formatCLP(o.price)}</span>}
                {note && <span className="opacity-70">· {note}</span>}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

/**
 * Los mismos datos del grafico, accesibles sin puntero ni color: un dia por
 * fila (solo dias con scraping real, del mas reciente al mas antiguo) y una
 * columna por cada tienda activa en el grafico.
 */
function DataTable({
  days,
  activeStores,
  nameById,
}: {
  days: MarketDay[]
  activeStores: [string, number][]
  nameById: Map<string, string>
}) {
  const observed = days.filter((d) => d.observed).reverse()
  return (
    <details className="mt-4 border-t pt-3">
      <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
        Ver los datos como tabla
      </summary>
      <div className="mt-3 max-h-72 overflow-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="sticky top-0 bg-card text-xs text-muted-foreground">
            <tr>
              <th scope="col" className="py-2 pr-4 font-medium">Fecha</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Mejor precio</th>
              <th scope="col" className="py-2 pr-4 font-medium">Tienda</th>
              <th scope="col" className="py-2 pr-4 text-right font-medium">Mediana</th>
              {activeStores.map(([id, slot]) => (
                <th key={id} scope="col" className="py-2 pr-4 text-right font-medium">
                  <span className="inline-flex items-center gap-1.5">
                    <LineKey color={SERIES_COLORS[slot]} />
                    {nameById.get(id)}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {observed.map((d) => (
              <tr key={d.date}>
                <td className="price py-2 pr-4">{formatDay(d.date)}</td>
                <td className="price py-2 pr-4 text-right">{d.best !== null ? formatCLP(d.best) : '—'}</td>
                <td className="py-2 pr-4 text-muted-foreground">{d.bestStoreName ?? '—'}</td>
                <td className="price py-2 pr-4 text-right text-muted-foreground">
                  {d.median !== null && d.storeCount > 1 ? formatCLP(d.median) : '—'}
                </td>
                {activeStores.map(([id]) => {
                  const p = d.stores[id]
                  return (
                    <td key={id} className={cn('price py-2 pr-4 text-right', (!p || !p.inStock) && 'text-muted-foreground')}>
                      {p ? formatCLP(p.price) : '—'}
                      {p && !p.inStock && <span className="font-sans text-xs"> sin stock</span>}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

// --- datos ---------------------------------------------------------------

const STATUS_ORDER: Record<StoreStatus, number> = { stock: 0, 'sin-stock': 1, 'sin-datos': 2, excluida: 3 }

/** Tiendas con historial, ordenadas como en la lista de precios: primero las con stock y mas baratas. */
function storeOptions(
  history: PriceHistory,
  listings: ProductListing[],
  stores: { id: string; status: string }[] | undefined,
): StoreOption[] {
  const listingByStore = new Map(listings.map((l) => [l.storeId, l]))
  const excluded = new Set((stores ?? []).filter((s) => s.status === 'excluded').map((s) => s.id))
  return history.series
    .map((s): StoreOption => {
      const l = listingByStore.get(s.storeId)
      const status: StoreStatus = excluded.has(s.storeId) ? 'excluida' : !l ? 'sin-datos' : l.inStock ? 'stock' : 'sin-stock'
      return { storeId: s.storeId, storeName: s.storeName, status, price: l?.price ?? null }
    })
    .sort(
      (a, b) =>
        STATUS_ORDER[a.status] - STATUS_ORDER[b.status] ||
        (a.price ?? Number.POSITIVE_INFINITY) - (b.price ?? Number.POSITIVE_INFINITY) ||
        a.storeName.localeCompare(b.storeName, 'es'),
    )
}

function buildRows(days: MarketDay[], activeIds: string[]): Row[] {
  const rows: Row[] = days.map((d) => ({
    date: d.date,
    best: d.best,
    // Con una sola tienda, la "mediana" seria su propio precio.
    median: d.storeCount > 1 ? d.median : null,
  }))
  for (const id of activeIds) {
    days.forEach((d, i) => {
      const p = d.stores[id]
      const prev = days[i - 1]?.stores[id]
      const next = days[i + 1]?.stores[id]
      rows[i][inKey(id)] = p?.inStock ? p.price : null
      // El tramo punteado (sin stock) se une a los puntos con stock vecinos
      // para que la linea de la tienda no quede cortada en el cambio.
      const touchesOut = (p && !p.inStock) || (p?.inStock && ((next && !next.inStock) || (prev && !prev.inStock)))
      rows[i][outKey(id)] = touchesOut ? p!.price : null
    })
  }
  return rows
}

/**
 * Eje Y ajustado a los precios visibles (no desde $0: aplastaria la
 * variacion), con marcas en montos redondos ($10.000, $25.000...).
 */
function priceAxis(rows: Row[]): { domain: [number, number]; ticks: number[] } {
  const values = rows.flatMap((r) =>
    Object.entries(r).flatMap(([k, v]) => (k !== 'date' && typeof v === 'number' ? [v] : [])),
  )
  if (values.length === 0) return { domain: [0, 1000], ticks: [0, 1000] }
  const min = Math.min(...values)
  const max = Math.max(...values)
  const pad = Math.max((max - min) * 0.1, max * 0.05)
  const step = niceStep((max - min + 2 * pad) / 4)
  const lo = Math.max(0, Math.floor((min - pad) / step) * step)
  const hi = Math.ceil((max + pad) / step) * step
  const ticks: number[] = []
  for (let t = lo; t <= hi; t += step) ticks.push(t)
  return { domain: [lo, hi], ticks }
}

/** El paso "redondo" (1, 2, 2,5 o 5 x 10^n) mas cercano por arriba. */
function niceStep(raw: number) {
  const pow = 10 ** Math.floor(Math.log10(raw))
  return [1, 2, 2.5, 5, 10].map((m) => m * pow).find((s) => s >= raw)!
}

interface EndLabelPos {
  storeId: string
  index: number
  /** Desplazamiento vertical en px: separa nombres de tiendas con precios parecidos. */
  dy: number
}

/**
 * Donde va el nombre de cada tienda: en el ultimo punto de su linea (con o
 * sin stock). Si dos lineas terminan casi en el mismo precio, los nombres se
 * apilan en vez de pisarse. Devuelve un mapa dataKey -> posicion.
 */
function endLabels(rows: Row[], ids: string[], [lo, hi]: [number, number]): Map<string, EndLabelPos> {
  const ends = ids.flatMap((id) => {
    for (let i = rows.length - 1; i >= 0; i--) {
      const vIn = rows[i][inKey(id)]
      const vOut = rows[i][outKey(id)]
      if (typeof vIn === 'number') return [{ id, key: inKey(id), index: i, value: vIn }]
      if (typeof vOut === 'number') return [{ id, key: outKey(id), index: i, value: vOut }]
    }
    return []
  })
  ends.sort((a, b) => b.value - a.value)

  const near = (hi - lo) * 0.08
  const result = new Map<string, EndLabelPos>()
  let prev: { index: number; value: number; dy: number } | null = null
  for (const e of ends) {
    const stacked: boolean = prev !== null && Math.abs(prev.index - e.index) <= 3 && prev.value - e.value < near
    const dy: number = stacked && prev ? prev.dy + 13 : -7
    result.set(e.key, { storeId: e.id, index: e.index, dy })
    prev = { index: e.index, value: e.value, dy }
  }
  return result
}

/**
 * Nombre de la tienda junto al final de su linea, en color de texto (no el
 * de la serie) con un borde del color de la tarjeta para que se lea encima
 * de otras lineas.
 */
function endLabel(index: number, dy: number, name: string, dimmed: boolean, atStart: boolean) {
  function EndLabel({ x, y, index: i }: { x?: number | string; y?: number | string; index?: number }) {
    if (i !== index || x == null || y == null) return <g />
    return (
      <text
        x={Number(x) + (atStart ? 6 : -6)}
        y={Number(y) + dy}
        textAnchor={atStart ? 'start' : 'end'}
        fontSize={11}
        fill="var(--foreground)"
        fillOpacity={dimmed ? 0.35 : 1}
        stroke="var(--card)"
        strokeWidth={3}
        paintOrder="stroke"
        style={{ fontFamily: 'var(--font-sans)' }}
      >
        {name}
      </text>
    )
  }
  return EndLabel
}

/**
 * Un punto sin vecinos (un solo dia con datos) no dibuja linea: se marca
 * con un punto para que no desaparezca.
 */
function isolatedDot(rows: Row[], key: string, color: string) {
  function Dot({ cx, cy, index }: { cx?: number; cy?: number; index?: number }) {
    const i = index ?? 0
    const isolated = rows[i]?.[key] != null && rows[i - 1]?.[key] == null && rows[i + 1]?.[key] == null
    if (!isolated || cx == null || cy == null) return <g key={`${key}-${i}`} />
    return <circle key={`${key}-${i}`} cx={cx} cy={cy} r={3.5} fill={color} stroke="var(--card)" strokeWidth={2} />
  }
  return Dot
}
