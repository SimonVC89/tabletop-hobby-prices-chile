import { cn } from '@/lib/utils'

// Mosaico como imagen + nombre como texto real (misma fuente y colores del
// logo). Asi el texto se puede dimensionar legible, cosa que el SVG
// horizontal no permite: ahi el texto es ~40% de la altura total.
const sizes = {
  sm: { gap: 'gap-3', mosaic: 'size-10 sm:size-12', name: 'text-base sm:text-lg', country: 'mt-1.5 text-[0.65rem]' },
  lg: { gap: 'gap-7', mosaic: 'size-28', name: 'text-4xl', country: 'mt-3 text-sm' },
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
      <img
        src="/brand/thpc-mosaico-web.svg"
        alt=""
        aria-hidden="true"
        className={cn('shrink-0', s.mosaic)}
      />
      <span className="flex flex-col leading-none">
        <span className={cn('font-mono font-semibold tracking-tight whitespace-nowrap text-foreground', s.name)}>
          Tabletop Hobby Prices
        </span>
        <span
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
