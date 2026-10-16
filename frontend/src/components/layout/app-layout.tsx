import { Link, NavLink, Outlet } from 'react-router'
import { usingMockData } from '@/api/client'
import { useMeta } from '@/api/hooks'
import { Logo } from '@/components/logo'
import { formatDateTime } from '@/lib/format'
import { cn } from '@/lib/utils'

const NAV = [{ to: '/', label: 'Ofertas' }]

const REPO_URL = 'https://github.com/SimonVC89/tabletop-hobby-prices-chile'

export function AppLayout() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="sticky top-0 z-30 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4 sm:px-6">
          <Link to="/" aria-label="Inicio" className="rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Logo size="sm" />
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

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 sm:py-10">
        <Outlet />
      </main>

      <SiteFooter />
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
