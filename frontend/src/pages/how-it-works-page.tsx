import { ArrowDown, ArrowRight, ArrowUpRight, CircleAlert } from 'lucide-react'
import { useEffect, type ReactNode } from 'react'
import { useMeta } from '@/api/hooks'
import { formatCLP } from '@/lib/format'
import { cn } from '@/lib/utils'

const LINKEDIN_URL = 'https://www.linkedin.com/in/simonvillarcabrera'
const GITHUB_URL = 'https://github.com/SimonVC89'
const REPO_URL = 'https://github.com/SimonVC89/tabletop-hobby-prices-chile'
const API_DOCS_URL = 'https://thpc-api.onrender.com/swagger-ui.html'

const PIPELINE = [
  {
    title: 'Recolectar',
    text: 'Scrapers en Python leen el catálogo de cada tienda dos veces al día, respetando su robots.txt y con pausas entre páginas.',
  },
  {
    title: 'Reconocer',
    text: 'Cada título se normaliza y se agrupa con el mismo juego en las otras tiendas, aunque lo escriban distinto.',
  },
  {
    title: 'Clasificar',
    text: 'Se separan los juegos de mesa de lo que no lo es: protectores, sobres de TCG, naipes, libros de rol.',
  },
  {
    title: 'Calcular',
    text: 'Con el precio de cada tienda se calcula la mediana, el historial y qué cuenta como oferta.',
  },
  {
    title: 'Publicar',
    text: 'Los resultados llegan a esta web y al bot de Telegram, que avisa las ofertas nuevas.',
  },
]

// Ejemplo inventado para explicar la regla: 5 tiendas, la mediana es la del medio.
const EXAMPLE = [
  { store: 'Tienda A', price: 24990 },
  { store: 'Tienda B', price: 30000 },
  { store: 'Tienda C', price: 31990 },
  { store: 'Tienda D', price: 32990 },
  { store: 'Tienda E', price: 34990 },
]
const EXAMPLE_MEDIAN = 31990

const STACK = [
  {
    area: 'Recolección',
    tech: 'Python · requests · BeautifulSoup · GitHub Actions',
    why: 'Un cron gratuito que corre en la mañana y en la tarde, cuando las tiendas ya cambiaron sus precios del día.',
  },
  {
    area: 'Base de datos',
    tech: 'PostgreSQL en Supabase · pgvector',
    why: 'El historial guarda solo los cambios de precio, no una fila por día: así entra cómodo en el plan gratuito.',
  },
  {
    area: 'Reconocer juegos',
    tech: 'sentence-transformers (modelo multilingüe, local)',
    why: 'Los embeddings se calculan en la misma máquina del cron: sin costo por consulta a una API externa.',
  },
  {
    area: 'Web',
    tech: 'React · TypeScript · Vite · TanStack Query · Tailwind · Recharts',
    why: 'Los filtros viven en la URL, así un link filtrado se puede compartir. El gráfico se carga solo en la ficha de cada juego.',
  },
  {
    area: 'API',
    tech: 'Spring Boot · Java 21 · Docker en Render · OpenAPI',
    why: 'La web y el bot leen de la misma API, con un usuario de base de datos que no puede modificar los precios. Documentada con Swagger: cada endpoint se puede probar desde el navegador.',
  },
  {
    area: 'Avisos',
    tech: 'Bot de Telegram (webhook)',
    why: 'Telegram le pasa cada mensaje a la API y el bot responde en segundos. Resumen de ofertas y seguimiento de hasta 20 juegos por persona, sin cuentas ni contraseñas.',
  },
  {
    area: 'Calidad',
    tech: 'pytest',
    why: 'Pruebas automáticas para las reglas que más fácil se rompen: normalizar títulos, detectar duplicados, armar los avisos.',
  },
]

