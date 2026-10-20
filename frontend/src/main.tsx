import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { NotFoundError } from '@/api/client'
import { AppLayout } from '@/components/layout/app-layout'
import { LegacyOffersRedirect } from '@/components/layout/legacy-offers-redirect'
import { HomePage } from '@/pages/home-page'
import { HowItWorksPage } from '@/pages/how-it-works-page'
import { NotFoundPage } from '@/pages/not-found-page'
import { OffersPage } from '@/pages/offers-page'
import { RouteErrorPage } from '@/pages/route-error-page'
import { SearchPage } from '@/pages/search-page'
import { TelegramPage } from '@/pages/telegram-page'
import './index.css'

// Tras un deploy, una pestana abierta desde antes pide archivos de la version anterior,
// que ya no existen (cada version cambia sus nombres). Vite avisa con este evento: se
// recarga una vez para tomar la version nueva. Como maximo una recarga por minuto, para
// no quedar en un ciclo si el problema es otro (sin red, por ejemplo).
window.addEventListener('vite:preloadError', (event) => {
  const key = 'thpc:recarga-por-deploy'
  try {
    const last = Number(sessionStorage.getItem(key) ?? 0)
    if (Date.now() - last < 60_000) return
    sessionStorage.setItem(key, String(Date.now()))
  } catch {
    return // sin sessionStorage no hay forma segura de evitar el ciclo: se muestra el error
  }
  event.preventDefault()
  window.location.reload()
})

// Un 404 no cambia al reintentar: se muestra la pagina de "no existe" de inmediato.
// Los demas errores (red, servidor dormido) si se reintentan, hasta 3 veces.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: (failures, error) => !(error instanceof NotFoundError) && failures < 3 },
  },
})

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      {
        // Ruta sin path que solo agrupa: un error se muestra dentro del layout (con
        // encabezado y menu) en vez de reemplazar todo el sitio.
        errorElement: <RouteErrorPage />,
        children: [
          // Las ofertas vivian en "/": los links viejos con filtros siguen funcionando.
          {
            index: true,
            element: (
              <LegacyOffersRedirect>
                <HomePage />
              </LegacyOffersRedirect>
            ),
          },
          { path: 'ofertas', element: <OffersPage /> },
          { path: 'juegos', element: <SearchPage /> },
          { path: 'telegram', element: <TelegramPage /> },
          { path: 'como-funciona', element: <HowItWorksPage /> },
          // Carga diferida: el detalle trae Recharts (~110 KB gzip) y la portada no lo necesita.
          {
            path: 'juego/:id',
            lazy: async () => ({ Component: (await import('@/pages/product-page')).ProductPage }),
          },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
