import { Link, NavLink, Outlet, ScrollRestoration } from 'react-router'
import { usingMockData } from '@/api/client'
import { useMeta } from '@/api/hooks'
import { Logo } from '@/components/logo'
import { useScrolled } from '@/hooks/use-scrolled'
import { formatDateTime } from '@/lib/format'
import { cn } from '@/lib/utils'

const NAV = [
  { to: '/', label: 'Ofertas' },
  { to: '/juegos', label: 'Buscar juegos' },
]

const REPO_URL = 'https://github.com/SimonVC89/tabletop-hobby-prices-chile'

// Cambio de logo al compactar: el que sale queda superpuesto (absolute) para
// que solo el visible defina el tamano del link.
const LOGO_SWAP = 'origin-left transition-[opacity,scale] duration-300 motion-reduce:transition-none'
const LOGO_HIDDEN = 'pointer-events-none absolute top-1/2 left-0 -translate-y-1/2 opacity-0'

export function AppLayout() {
  const compact = useScrolled(24)

  return (
    <div className="flex min-h-svh flex-col">
      {/* Reserva el alto del header expandido: al compactarse el contenido no salta. */}
      <div className="h-26 shrink-0 md:h-30">
        <header
          className={cn(
            'fixed inset-x-0 top-0 z-30 border-b bg-background/90 backdrop-blur transition-[height] duration-300 motion-reduce:transition-none',
            compact ? 'h-16' : 'h-26 md:h-30',
          )}
        >
          <div className="mx-auto flex h-full max-w-6xl items-center justify-between gap-6 px-4 sm:px-6">
            <Link
              to="/"
              aria-label="Tabletop Hobby Prices Chile, inicio"
              className="relative flex items-center rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Logo size="sm" className={cn(LOGO_SWAP, compact && cn(LOGO_HIDDEN, 'scale-75'))} />
              <Logo size="compact" className={cn(LOGO_SWAP, !compact && cn(LOGO_HIDDEN, 'scale-125'))} />
            </Link>
            <nav aria-label="Principal" className="flex items-center gap-1">
              {NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end
                  className={({ isActive }) =>
                    cn(
                      'rounded-md px-3 py-2 text-sm font-medium transition-colors hover:text-foreground',
                      isActive ? 'text-foreground' : 'text-muted-foreground',
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </header>
      </div>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 sm:py-10">
        <Outlet />
      </main>

      <SiteFooter />
      {/* Pagina nueva parte arriba; al volver atras recupera donde estaba. */}
      <ScrollRestoration />
    </div>
  )
}

function SiteFooter() {
  const { data: meta } = useMeta()

  return (
    <footer className="border-t">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>
          {meta ? <>Precios actualizados el {formatDateTime(meta.lastUpdated)}</> : 'Precios actualizados a diario'}
          {usingMockData && ' · datos de un snapshot de desarrollo'}
        </p>
        <p>
          Proyecto personal ·{' '}
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="underline-offset-4 hover:text-foreground hover:underline">
            código en GitHub
          </a>
        </p>
      </div>
    </footer>
  )
}
