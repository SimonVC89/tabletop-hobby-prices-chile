import { Link } from 'react-router'

export function NotFoundPage() {
  return (
    <div className="py-16 text-center">
      <p className="font-mono text-sm text-highlight">404</p>
      <h1 className="mt-2 text-2xl font-bold">Esta página no está en el tablero</h1>
      <p className="mt-3 text-muted-foreground">Puede que el juego ya no esté a la venta o que el enlace esté mal escrito.</p>
      <Link to="/" className="mt-6 inline-block text-primary underline-offset-4 hover:underline">
        Volver a las ofertas
      </Link>
    </div>
  )
}
