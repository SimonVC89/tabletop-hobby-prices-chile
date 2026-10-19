import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'

// Filtros que usaba la pagina de ofertas cuando vivia en "/".
const OFFER_PARAMS = ['tipo', 'tienda', 'orden']

/**
 * Las ofertas se mudaron de "/" a "/ofertas". Un enlace compartido con filtros
 * (/?tienda=Aldea+Juegos) se redirige a la nueva ruta en vez de perder los filtros.
 */
export function LegacyOffersRedirect({ children }: { children: ReactNode }) {
  const { search } = useLocation()
  const params = new URLSearchParams(search)
  if (OFFER_PARAMS.some((key) => params.has(key))) {
    return <Navigate to={`/ofertas${search}`} replace />
  }
  return children
}
