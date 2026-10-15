import { Logo } from '@/components/logo'
import { Button } from '@/components/ui/button'

// Pagina provisoria: solo verifica que el tema (colores, fuentes, radios)
// se aplique bien antes de construir pantallas reales.
export default function App() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <Logo size="lg" />

      <h1 className="mt-10 text-3xl font-bold">Ofertas de hoy</h1>
      <p className="mt-2 max-w-prose text-muted-foreground">
        Precios comparados entre 11 tiendas chilenas. Una oferta es real
        cuando una tienda vende bajo la mediana del mercado.
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <article className="rounded-lg border bg-card p-5">
          <div className="flex items-start justify-between gap-4">
            <h2 className="text-lg font-semibold">Terraforming Mars</h2>
            <span className="rounded-md bg-deal/15 px-2 py-0.5 text-sm font-medium text-deal">
              −32%
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Aldea Juegos</p>
          <p className="mt-4 flex items-baseline gap-3">
            <span className="price text-2xl font-semibold">$44.190</span>
            <span className="price text-sm text-muted-foreground line-through">
              $64.990
            </span>
          </p>
        </article>

        <article className="rounded-lg border bg-card p-5">
          <div className="flex items-start justify-between gap-4">
            <h2 className="text-lg font-semibold">Catan Big Box</h2>
            <span className="rounded-md bg-price-up/15 px-2 py-0.5 text-sm font-medium text-price-up">
              +8%
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">UpDown</p>
          <p className="mt-4 flex items-baseline gap-3">
            <span className="price text-2xl font-semibold">$75.590</span>
            <span className="text-sm text-highlight">Destacado</span>
          </p>
        </article>
      </div>

      <div className="mt-8 flex flex-wrap gap-3">
        <Button>Ver todas las ofertas</Button>
        <Button variant="outline">Cómo funciona</Button>
        <Button variant="ghost">Tiendas</Button>
      </div>
    </main>
  )
}
