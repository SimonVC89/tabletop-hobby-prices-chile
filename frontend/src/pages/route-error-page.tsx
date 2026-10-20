import { Link, useRouteError } from 'react-router'
import { Button } from '@/components/ui/button'

/**
 * Error al cargar o mostrar una pagina. El caso tipico: la pestana quedo abierta desde
 * antes de un deploy y pide un archivo de codigo que ya no existe (cada version cambia
 * sus nombres). Normalmente main.tsx recarga solo; esto es lo que se ve si aun asi falla.
 */
export function RouteErrorPage() {
  const error = useRouteError()
  const message = error instanceof Error ? error.message : ''
  const outdated = /dynamically imported module|Importing a module script failed|Failed to fetch/i.test(message)

  return (
    <div className="py-16 text-center">
      <p className="font-mono text-sm text-highlight">{outdated ? 'Versión nueva' : 'Error'}</p>
      <h1 className="mt-2 text-2xl font-bold">
        {outdated ? 'El sitio se actualizó mientras lo tenías abierto' : 'No pudimos mostrar esta página'}
      </h1>
      <p className="mx-auto mt-3 max-w-md text-muted-foreground">
        {outdated
          ? 'Recarga la página para usar la versión nueva. No se pierde nada.'
          : 'Prueba recargando. Si sigue pasando, vuelve al inicio y entra de nuevo.'}
      </p>
      <div className="mt-6 flex items-center justify-center gap-4">
        <Button onClick={() => window.location.reload()}>Recargar</Button>
        <Link to="/" className="text-primary underline-offset-4 hover:underline">
          Volver al inicio
        </Link>
      </div>
    </div>
  )
}
