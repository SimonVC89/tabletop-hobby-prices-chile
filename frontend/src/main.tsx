import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { AppLayout } from '@/components/layout/app-layout'
import { NotFoundPage } from '@/pages/not-found-page'
import { OffersPage } from '@/pages/offers-page'
import './index.css'

const queryClient = new QueryClient()

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <OffersPage /> },
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