export function HowItWorksPage() {
  const { data: meta } = useMeta()

  useEffect(() => {
    document.title = 'Cómo funciona · Tabletop Hobby Prices Chile'
    return () => {
      document.title = 'Tabletop Hobby Prices Chile'
    }
  }, [])

  return (
    <div>
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold sm:text-4xl">Cómo funciona</h1>
        <p className="mt-3 text-muted-foreground">
          Este sitio compara los precios de {meta ? meta.activeStores : 'varias'} tiendas chilenas de juegos de mesa para
          encontrar las ofertas de verdad. Esta página explica de dónde salen los datos, qué reglas se aplican y qué
          cosas todavía no hace bien.
        </p>
      </header>

      <Section id="flujo" title="Del catálogo de la tienda a esta página">
        <ol className="mt-5 grid gap-2 lg:grid-cols-5 lg:gap-3">
          {PIPELINE.map((step, i) => (
            <li key={step.title} className="flex flex-col lg:flex-row lg:items-stretch">
              <div className="flex-1 rounded-lg border bg-card p-4">
                <p className="price text-xs font-semibold text-highlight">{String(i + 1).padStart(2, '0')}</p>
                <h3 className="mt-1 font-semibold">{step.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{step.text}</p>
              </div>
              {i < PIPELINE.length - 1 && (
                <>
                  <ArrowDown className="mx-auto my-1 size-4 text-muted-foreground lg:hidden" aria-hidden="true" />
                  <ArrowRight
                    className="-mr-3 hidden size-4 shrink-0 self-center text-muted-foreground lg:block"
                    aria-hidden="true"
                  />
                </>
              )}
            </li>
          ))}
        </ol>
      </Section>

      <Section id="oferta" title="Cuándo algo es oferta">
        <div className="mt-5 grid gap-8 lg:grid-cols-2 lg:gap-12">
          <div className="space-y-3 text-muted-foreground">
            <p>
              Aquí no se usa el precio "antes" que muestra la tienda, porque cada una lo calcula a su manera. Se compara
              contra lo que cobra <strong className="font-medium text-foreground">el resto del mercado</strong>:
            </p>
            <ul className="list-disc space-y-2 pl-5 marker:text-foreground">
              <li>
                Se toma el precio más barato con stock de cada tienda: <Strong>una tienda, un precio</Strong>. Así una
                tienda que publica el mismo juego dos veces no pesa doble.
              </li>
              <li>
                Con esos precios se calcula la <Strong>mediana</Strong>, el precio del medio. A diferencia del promedio,
                una tienda con un precio absurdo no la mueve.
              </li>
              <li>
                Es <Strong>oferta</Strong> si una tienda lo vende al menos <Strong>20% bajo la mediana</Strong>, y{' '}
                <span className="font-medium text-highlight">destacada</span> si es 50% o más.
              </li>
              <li>
                Solo se compara con <Strong>3 o más tiendas</Strong> con stock: con dos, la mediana es solo el punto
                medio entre ellas y no dice mucho.
              </li>
            </ul>
          </div>

          <OfferExample />
        </div>
      </Section>

      <Section id="mismo-juego" title="El mismo juego en tiendas distintas">
        <div className="mt-4 max-w-3xl space-y-3 text-muted-foreground">
          <p>
            Cada tienda escribe el título a su manera: "Catan", "Catan Básico", "CATAN - Juego de mesa (Español)". Para
            compararlos hay que saber que son el mismo juego.
          </p>
          <ol className="list-decimal space-y-2 pl-5 marker:text-foreground">
            <li>
              <Strong>Normalizar.</Strong> Se quitan tildes, mayúsculas y palabras de relleno ("juego de mesa",
              "español"), se unifican sinónimos y ordinales ("2da edición" y "segunda edición") y queda una clave. Los
              títulos con la misma clave son el mismo juego.
            </li>
            <li>
              <Strong>Comparar significados.</Strong> Para lo que la clave no alcanza, un modelo de lenguaje convierte
              cada título en un vector (embedding) y se buscan pares casi idénticos.
            </li>
            <li>
              <Strong>Reglas de excepción.</Strong> Hay títulos que se parecen mucho y son juegos distintos: una edición
              "revisada", una expansión de campaña y otra de investigadores, una secuela y una segunda edición. Esos
              casos nunca se juntan.
            </li>
            <li>
              <Strong>Fusiones revisadas y reversibles.</Strong> Los duplicados se revisan antes de fusionarlos, y la
              fusión deja un alias: si mañana una tienda nueva escribe el título como antes, cae en el juego correcto.
            </li>
          </ol>
        </div>
      </Section>

      <Section id="stack" title="Tecnologías y decisiones">
        <dl className="mt-5 divide-y rounded-lg border bg-card">
          {STACK.map((row) => (
            <div key={row.area} className="grid gap-1 px-4 py-4 md:grid-cols-[10rem_minmax(0,18rem)_1fr] md:gap-6">
              <dt className="font-semibold">{row.area}</dt>
              <dd className="font-mono text-sm">{row.tech}</dd>
              <dd className="text-sm text-muted-foreground">{row.why}</dd>
            </div>
          ))}
        </dl>
      </Section>

      <Section id="limitaciones" title="Lo que todavía no hace bien">
        <ul className="mt-4 max-w-3xl space-y-3">
          <Limitation>
            Los precios se revisan dos veces al día, a las 5:17 y a las 19:17, y cada revisión tarda cerca de una hora. Entre
            una y otra un precio puede cambiar en la tienda: <Strong>el precio que vale es el de la tienda</Strong>.
          </Limitation>
          <Limitation>
            Una tienda bloquea los servidores en la nube y se actualiza a mano, así que sus precios pueden tener unos días.
            Otras bloquean el acceso automatizado: se respetó y se dejaron de revisar.
          </Limitation>
          <Limitation>
            El reconocimiento de juegos no es perfecto. Si una tienda agrega texto publicitario al título, el mismo juego
            puede aparecer dos veces.
          </Limitation>
          <Limitation>
            No todos los juegos tienen descripción: se toma de la página de una tienda, y no todas la publican.
          </Limitation>
          <Limitation>
            La API corre en un plan gratuito: si se reinicia, la primera respuesta puede tardar cerca de un minuto.
          </Limitation>
        </ul>
      </Section>

      <Section id="autor" title="Sobre el autor">
        <div className="mt-4 max-w-3xl rounded-lg border bg-card p-5">
          <p className="text-muted-foreground">
            Soy <Strong>Simón Villar</Strong>. Hice este proyecto para comparar precios con mis amigos jugones y para
            construir un sistema completo de punta a punta: recolección de datos, base de datos, reglas de negocio, web y
            bot.
          </p>
          <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
            <ExternalLink href={LINKEDIN_URL}>LinkedIn</ExternalLink>
            <ExternalLink href={GITHUB_URL}>GitHub</ExternalLink>
            <ExternalLink href={REPO_URL}>Código de este proyecto</ExternalLink>
            <ExternalLink href={API_DOCS_URL}>Documentación de la API</ExternalLink>
          </div>
        </div>
      </Section>
    </div>
  )
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section aria-labelledby={id} className="mt-14">
      <h2 id={id} className="scroll-mt-24 text-xl font-bold sm:text-2xl">
        {title}
      </h2>
      {children}
    </section>
  )
}

