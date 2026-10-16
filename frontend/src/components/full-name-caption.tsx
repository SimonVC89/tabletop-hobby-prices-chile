import { cn } from '@/lib/utils'

/**
 * Nombre completo de un juego cuyo titulo se corta en la tarjeta. Va dentro
 * del contenedor de la imagen y sube sobre su borde inferior al pasar el
 * puntero o enfocar el titulo (la tarjeta debe tener la clase `group`).
 * Es solo visual: el titulo ya contiene el nombre completo para lectores
 * de pantalla.
 */
export function FullNameCaption({ name, className }: { name: string; className?: string }) {
  return (
    <p
      aria-hidden="true"
      className={cn(
        'pointer-events-none absolute inset-x-0 bottom-0 translate-y-1 border-t bg-popover/95 px-3 py-2 font-heading text-sm leading-snug font-semibold text-popover-foreground opacity-0 backdrop-blur-sm transition duration-150',
        'group-has-[h2:hover]:translate-y-0 group-has-[h2:hover]:opacity-100',
        'group-has-[h2_a:focus-visible]:translate-y-0 group-has-[h2_a:focus-visible]:opacity-100',
        'motion-reduce:transition-none',
        className,
      )}
    >
      {name}
    </p>
  )
}
