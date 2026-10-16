import { useState } from 'react'
import { cn } from '@/lib/utils'

/**
 * Imagen de producto servida desde la CDN de cada tienda. Sin referrer,
 * porque algunas tiendas bloquean imagenes enlazadas desde otro dominio;
 * si igual falla, cae al mosaico de la marca en vez de un icono roto.
 */
export function ProductImage({ src, alt, className }: { src: string | null; alt: string; className?: string }) {
  const [failed, setFailed] = useState(false)
  const showFallback = !src || failed

  return (
    <div className={cn('flex items-center justify-center overflow-hidden rounded-md bg-tile', className)}>
      {showFallback ? (
        <img src="/brand/thpc-mosaico-web.svg" alt="" aria-hidden="true" className="size-1/3 opacity-30 grayscale" />
      ) : (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setFailed(true)}
          className="size-full object-contain p-3 mix-blend-multiply"
        />
      )}
    </div>
  )
}
