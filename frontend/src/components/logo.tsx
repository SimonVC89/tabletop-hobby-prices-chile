import { cn } from '@/lib/utils'

// Marca como imagen + nombre como texto real (misma fuente y colores del
// logo). Asi el texto se puede dimensionar legible, cosa que el SVG
// horizontal no permite: ahi el texto es ~40% de la altura total.
// En el mosaico el meeple ocupa una sola loseta: bajo ~70px deja de
// distinguirse. Para tamanos chicos se usa la loseta del meeple sola.
const MOSAIC = '/brand/thpc-mosaico-web.svg'
const MEEPLE_TILE = '/brand/thpc-loseta-meeple-web.svg'

const sizes = {
  // Header compacto (al hacer scroll).
  compact: {
    mark: MEEPLE_TILE,
    gap: 'gap-3',
    markSize: 'size-10',
    name: 'text-lg',
    country: 'mt-1 text-[0.6rem]',
    short: true,
  },
  // Header expandido. En celular el nombre completo no cabe junto a la
  // navegacion: siglas.
  sm: {
    mark: MOSAIC,
    gap: 'gap-3 md:gap-4',
    markSize: 'size-20 md:size-24',
    name: 'text-2xl',
    country: 'mt-2 text-xs',
    short: true,
  },
  lg: { mark: MOSAIC, gap: 'gap-7', markSize: 'size-28', name: 'text-4xl', country: 'mt-3 text-sm', short: false },
}

export function Logo({
  size = 'sm',
  className,
}: {
  size?: keyof typeof sizes
  className?: string
}) {
  const s = sizes[size]
  return (
    <span className={cn('inline-flex items-center', s.gap, className)}>
      <img src={s.mark} alt="" aria-hidden="true" className={cn('shrink-0', s.markSize)} />
      <span className="flex flex-col leading-none">
        <span
          aria-hidden="true"
          className={cn('font-mono font-semibold tracking-tight whitespace-nowrap text-foreground', s.name)}
        >
          {s.short ? (
            <>
              <span className="md:hidden">THPC</span>
              <span className="hidden md:inline">Tabletop Hobby Prices</span>
            </>
          ) : (
            'Tabletop Hobby Prices'
          )}
        </span>
        <span
          aria-hidden="true"
          className={cn(
            'font-mono font-medium tracking-[0.45em] text-highlight',
            s.country,
          )}
        >
          CHILE
        </span>
      </span>
      <span className="sr-only">Tabletop Hobby Prices Chile</span>
    </span>
  )
}
