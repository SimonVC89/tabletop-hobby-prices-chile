import { type RefObject, useLayoutEffect, useState } from 'react'

/** true si el texto del elemento esta cortado (line-clamp / overflow). */
export function useIsTruncated(ref: RefObject<HTMLElement | null>) {
  const [truncated, setTruncated] = useState(false)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    // ResizeObserver avisa al observar y cada vez que cambia el ancho de la
    // tarjeta (rotar el celular, achicar la ventana).
    const observer = new ResizeObserver(() => setTruncated(el.scrollHeight > el.clientHeight + 1))
    observer.observe(el)
    return () => observer.disconnect()
  }, [ref])

  return truncated
}