/** Barras de precio por tienda con la mediana marcada: la regla de oferta, en un ejemplo. */
function OfferExample() {
  const max = Math.max(...EXAMPLE.map((e) => e.price))
  const medianPct = (EXAMPLE_MEDIAN / max) * 100

  return (
    <figure className="self-start rounded-lg border bg-card p-5">
      <div className="relative space-y-2.5">
        {/* Linea de la mediana, sobre la columna de barras (deja libre la de nombres). */}
        <div className="pointer-events-none absolute inset-y-0 right-24 left-20" aria-hidden="true">
          <div className="absolute inset-y-0 border-l border-dashed border-foreground/50" style={{ left: `${medianPct}%` }} />
        </div>
        {EXAMPLE.map((e) => {
          const pct = Math.round((100 * (EXAMPLE_MEDIAN - e.price)) / EXAMPLE_MEDIAN)
          const offer = pct >= 20
          return (
            <div key={e.store} className="flex items-center gap-0 text-sm">
              <span className="w-20 shrink-0 text-muted-foreground">{e.store}</span>
              <div className="h-5 flex-1">
                <div
                  className={cn('h-full rounded-r', offer ? 'bg-deal' : 'bg-chart-neutral/60')}
                  style={{ width: `${(e.price / max) * 100}%` }}
                />
              </div>
              <span className={cn('price w-24 shrink-0 text-right', offer && 'font-semibold text-deal')}>
                {formatCLP(e.price)}
              </span>
            </div>
          )
        })}
      </div>
      <figcaption className="mt-4 text-sm text-muted-foreground">
        Ejemplo con datos inventados. La mediana es <span className="price text-foreground">{formatCLP(EXAMPLE_MEDIAN)}</span>{' '}
        (línea punteada). La Tienda A vende a{' '}
        <span className="price font-semibold text-deal">
          {Math.round((100 * (EXAMPLE_MEDIAN - EXAMPLE[0].price)) / EXAMPLE_MEDIAN)}% menos
        </span>
        : es oferta.
      </figcaption>
    </figure>
  )
}

function Limitation({ children }: { children: ReactNode }) {
  return (
    <li className="flex gap-3 text-muted-foreground">
      <CircleAlert className="mt-0.5 size-5 shrink-0 text-highlight" aria-hidden="true" />
      <span>{children}</span>
    </li>
  )
}

function Strong({ children }: { children: ReactNode }) {
  return <strong className="font-medium text-foreground">{children}</strong>
}

function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
    >
      {children}
      <ArrowUpRight className="size-4" aria-hidden="true" />
      <span className="sr-only"> (se abre en otra pestaña)</span>
    </a>
  )
}
