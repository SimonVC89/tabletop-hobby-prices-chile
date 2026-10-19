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
import { SearchPage } from '@/pages/search-page'
import { TelegramPage } from '@/pages/telegram-page'
import './index.css'

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
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
