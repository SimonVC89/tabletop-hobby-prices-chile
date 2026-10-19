import { useSimilarProducts } from '@/api/hooks'
import { ProductCard } from '@/components/product-card'

/**
 * Juegos de la misma saga o con nombre casi identico que hoy se pueden
 * comprar. Es una seccion secundaria: si falla o no hay relacionados, no se
 * muestra nada (un error aqui no debe ensuciar la ficha del juego).
 */
export function RelatedGames({ productId }: { productId: string }) {
  const { data: related } = useSimilarProducts(productId)

  if (!related || related.length === 0) return null

  return (
    <section aria-labelledby="relacionados-titulo" className="mt-12">
      <h2 id="relacionados-titulo" className="text-xl font-bold">
        Juegos relacionados
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        De la misma saga o con un nombre muy parecido, y disponibles hoy en alguna tienda.
      </p>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-6">
        {related.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </section>
  )
}
